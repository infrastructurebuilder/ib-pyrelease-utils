"""Guards on the package's public API surface.

The `master` branch exported a broader set of names from the package root than
the refactored branch did. That divergence went unnoticed because nothing
asserted the surface, so `from ib_pyrelease_utils import get_current_version`
would have started failing silently.

These tests pin the surface so it can grow but not shrink by accident.
"""

import unittest

import ib_pyrelease_utils
from ib_pyrelease_utils import basic

# Names exported from the package root on the `master` branch (commit 5e47a90).
# Removing any of these is a breaking change for importers and must be a
# deliberate decision, not a refactoring side effect.
MASTER_ROOT_EXPORTS = frozenset(
    {
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
    }
)

# Public callables defined in basic.py on `master`. These must remain importable
# from ib_pyrelease_utils.basic even if they are not re-exported at the root.
MASTER_BASIC_CALLABLES = frozenset(
    MASTER_ROOT_EXPORTS
    | {
        "bmv",
        "git",
        "main",
        "uv",
    }
)

# Console script entry points declared in pyproject.toml [project.scripts].
ENTRY_POINTS = frozenset({"main", "prepare_main", "perform_main"})


class TestPackageExports(unittest.TestCase):
    """The package root exposes everything it claims to."""

    def test_all_names_are_importable(self):
        """Every name in __all__ resolves on the package."""
        for name in ib_pyrelease_utils.__all__:
            with self.subTest(name=name):
                self.assertTrue(
                    hasattr(ib_pyrelease_utils, name),
                    f"__all__ lists {name!r} but the package does not define it",
                )

    def test_all_has_no_duplicates(self):
        """__all__ is a set, not an accidental multiset."""
        names = list(ib_pyrelease_utils.__all__)
        self.assertEqual(sorted(names), sorted(set(names)))

    def test_master_exports_are_retained(self):
        """The historical root surface from master is still exported."""
        missing = MASTER_ROOT_EXPORTS - set(ib_pyrelease_utils.__all__)
        self.assertEqual(
            missing,
            set(),
            f"public names dropped relative to master: {sorted(missing)}",
        )

    def test_entry_points_are_exported(self):
        """Console script targets are reachable from the package root."""
        missing = ENTRY_POINTS - set(ib_pyrelease_utils.__all__)
        self.assertEqual(missing, set())

    def test_build_tool_configuration_is_exported(self):
        """The build tool knobs are part of the documented surface."""
        for name in ("resolve_build_tool", "DEFAULT_BUILD_TOOL", "BUILD_TOOL_ENV_VAR"):
            with self.subTest(name=name):
                self.assertIn(name, ib_pyrelease_utils.__all__)


class TestBasicModuleSurface(unittest.TestCase):
    """basic.py still provides everything master's basic.py did."""

    def test_master_callables_still_exist(self):
        """No public callable from master's basic.py was removed."""
        missing = {n for n in MASTER_BASIC_CALLABLES if not hasattr(basic, n)}
        self.assertEqual(
            missing,
            set(),
            f"callables dropped from basic.py relative to master: {sorted(missing)}",
        )

    def test_master_callables_are_callable(self):
        """Those names are functions, not leftover constants."""
        for name in sorted(MASTER_BASIC_CALLABLES):
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(basic, name)))

    def test_entry_points_are_callable(self):
        """Each console script target is a zero-argument callable."""
        for name in sorted(ENTRY_POINTS):
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(basic, name)))


class TestVersion(unittest.TestCase):
    """The package version stays in lockstep with the packaging metadata."""

    def test_version_is_exposed(self):
        """__version__ is present and non-empty."""
        self.assertTrue(ib_pyrelease_utils.__version__)

    def test_version_matches_distribution_metadata(self):
        """__version__ agrees with the installed distribution.

        bump-my-version updates pyproject.toml and __init__.py together; this
        catches the two drifting apart.
        """
        from importlib.metadata import PackageNotFoundError, version

        try:
            installed = version("ib-pyrelease-utils")
        except PackageNotFoundError:  # pragma: no cover - only when not installed
            self.skipTest("ib-pyrelease-utils is not installed in this environment")
        self.assertEqual(ib_pyrelease_utils.__version__, installed)


if __name__ == "__main__":
    unittest.main()
