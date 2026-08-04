"""
ib_pyrelease_utils - Utilities for helping release projects effectively.

This package provides utilities for managing Python project releases,
including reading properties files and checking for release conditions.
"""

__version__ = "0.0.1"

# Import main functions for easier access
from .basic import (
    BUILD_TOOL_ENV_VAR,
    DEFAULT_BUILD_TOOL,
    check_for_release,
    ensure_empty_directory,
    main,
    perform_main,
    prepare_main,
    read_properties_file,
    release_perform,
    release_prepare,
    resolve_build_tool,
)

__all__ = [
    "read_properties_file",
    "check_for_release",
    "ensure_empty_directory",
    "release_prepare",
    "release_perform",
    "main",
    "prepare_main",
    "perform_main",
    "resolve_build_tool",
    "DEFAULT_BUILD_TOOL",
    "BUILD_TOOL_ENV_VAR",
]
