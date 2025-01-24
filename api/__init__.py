"""API package for TonyStock project.

This package contains the FastAPI server implementation that exposes
TonyStock's functionality through a REST API.
"""

from .server import app, start

__all__ = ["app", "start"]
