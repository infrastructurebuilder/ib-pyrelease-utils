"""
ib_pyrelease_utils - Utilities for helping release projects effectively.

This package provides utilities for managing Python project releases,
including reading properties files and checking for release conditions.
"""

__version__ = "0.0.6"

# Import main functions for easier access
from .basic import (
    BUILD_TOOL_ENV_VAR,
    DEFAULT_BUILD_TOOL,
    bump_sync_commit,
    check_for_release,
    create_release_properties_file,
    create_tag_for_version,
    ensure_empty_directory,
    ensure_no_changed_files,
    ensure_release_tag_does_not_exist,
    get_current_version,
    get_next_version,
    main,
    perform_main,
    prepare_main,
    read_properties_file,
    release_perform,
    release_prepare,
    resolve_build_tool,
    run_command_or_fail,
)

__all__ = [
    # Properties and preconditions
    "read_properties_file",
    "check_for_release",
    "ensure_empty_directory",
    "ensure_no_changed_files",
    "ensure_release_tag_does_not_exist",
    # Versioning
    "get_current_version",
    "get_next_version",
    "bump_sync_commit",
    # Tagging and release metadata
    "create_tag_for_version",
    "create_release_properties_file",
    # Release phases
    "release_prepare",
    "release_perform",
    # Console script entry points
    "main",
    "prepare_main",
    "perform_main",
    # Build tool configuration
    "resolve_build_tool",
    "DEFAULT_BUILD_TOOL",
    "BUILD_TOOL_ENV_VAR",
    # Command execution
    "run_command_or_fail",
]
