"""
ib_pyrelease_utils - Utilities for helping release projects effectively.

This package provides utilities for managing Python project releases,
including reading properties files and checking for release conditions.
"""

__version__ = "0.0.5"

# Import main functions for easier access
from .basic import (
    bump_sync_commit,
    check_for_release,
    create_release_properties_file,
    create_tag_for_version,
    ensure_empty_directory,
    ensure_no_changed_files,
    ensure_release_tag_does_not_exist,
    get_current_version,
    get_next_version,
    read_properties_file,
    release_perform,
    release_prepare,
    run_command_or_fail,
)

__all__ = [
    "bump_sync_commit",
    "check_for_release",
    "create_release_properties_file",
    "create_tag_for_version",
    "ensure_empty_directory",
    "ensure_no_changed_files",
    "ensure_release_tag_does_not_exist",
    "get_current_version",
    "get_next_version",
    "read_properties_file",
    "release_perform",
    "release_prepare",
    "run_command_or_fail",
]
