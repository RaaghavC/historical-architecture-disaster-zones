from pathlib import Path
from typing import Iterable


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def list_files(directory: Path, exts: Iterable[str]):
    for ext in exts:
        yield from directory.glob(f"*.{ext}")
