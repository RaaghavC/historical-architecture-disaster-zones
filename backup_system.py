"""
Automated Backup System for Antakya Heritage Data
Provides scheduled backups to cloud storage and local redundancy
"""

import os
import json
import shutil
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import schedule
import time
import boto3
from google.cloud import storage as gcs
import dropbox
import requests


class BackupConfig:
    """Configuration for backup destinations"""
    
    def __init__(self, config_file: str = ".backup_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load backup configuration from file or environment"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Try to load from environment variables
        config = {
            "local": {
                "enabled": True,
                "paths": [
                    os.getenv("BACKUP_LOCAL_PATH1", "/Volumes/Backup/antakya_heritage"),
                    os.getenv("BACKUP_LOCAL_PATH2", "~/Documents/antakya_backup")
                ]
            },
            "s3": {
                "enabled": bool(os.getenv("AWS_ACCESS_KEY_ID")),
                "bucket": os.getenv("S3_BACKUP_BUCKET", "antakya-heritage-backup"),
                "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                "prefix": "backups/"
            },
            "gcs": {
                "enabled": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
                "bucket": os.getenv("GCS_BACKUP_BUCKET", "antakya-heritage-backup"),
                "prefix": "backups/"
            },
            "dropbox": {
                "enabled": bool(os.getenv("DROPBOX_ACCESS_TOKEN")),
                "token": os.getenv("DROPBOX_ACCESS_TOKEN"),
                "folder": "/antakya_heritage_backup"
            },
            "webhook": {
                "enabled": bool(os.getenv("BACKUP_WEBHOOK_URL")),
                "url": os.getenv("BACKUP_WEBHOOK_URL")
            }
        }
        
        return config
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)


