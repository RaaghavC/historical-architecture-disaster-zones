# This file makes 'connectors' a Python package
from .base import BaseConnector
from .archnet import ArchnetConnector
from .manar import ManarConnector
from .salt import SALTConnector
from .nit import NITConnector
from .wikimedia import WikimediaConnector

__all__ = ['BaseConnector', 'ArchnetConnector', 'ManarConnector', 'SALTConnector', 'NITConnector', 'WikimediaConnector']