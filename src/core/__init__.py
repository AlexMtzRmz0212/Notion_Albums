# src/core/__init__.py
"""
Core components for Notion Music Manager.

Contains base classes and shared utilities.
"""

from .base import Album, BaseNotionManager
from .utils import (
    fetch_all_notion_pages,
    clear_console,
    get_user_choice,
    log_message
)

__all__ = [
    'Album',
    'BaseNotionManager',
    'fetch_all_notion_pages',
    'clear_console',
    'get_user_choice',
    'log_message'
]