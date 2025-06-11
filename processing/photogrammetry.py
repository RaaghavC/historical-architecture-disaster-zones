"""
Thin wrapper around COLMAP → OpenMVS workflow to produce textured
meshes + point clouds from harvested photographs.

Usage example:
    python -m processing.photogrammetry reconstruct archnet:12345
"""
import subprocess
import tempfile
from pathlib import Path
from typing import List
import requests
import typer
from database.models import Item, Session
from config import settings
from utils.logging_config import get_logger

log = get_logger(__name__)
app = typer.Typer(add_completion=False)


def fetch_images(site_items: List[Item], workdir: Path) -> List[Path]:
    imgs = []
    workdir.mkdir(parents=True, exist_ok=True)
    for itm in site_items:
        target = workdir / f"{itm.identifier}.{itm.format.split('/')[-1]}"
        if not target.exists():
            target.write_bytes(requests.get(itm.source_url, timeout=60).content)
        imgs.append(target)
    return imgs


@app.command()
def reconstruct(site_id: str):
    with Session() as sess:
        items = sess.query(Item).filter_by(identifier=site_id).all()
    if not items:
        raise typer.Exit(f"No records for {site_id}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        images = fetch_images(items, tmp / "images")

        colmap_cmd = [
            str(settings.COLMAP_BIN),
            "automatic_reconstructor",
            "--workspace_path",
            str(tmp),
            "--image_path",
            str(tmp / "images"),
            "--mkdir_if_not_exists",
            "1",
        ]
        subprocess.run(colmap_cmd, check=True)

        mvs_cmd = [
            str(settings.OPENMVS_BIN),
            str(tmp / "dense" / "fused.ply"),
            str(tmp / "mesh.ply"),
        ]
        subprocess.run(mvs_cmd, check=True)

        out = settings.DATA_DIR / "meshes" / f"{site_id}.ply"
        out.parent.mkdir(parents=True, exist_ok=True)
        (tmp / "mesh.ply").replace(out)
        log.info("→ 3D mesh written to %s", out)


if __name__ == "__main__":
    app()
