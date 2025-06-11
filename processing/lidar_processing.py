"""Placeholder for LiDAR processing routines"""
from pathlib import Path
from utils.logging_config import get_logger

log = get_logger(__name__)


def align_lidar(lidar_path: Path, mesh_path: Path):
    log.info("Aligning %s with %s", lidar_path, mesh_path)
    # Placeholder implementation
