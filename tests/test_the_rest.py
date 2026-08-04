"""Tests for remaining coverage gaps in basic.py."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import (
    bmv,
    get_current_version,
    get_next_version,
    git,
    main,
    perform_main,
    prepare_main,
    uv,
)


class TestHelperFunctions(unittest.TestCase):
    """Test helper wrapper functions."""

    def test_uv_calls_run_command_or_fail(self):
        """Test that uv() calls run_command_or_fail with correct arguments."""
        with patch("ib_pyrelease_utils.basic.run_command_or_fail") as mock_run:
            mock_run.return_value = "output"
            result = uv(["publish", "--token", "token123"])
            mock_run.assert_called_once_with(
                "uv", ["publish", "--token", "token123"], Path("."), secrets=None
            )
            self.assertEqual(result, "output")

    def test_uv_forwards_secrets(self):
        """Test that uv() forwards secrets so they are redacted on failure."""
        with patch("ib_pyrelease_utils.basic.run_command_or_fail") as mock_run:
            mock_run.return_value = "output"
            uv(["publish", "--token", "token123"], secrets=["token123"])
            mock_run.assert_called_once_with(
                "uv",
                ["publish", "--token", "token123"],
                Path("."),
                secrets=["token123"],
            )

    def test_uv_with_custom_cwd(self):
        """Test that uv() passes custom cwd to run_command_or_fail."""
        custom_dir = Path("/custom/dir")
        with patch("ib_pyrelease_utils.basic.run_command_or_fail") as mock_run:
            mock_run.return_value = "output"
            result = uv(["sync"], cwd=custom_dir)
            mock_run.assert_called_once_with("uv", ["sync"], custom_dir, secrets=None)
            self.assertEqual(result, "output")

    def test_git_calls_run_command_or_fail(self):
        """Test that git() calls run_command_or_fail with correct arguments."""
        with patch("ib_pyrelease_utils.basic.run_command_or_fail") as mock_run:
            mock_run.return_value = "commit_hash"
            result = git(["commit", "-m", "test"])
            mock_run.assert_called_once_with(
                "git", ["commit", "-m", "test"], Path("."), None, []
            )
            self.assertEqual(result, "commit_hash")

    def test_git_with_error_message(self):
        """Test that git() passes errmsg to run_command_or_fail."""
        errmsg = "Failed to commit"
        with patch("ib_pyrelease_utils.basic.run_command_or_fail") as mock_run:
            mock_run.return_value = ""
            git(["tag", "v1.0.0"], errmsg=errmsg)
            mock_run.assert_called_once_with(
                "git", ["tag", "v1.0.0"], Path("."), errmsg, []
            )

    def test_git_with_custom_cwd(self):
        """Test that git() passes custom cwd to run_command_or_fail."""
        custom_dir = Path("/project")
        with patch("ib_pyrelease_utils.basic.run_command_or_fail") as mock_run:
            mock_run.return_value = "origin"
            git(["remote", "-v"], cwd=custom_dir)
            mock_run.assert_called_once_with(
                "git", ["remote", "-v"], custom_dir, None, []
            )

    def test_bmv_calls_uv_correctly(self):
        """Test that bmv() constructs correct arguments for uv()."""
        with patch("ib_pyrelease_utils.basic.uv") as mock_uv:
            mock_uv.return_value = "0.2.0"
            result = bmv(["show", "current_version"])
            mock_uv.assert_called_once_with(
                ["run", "bump-my-version", "show", "current_version"], Path(".")
            )
            self.assertEqual(result, "0.2.0")

    def test_bmv_with_custom_cwd(self):
        """Test that bmv() passes custom cwd to uv()."""
        custom_dir = Path("/project")
        with patch("ib_pyrelease_utils.basic.uv") as mock_uv:
            mock_uv.return_value = ""
            bmv(["bump", "--new-version", "1.1.0"], cwd=custom_dir)
            mock_uv.assert_called_once_with(
                ["run", "bump-my-version", "bump", "--new-version", "1.1.0"], custom_dir
            )

    def test_get_next_version(self):
        """Test that get_next_version() calls bmv with correct arguments."""
        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv:
            mock_bmv.return_value = "1.0.1"
            result = get_next_version()
            mock_bmv.assert_called_once_with(
                ["--increment", "patch", "show"], Path(".")
            )
            self.assertEqual(result, "1.0.1")

    def test_get_next_version_with_custom_cwd(self):
        """Test that get_next_version() passes custom cwd to bmv()."""
        custom_dir = Path("/project")
        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv:
            mock_bmv.return_value = "2.0.0"
            result = get_next_version(cwd=custom_dir)
            mock_bmv.assert_called_once_with(
                ["--increment", "patch", "show"], custom_dir
            )
            self.assertEqual(result, "2.0.0")

    def test_get_current_version(self):
        """Test that get_current_version() calls bmv with correct arguments."""
        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv:
            mock_bmv.return_value = "1.0.0"
            result = get_current_version()
            mock_bmv.assert_called_once_with(["show", "current_version"], Path("."))
            self.assertEqual(result, "1.0.0")

    def test_get_current_version_with_custom_cwd(self):
        """Test that get_current_version() passes custom cwd to bmv()."""
        custom_dir = Path("/project")
        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv:
            mock_bmv.return_value = "0.5.0"
            result = get_current_version(cwd=custom_dir)
            mock_bmv.assert_called_once_with(["show", "current_version"], custom_dir)
            self.assertEqual(result, "0.5.0")


class TestReadPropertiesFileBranches(unittest.TestCase):
    """Test branches in read_properties_file."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_read_properties_file_with_only_empty_lines(self):
        """Test read_properties_file with file containing only empty lines."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("\n\n\n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {})

    def test_read_properties_file_with_only_comment_lines(self):
        """Test read_properties_file with file containing only comments."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("# This is a comment\n! This is also a comment\n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {})

    def test_read_properties_file_with_mixed_empty_and_comments(self):
        """Test read_properties_file with mixed empty lines and comments."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text(
            "\n# Comment\nkey=value\n\n! Another comment\nkey2=value2\n"
        )

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {"key": "value", "key2": "value2"})

    def test_read_properties_file_with_whitespace_around_equals(self):
        """Test read_properties_file strips whitespace around keys and values."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("  key1  =  value1  \n  key2 = value2 \n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_read_properties_file_with_no_equals_sign(self):
        """Test read_properties_file skips lines without equals sign."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("key1=value1\ninvalid_line\nkey2=value2\n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_read_properties_file_with_value_containing_equals(self):
        """Test read_properties_file handles values containing equals signs."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("equation=x=y+z\nformula=a=b*c\n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {"equation": "x=y+z", "formula": "a=b*c"})

    def test_read_properties_file_with_empty_value(self):
        """Test read_properties_file handles empty values."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("key1=\nkey2=value2\n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(result, {"key1": "", "key2": "value2"})

    def test_read_properties_file_with_special_characters_in_value(self):
        """Test read_properties_file handles special characters in values."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("path=/usr/bin/python\nurl=https://example.com:8080\n")

        from ib_pyrelease_utils.basic import read_properties_file

        result = read_properties_file(props_file)
        self.assertEqual(
            result,
            {
                "path": "/usr/bin/python",
                "url": "https://example.com:8080",
            },
        )


