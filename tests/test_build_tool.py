"""Tests for the configurable build tool used inside the release checkout.

Two fixture projects under ``tests/resources`` implement the same contract --
a ``clean`` target and a ``build`` target -- with different tools:

* ``test_build_justfile/`` is driven by ``just``
* ``test-makefile/`` is driven by ``make``

Each fixture's ``build`` writes ``build.marker`` naming the tool that ran, so a
test can prove which tool release_perform actually invoked.

Fixtures are copied to a system temp directory rather than used in place:
``just`` searches *upward* for a justfile, so running it inside the repo would
find the project's own Justfile instead of the fixture's.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import (
    BUILD_TOOL_ENV_VAR,
    DEFAULT_BUILD_TOOL,
    perform_main,
    release_perform,
    resolve_build_tool,
)

RESOURCES = Path(__file__).resolve().parent / "resources"
JUSTFILE_FIXTURE = RESOURCES / "test_build_justfile"
MAKEFILE_FIXTURE = RESOURCES / "test-makefile"

HAVE_JUST = shutil.which("just") is not None
HAVE_MAKE = shutil.which("make") is not None


class TestResolveBuildTool(unittest.TestCase):
    """Test build tool resolution precedence."""

    def test_defaults_to_just(self):
        """With nothing supplied the default tool is used."""
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(resolve_build_tool(), DEFAULT_BUILD_TOOL)
            self.assertEqual(resolve_build_tool(None), "just")

    def test_explicit_value_wins(self):
        """An explicit argument is used verbatim."""
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(resolve_build_tool("make"), "make")

    def test_environment_variable_is_honoured(self):
        """$IB_BUILD_TOOL is used when no explicit value is given."""
        with patch.dict("os.environ", {BUILD_TOOL_ENV_VAR: "make"}, clear=True):
            self.assertEqual(resolve_build_tool(), "make")

    def test_explicit_value_overrides_environment(self):
        """An explicit argument beats $IB_BUILD_TOOL."""
        with patch.dict("os.environ", {BUILD_TOOL_ENV_VAR: "make"}, clear=True):
            self.assertEqual(resolve_build_tool("task"), "task")

    def test_blank_values_fall_through(self):
        """Empty strings fall through to the next source rather than running ''."""
        with patch.dict("os.environ", {BUILD_TOOL_ENV_VAR: ""}, clear=True):
            self.assertEqual(resolve_build_tool(""), DEFAULT_BUILD_TOOL)


class TestReleasePerformBuildTool(unittest.TestCase):
    """Test which command release_perform invokes for clean/build."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)
        self.checkout_path = self.temp_dir_path / "checkout"
        self.checkout_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _build_command(self, build_tool=None, env=None):
        """Run release_perform and return the (command, args) used to build."""
        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ) as mock_run_cmd, patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ), patch.dict(
            "os.environ", env or {}, clear=True
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_run_cmd.return_value = ""

            release_perform(self.checkout_path, token="tok", build_tool=build_tool)

        build_calls = [
            c for c in mock_run_cmd.call_args_list if c[0][1] == ["clean", "build"]
        ]
        self.assertEqual(len(build_calls), 1)
        return build_calls[0]

    def test_defaults_to_just(self):
        """Without configuration release_perform runs 'just clean build'."""
        call = self._build_command()
        self.assertEqual(call[0][0], "just")

    def test_explicit_build_tool_is_used(self):
        """An explicit build_tool replaces the default."""
        call = self._build_command(build_tool="make")
        self.assertEqual(call[0][0], "make")

    def test_environment_variable_is_used(self):
        """$IB_BUILD_TOOL is honoured when no explicit value is passed."""
        call = self._build_command(env={BUILD_TOOL_ENV_VAR: "make"})
        self.assertEqual(call[0][0], "make")

    def test_explicit_build_tool_overrides_environment(self):
        """An explicit build_tool beats $IB_BUILD_TOOL."""
        call = self._build_command(build_tool="just", env={BUILD_TOOL_ENV_VAR: "make"})
        self.assertEqual(call[0][0], "just")

    def test_build_runs_in_the_checkout_directory(self):
        """The build tool is anchored to the checkout, not the ambient cwd."""
        call = self._build_command()
        self.assertEqual(call[1]["cwd"], self.checkout_path.absolute())


class TestPerformMainBuildToolOption(unittest.TestCase):
    """Test the --build-tool option on the ib-perform entry point."""

    def _forwarded_build_tool(self, argv, env=None):
        with patch("sys.argv", argv), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform, patch.dict("os.environ", env or {}, clear=True):
            perform_main()
            return mock_perform.call_args[1]["build_tool"]

    def test_no_option_forwards_none(self):
        """Without the flag, resolution is left to release_perform."""
        self.assertIsNone(self._forwarded_build_tool(["ib-perform"]))

    def test_build_tool_option_is_forwarded(self):
        """--build-tool is passed straight through."""
        self.assertEqual(
            self._forwarded_build_tool(["ib-perform", "--build-tool", "make"]),
            "make",
        )

    def test_build_tool_option_with_checkout_path(self):
        """--build-tool composes with the positional checkout path."""
        with patch(
            "sys.argv", ["ib-perform", "some/where", "--build-tool", "make"]
        ), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform, patch.dict(
            "os.environ", {}, clear=True
        ):
            perform_main()
            kwargs = mock_perform.call_args[1]
            self.assertEqual(kwargs["checkout_path"], Path("some/where"))
            self.assertEqual(kwargs["build_tool"], "make")

    def test_unknown_option_exits_one(self):
        """An unrecognised flag exits 1 rather than argparse's default 2."""
        with patch("sys.argv", ["ib-perform", "--nope"]), patch("sys.stderr"), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform:
            with self.assertRaises(SystemExit) as cm:
                perform_main()
            self.assertEqual(cm.exception.code, 1)
            mock_perform.assert_not_called()


class TestBuildToolFixtures(unittest.TestCase):
    """Run the real build tools against the two fixture projects.

    Everything in release_perform is mocked except run_command_or_fail, so the
    clean/build step genuinely executes. Neither fixture has an .envrc, so the
    build command is the only one that actually runs.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)
        # Source repo the release is driven from; deliberately has no .envrc.
        self.source_dir = self.temp_dir_path / "source"
        self.source_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _checkout_from(self, fixture):
        """Copy a fixture project into a temp checkout directory."""
        checkout = self.temp_dir_path / "checkout"
        shutil.copytree(fixture, checkout)
        return checkout

    def _perform(self, checkout, build_tool):
        """Run release_perform with the build step left unmocked."""
        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ), patch(
            "pathlib.Path.cwd", return_value=self.source_dir
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            release_perform(checkout, token="tok", build_tool=build_tool)

    @unittest.skipUnless(HAVE_JUST, "just is not installed")
    def test_justfile_fixture_is_built_by_just(self):
        """The Justfile fixture builds when the build tool is 'just'."""
        checkout = self._checkout_from(JUSTFILE_FIXTURE)
        self._perform(checkout, "just")
        marker = checkout / "build.marker"
        self.assertTrue(marker.exists())
        self.assertEqual(marker.read_text(encoding="utf-8").strip(), "just")

    @unittest.skipUnless(HAVE_MAKE, "make is not installed")
    def test_makefile_fixture_is_built_by_make(self):
        """The Makefile fixture builds when the build tool is 'make'."""
        checkout = self._checkout_from(MAKEFILE_FIXTURE)
        self._perform(checkout, "make")
        marker = checkout / "build.marker"
        self.assertTrue(marker.exists())
        self.assertEqual(marker.read_text(encoding="utf-8").strip(), "make")

    @unittest.skipUnless(HAVE_MAKE, "make is not installed")
    def test_justfile_fixture_is_not_built_by_make(self):
        """The Justfile fixture has no Makefile, so 'make' fails."""
        checkout = self._checkout_from(JUSTFILE_FIXTURE)
        with self.assertRaises(SystemExit) as cm:
            self._perform(checkout, "make")
        self.assertEqual(cm.exception.code, 1)
        self.assertFalse((checkout / "build.marker").exists())

    @unittest.skipUnless(HAVE_JUST, "just is not installed")
    def test_makefile_fixture_is_not_built_by_just(self):
        """The Makefile fixture has no Justfile, so 'just' fails."""
        checkout = self._checkout_from(MAKEFILE_FIXTURE)
        with self.assertRaises(SystemExit) as cm:
            self._perform(checkout, "just")
        self.assertEqual(cm.exception.code, 1)
        self.assertFalse((checkout / "build.marker").exists())

    @unittest.skipUnless(HAVE_MAKE, "make is not installed")
    def test_default_tool_does_not_build_the_makefile_fixture(self):
        """The default ('just') cannot build the Makefile fixture.

        This is what makes the two fixtures a real differentiator: the same
        checkout succeeds or fails purely on the build_tool value.
        """
        checkout = self._checkout_from(MAKEFILE_FIXTURE)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(SystemExit):
                self._perform(checkout, None)
        self.assertFalse((checkout / "build.marker").exists())

        self._perform(checkout, "make")
        self.assertEqual(
            (checkout / "build.marker").read_text(encoding="utf-8").strip(), "make"
        )


if __name__ == "__main__":
    unittest.main()
