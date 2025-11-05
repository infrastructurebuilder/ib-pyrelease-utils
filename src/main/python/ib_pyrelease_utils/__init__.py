"""
ib_pyrelease_utils - Utilities for helping release projects effectively.

This package provides utilities for managing Python project releases,
including reading properties files and checking for release conditions.
"""

__version__ = "0.0.1"

# Import main functions for easier access
from .basic import (
    check_for_release,
    ensure_empty_directory,
    read_properties_file,
    release_prepare,
)

__all__ = [
    "read_properties_file",
    "check_for_release",
    "ensure_empty_directory",
    "release_prepare",
]