class BackupManager:
    """Manages automated backups of heritage data"""
    
    def __init__(self, project_root: str = ".", config: Optional[BackupConfig] = None):
        self.project_root = Path(project_root)
        self.config = config or BackupConfig()
        
        # Directories to backup
        self.backup_dirs = [
            "harvested_data",
            "downloaded_images", 
            "field_data",
            "comparisons",
            "database"
        ]
        
        # File patterns to include
        self.include_patterns = [
            "*.json", "*.xlsx", "*.csv", "*.db", "*.jpg", "*.png",
            "*.tif", "*.tiff", "*.pdf", "*.html", "*.md"
        ]
        
        # Backup metadata
        self.backup_log = self.project_root / ".backup_log.json"
        self.load_backup_log()
    
    def load_backup_log(self):
        """Load backup history"""
        if self.backup_log.exists():
            with open(self.backup_log, 'r') as f:
                self.log = json.load(f)
        else:
            self.log = {"backups": [], "last_backup": None}
    
    def save_backup_log(self):
        """Save backup history"""
        with open(self.backup_log, 'w') as f:
            json.dump(self.log, f, indent=2)
    
    def calculate_changes(self) -> Dict[str, List[Path]]:
        """Calculate which files have changed since last backup"""
        changes = {"new": [], "modified": [], "deleted": []}
        
        # Get last backup time
        last_backup = None
        if self.log["last_backup"]:
            last_backup = datetime.fromisoformat(self.log["last_backup"])
        
        # Track current files
        current_files = {}
        
        for backup_dir in self.backup_dirs:
            dir_path = self.project_root / backup_dir
            if not dir_path.exists():
                continue
            
            for pattern in self.include_patterns:
                for file_path in dir_path.rglob(pattern):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(self.project_root)
                        file_hash = self._get_file_hash(file_path)
                        current_files[str(rel_path)] = {
                            "hash": file_hash,
                            "modified": file_path.stat().st_mtime,
                            "size": file_path.stat().st_size
                        }
                        
                        # Check if new or modified
                        if last_backup:
                            if file_path.stat().st_mtime > last_backup.timestamp():
                                if str(rel_path) in self.log.get("file_hashes", {}):
                                    if self.log["file_hashes"][str(rel_path)] != file_hash:
                                        changes["modified"].append(file_path)
                                else:
                                    changes["new"].append(file_path)
                        else:
                            changes["new"].append(file_path)
        
        # Check for deleted files
        if "file_hashes" in self.log:
            for old_file in self.log["file_hashes"]:
                if old_file not in current_files:
                    changes["deleted"].append(old_file)
        
        # Update file hashes
        self.log["file_hashes"] = {k: v["hash"] for k, v in current_files.items()}
        
        return changes
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Calculate file hash"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def create_backup_archive(self, changes: Dict[str, List[Path]]) -> Optional[Path]:
        """Create incremental backup archive"""
        if not any(changes.values()):
            print("No changes detected, skipping backup")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"antakya_backup_{timestamp}"
        
        # Create temporary backup directory
        temp_dir = self.project_root / ".temp_backup" / backup_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy changed files
        for file_path in changes["new"] + changes["modified"]:
            rel_path = file_path.relative_to(self.project_root)
            dest_path = temp_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)
        
        # Create metadata file
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "incremental" if self.log["last_backup"] else "full",
            "changes": {
                "new": len(changes["new"]),
                "modified": len(changes["modified"]),
                "deleted": len(changes["deleted"])
            },
            "deleted_files": changes["deleted"]
        }
        
        with open(temp_dir / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create zip archive
        archive_path = self.project_root / f"{backup_name}.zip"
        shutil.make_archive(str(archive_path.with_suffix('')), 'zip', temp_dir)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir.parent)
        
        return archive_path
    
    def backup_to_local(self, archive_path: Path) -> List[str]:
        """Backup to local destinations"""
        successful = []
        
        for local_path in self.config.config["local"]["paths"]:
            try:
                dest_path = Path(local_path).expanduser()
                dest_path.mkdir(parents=True, exist_ok=True)
                
                dest_file = dest_path / archive_path.name
                shutil.copy2(archive_path, dest_file)
                
                successful.append(str(dest_file))
                print(f"✓ Backed up to local: {dest_file}")
            except Exception as e:
                print(f"✗ Failed to backup to {local_path}: {e}")
        
        return successful
    
    def backup_to_s3(self, archive_path: Path) -> Optional[str]:
        """Backup to Amazon S3"""
        if not self.config.config["s3"]["enabled"]:
            return None
        
        try:
            s3 = boto3.client('s3')
            bucket = self.config.config["s3"]["bucket"]
            key = f"{self.config.config['s3']['prefix']}{archive_path.name}"
            
            s3.upload_file(str(archive_path), bucket, key)
            
            s3_url = f"s3://{bucket}/{key}"
            print(f"✓ Backed up to S3: {s3_url}")
            return s3_url
        except Exception as e:
            print(f"✗ Failed to backup to S3: {e}")
            return None
    
    def backup_to_gcs(self, archive_path: Path) -> Optional[str]:
        """Backup to Google Cloud Storage"""
        if not self.config.config["gcs"]["enabled"]:
            return None
        
        try:
            client = gcs.Client()
            bucket = client.bucket(self.config.config["gcs"]["bucket"])
            blob_name = f"{self.config.config['gcs']['prefix']}{archive_path.name}"
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(str(archive_path))
            
            gcs_url = f"gs://{bucket.name}/{blob_name}"
            print(f"✓ Backed up to GCS: {gcs_url}")
            return gcs_url
        except Exception as e:
            print(f"✗ Failed to backup to GCS: {e}")
            return None
    
    def backup_to_dropbox(self, archive_path: Path) -> Optional[str]:
        """Backup to Dropbox"""
        if not self.config.config["dropbox"]["enabled"]:
            return None
        
        try:
            dbx = dropbox.Dropbox(self.config.config["dropbox"]["token"])
            
            dest_path = f"{self.config.config['dropbox']['folder']}/{archive_path.name}"
            
            with open(archive_path, 'rb') as f:
                dbx.files_upload(f.read(), dest_path)
            
            print(f"✓ Backed up to Dropbox: {dest_path}")
            return dest_path
        except Exception as e:
            print(f"✗ Failed to backup to Dropbox: {e}")
            return None
    
    def send_webhook_notification(self, backup_info: Dict):
        """Send backup notification via webhook"""
        if not self.config.config["webhook"]["enabled"]:
            return
        
        try:
            webhook_url = self.config.config["webhook"]["url"]
            
            payload = {
                "event": "backup_completed",
                "timestamp": backup_info["timestamp"],
                "size": backup_info["size"],
                "files_backed_up": backup_info["files_count"],
                "destinations": backup_info["destinations"]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.ok:
                print(f"✓ Webhook notification sent")
            else:
                print(f"✗ Webhook notification failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Failed to send webhook: {e}")
    
    def perform_backup(self) -> Dict:
        """Perform a complete backup"""
        print(f"\n{'='*60}")
        print(f"Starting backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Calculate changes
        changes = self.calculate_changes()
        
        total_changes = len(changes["new"]) + len(changes["modified"])
        print(f"\nChanges detected:")
        print(f"  New files: {len(changes['new'])}")
        print(f"  Modified files: {len(changes['modified'])}")
        print(f"  Deleted files: {len(changes['deleted'])}")
        
        if total_changes == 0 and len(changes['deleted']) == 0:
            print("\nNo changes to backup.")
            return {"status": "no_changes"}
        
        # Create backup archive
        archive_path = self.create_backup_archive(changes)
        if not archive_path:
            return {"status": "failed", "error": "Could not create archive"}
        
        archive_size = archive_path.stat().st_size
        print(f"\nCreated backup archive: {archive_path.name}")
        print(f"Size: {archive_size / 1024 / 1024:.2f} MB")
        
        # Backup to destinations
        destinations = []
        
        if self.config.config["local"]["enabled"]:
            local_dests = self.backup_to_local(archive_path)
            destinations.extend([{"type": "local", "path": p} for p in local_dests])
        
        if self.config.config["s3"]["enabled"]:
            s3_url = self.backup_to_s3(archive_path)
            if s3_url:
                destinations.append({"type": "s3", "path": s3_url})
        
        if self.config.config["gcs"]["enabled"]:
            gcs_url = self.backup_to_gcs(archive_path)
            if gcs_url:
                destinations.append({"type": "gcs", "path": gcs_url})
        
        if self.config.config["dropbox"]["enabled"]:
            dropbox_path = self.backup_to_dropbox(archive_path)
            if dropbox_path:
                destinations.append({"type": "dropbox", "path": dropbox_path})
        
        # Update backup log
        backup_info = {
            "timestamp": datetime.now().isoformat(),
            "archive": archive_path.name,
            "size": archive_size,
            "files_count": total_changes,
            "destinations": destinations,
            "changes": {
                "new": len(changes["new"]),
                "modified": len(changes["modified"]),
                "deleted": len(changes["deleted"])
            }
        }
        
        self.log["backups"].append(backup_info)
        self.log["last_backup"] = datetime.now().isoformat()
        self.save_backup_log()
        
        # Send webhook notification
        self.send_webhook_notification(backup_info)
        
        # Clean up local archive if backed up elsewhere
        if destinations and not any(d["type"] == "local" for d in destinations):
            archive_path.unlink()
            print(f"\nCleaned up temporary archive")
        
        print(f"\n✓ Backup completed successfully!")
        print(f"  Backed up to {len(destinations)} destination(s)")
        
        return backup_info
    
    def restore_from_backup(self, backup_name: str, source: str = "local") -> bool:
        """Restore from a backup"""
        print(f"\nRestoring from backup: {backup_name}")
        
        # Find backup in log
        backup_info = None
        for backup in self.log["backups"]:
            if backup["archive"] == backup_name:
                backup_info = backup
                break
        
        if not backup_info:
            print(f"✗ Backup not found in log: {backup_name}")
            return False
        
        # TODO: Implement restore logic based on source
        # This would download from cloud storage and extract
        
        return True
    
    def schedule_backups(self, interval: str = "daily"):
        """Schedule automatic backups"""
        if interval == "hourly":
            schedule.every().hour.do(self.perform_backup)
        elif interval == "daily":
            schedule.every().day.at("02:00").do(self.perform_backup)
        elif interval == "weekly":
            schedule.every().week.do(self.perform_backup)
        
        print(f"Scheduled {interval} backups")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nBackup scheduler stopped")
    
    def get_backup_status(self) -> Dict:
        """Get current backup status"""
        status = {
            "last_backup": self.log.get("last_backup"),
            "total_backups": len(self.log.get("backups", [])),
            "destinations_configured": [],
            "recent_backups": []
        }
        
        # Check configured destinations
        for dest_type in ["local", "s3", "gcs", "dropbox"]:
            if self.config.config[dest_type]["enabled"]:
                status["destinations_configured"].append(dest_type)
        
        # Get recent backups
        if self.log.get("backups"):
            status["recent_backups"] = self.log["backups"][-5:][::-1]
        
        return status


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Antakya Heritage Backup System")
    parser.add_argument("command", choices=["backup", "status", "schedule", "restore", "config"],
                       help="Command to execute")
    parser.add_argument("--interval", choices=["hourly", "daily", "weekly"],
                       default="daily", help="Backup interval for scheduling")
    parser.add_argument("--backup-name", help="Name of backup to restore")
    parser.add_argument("--source", default="local", help="Source for restore")
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.command == "backup":
        manager.perform_backup()
    elif args.command == "status":
        status = manager.get_backup_status()
        print(json.dumps(status, indent=2))
    elif args.command == "schedule":
        manager.schedule_backups(args.interval)
    elif args.command == "restore":
        if args.backup_name:
            manager.restore_from_backup(args.backup_name, args.source)
        else:
            print("Please specify --backup-name")
    elif args.command == "config":
        print(json.dumps(manager.config.config, indent=2))