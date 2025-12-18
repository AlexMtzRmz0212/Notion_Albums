# src/managers/__init__.py
"""
Manager classes for Notion Music Manager operations.

Each manager handles a specific aspect of music library management.
"""

from .sorter import AlbumSorter
from .decorator import AlbumDecorator

__all__ = [
    'AlbumSorter',
    'AlbumDecorator'
]