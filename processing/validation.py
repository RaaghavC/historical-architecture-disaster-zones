"""Placeholder for mesh/texture validation routines"""
from utils.logging_config import get_logger

log = get_logger(__name__)


def validate_mesh(mesh_path):
    log.info("Validating %s", mesh_path)
