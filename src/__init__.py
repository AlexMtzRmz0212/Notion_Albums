# src/__init__.py
"""
Notion Music Manager

A comprehensive tool for managing music libraries in Notion.
"""

__version__ = "1.0.0"
__author__ = "Alex Martinez"
__email__ = "alejandro.martinez.rmz97@gmail.com"

# Make key modules/classes available at package level
from .core.base import Album, BaseNotionManager
from .managers.sorter import AlbumSorter
from .managers.decorator import AlbumDecorator

__all__ = [
    'Album',
    'BaseNotionManager',
    'AlbumSorter',
    'AlbumDecorator',
]