class TestMainFunction(unittest.TestCase):
    """Test the main() function."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_main_with_missing_arguments(self):
        """Test main() exits with error when no arguments provided."""
        with patch("sys.argv", ["script"]):
            with patch("sys.stderr"):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_main_with_too_many_arguments(self):
        """Test main() exits with error when too many arguments provided."""
        with patch("sys.argv", ["script", "arg1", "arg2"]):
            with patch("sys.stderr"):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_main_with_valid_directory_no_release_properties(self):
        """Test main() succeeds when directory exists and no release.properties."""
        with patch("sys.argv", ["script", str(self.temp_dir_path)]):
            with patch("ib_pyrelease_utils.basic.check_for_release") as mock_check:
                main()
                mock_check.assert_called_once_with(str(self.temp_dir_path))

    def test_main_calls_check_for_release(self):
        """Test that main() calls check_for_release with directory argument."""
        test_dir = "/test/directory"
        with patch("sys.argv", ["script", test_dir]):
            with patch("ib_pyrelease_utils.basic.check_for_release") as mock_check:
                main()
                mock_check.assert_called_once_with(test_dir)

    def test_main_unknown_option_exits_one(self):
        """An unrecognised flag exits 1 rather than argparse's default 2."""
        with patch("sys.argv", ["ib-check-release", "--nope"]), patch(
            "sys.stderr"
        ), patch("ib_pyrelease_utils.basic.check_for_release") as mock_check:
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)
            mock_check.assert_not_called()

    def test_main_help_exits_zero(self):
        """--help is handled by the parser and exits successfully."""
        with patch("sys.argv", ["ib-check-release", "--help"]), patch(
            "sys.stdout"
        ), patch("ib_pyrelease_utils.basic.check_for_release") as mock_check:
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
            mock_check.assert_not_called()


