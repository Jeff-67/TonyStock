"""Database package initialization."""

from typing import Type

from database.utils import DatabaseManager as _DatabaseManager
from database.utils import db_manager as _db_manager

DatabaseManager: Type[_DatabaseManager] = _DatabaseManager
db_manager: _DatabaseManager = _db_manager

__all__ = ["DatabaseManager", "db_manager"]