class TestReleasePerformEdgeCases(unittest.TestCase):
    """Test edge cases in release_perform not covered by test_release_perform.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_release_perform_with_secrets_parameter(self):
        """Test that secrets are passed correctly to uv when publishing."""
        from ib_pyrelease_utils.basic import release_perform

        checkout_path = self.temp_dir_path / "checkout"
        token = "my_secret_token_xyz"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ), patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v1.0.0"}
            mock_uv.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Verify uv was called with secrets parameter
            mock_uv.assert_called_once()
            call_kwargs = mock_uv.call_args
            self.assertIn("secrets", call_kwargs[1])
            self.assertEqual(call_kwargs[1]["secrets"], [token])

    def test_release_perform_publishes_with_both_index_and_token(self):
        """Test that publish command includes both --index and --token."""
        from ib_pyrelease_utils.basic import release_perform

        checkout_path = self.temp_dir_path / "checkout"
        publish_index = "testpypi"
        token = "test_token_123"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ), patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v1.0.0"}
            mock_uv.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, publish_index, token)

            # Get the first call to uv (publish call)
            mock_uv.assert_called_once()
            args = mock_uv.call_args[0][0]
            self.assertIn("publish", args)
            self.assertIn("--token", args)
            self.assertIn(token, args)
            self.assertIn("--index", args)
            self.assertIn(publish_index, args)

    def test_release_perform_publishes_without_index(self):
        """Test that publish command works without --index parameter."""
        from ib_pyrelease_utils.basic import release_perform

        checkout_path = self.temp_dir_path / "checkout"
        token = "test_token_123"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ), patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v1.0.0"}
            mock_uv.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Get the first call to uv (publish call)
            mock_uv.assert_called_once()
            args = mock_uv.call_args[0][0]
            self.assertIn("publish", args)
            self.assertIn("--token", args)
            # Should NOT have --index when publish_index is None
            self.assertNotIn("--index", args)


class TestPrepareMain(unittest.TestCase):
    """Test the ib-prepare console script entry point."""

    def test_prepare_main_without_version(self):
        """prepare_main() passes None when no version argument is given."""
        with patch("sys.argv", ["ib-prepare"]), patch(
            "ib_pyrelease_utils.basic.release_prepare"
        ) as mock_prepare:
            prepare_main()
            mock_prepare.assert_called_once_with(None)

    def test_prepare_main_with_version(self):
        """prepare_main() forwards an explicit version argument."""
        with patch("sys.argv", ["ib-prepare", "1.2.3"]), patch(
            "ib_pyrelease_utils.basic.release_prepare"
        ) as mock_prepare:
            prepare_main()
            mock_prepare.assert_called_once_with("1.2.3")

    def test_prepare_main_with_too_many_arguments(self):
        """prepare_main() exits with error when given extra arguments."""
        with patch("sys.argv", ["ib-prepare", "1.2.3", "extra"]), patch(
            "sys.stderr"
        ), patch("ib_pyrelease_utils.basic.release_prepare") as mock_prepare:
            with self.assertRaises(SystemExit) as cm:
                prepare_main()
            self.assertEqual(cm.exception.code, 1)
            mock_prepare.assert_not_called()

    def test_prepare_main_unknown_option_exits_one(self):
        """An unrecognised flag exits 1 rather than argparse's default 2."""
        with patch("sys.argv", ["ib-prepare", "--nope"]), patch("sys.stderr"), patch(
            "ib_pyrelease_utils.basic.release_prepare"
        ) as mock_prepare:
            with self.assertRaises(SystemExit) as cm:
                prepare_main()
            self.assertEqual(cm.exception.code, 1)
            mock_prepare.assert_not_called()

    def test_prepare_main_help_exits_zero(self):
        """--help is handled by the parser and exits successfully."""
        with patch("sys.argv", ["ib-prepare", "--help"]), patch("sys.stdout"), patch(
            "ib_pyrelease_utils.basic.release_prepare"
        ) as mock_prepare:
            with self.assertRaises(SystemExit) as cm:
                prepare_main()
            self.assertEqual(cm.exception.code, 0)
            mock_prepare.assert_not_called()


class TestPerformMain(unittest.TestCase):
    """Test the ib-perform console script entry point."""

    def test_perform_main_defaults(self):
        """perform_main() uses the default checkout path and env credentials."""
        with patch("sys.argv", ["ib-perform"]), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform, patch.dict(
            "os.environ",
            {"UV_PUBLISH_TOKEN": "tok", "UV_PUBLISH_INDEX": "testpypi"},
            clear=True,
        ):
            perform_main()
            mock_perform.assert_called_once_with(
                checkout_path=Path("target/checkout"),
                publish_index="testpypi",
                token="tok",
                build_tool=None,
            )

    def test_perform_main_with_explicit_checkout_path(self):
        """perform_main() forwards an explicit checkout path."""
        with patch("sys.argv", ["ib-perform", "some/where"]), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform, patch.dict("os.environ", {}, clear=True):
            perform_main()
            mock_perform.assert_called_once_with(
                checkout_path=Path("some/where"),
                publish_index=None,
                token=None,
                build_tool=None,
            )

    def test_perform_main_missing_env_becomes_none(self):
        """perform_main() maps empty env vars to None rather than empty strings."""
        with patch("sys.argv", ["ib-perform"]), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform, patch.dict(
            "os.environ",
            {"UV_PUBLISH_TOKEN": "", "UV_PUBLISH_INDEX": ""},
            clear=True,
        ):
            perform_main()
            _, kwargs = mock_perform.call_args
            self.assertIsNone(kwargs["token"])
            self.assertIsNone(kwargs["publish_index"])

    def test_perform_main_with_too_many_arguments(self):
        """perform_main() exits with error when given extra arguments."""
        with patch("sys.argv", ["ib-perform", "a", "b"]), patch("sys.stderr"), patch(
            "ib_pyrelease_utils.basic.release_perform"
        ) as mock_perform:
            with self.assertRaises(SystemExit) as cm:
                perform_main()
            self.assertEqual(cm.exception.code, 1)
            mock_perform.assert_not_called()


if __name__ == "__main__":
    unittest.main()
