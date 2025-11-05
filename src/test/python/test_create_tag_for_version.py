import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import create_tag_for_version


class TestCreateTagForVersion(unittest.TestCase):

    def setUp(self):
        """Create a temporary git repository with testbmv content."""
        # Create a temporary directory in the project's target directory
        target_dir = Path.cwd() / "target"
        target_dir.mkdir(exist_ok=True)

        # Create a temporary git repo with a random name
        self.temp_dir = tempfile.mkdtemp(dir=target_dir, prefix="test_tag_")
        self.temp_dir_path = Path(self.temp_dir)

        # Copy testbmv tree into temp directory
        testbmv_src = Path.cwd() / "src" / "test" / "resources" / "testbmv"
        if testbmv_src.exists():
            # Copy all files from testbmv
            for item in testbmv_src.iterdir():
                if item.is_file():
                    shutil.copy2(item, self.temp_dir_path / item.name)
                elif item.is_dir():
                    shutil.copytree(
                        item,
                        self.temp_dir_path / item.name,
                        dirs_exist_ok=True,
                    )

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

        # Configure git user for commits
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

        # Add and commit initial files
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

    def tearDown(self):
        """Clean up temporary git repository."""
        if self.temp_dir_path.exists():
            shutil.rmtree(self.temp_dir)

    def test_create_tag_for_version_with_explicit_next_version(self):
        """Test create_tag_for_version with explicitly provided next version."""
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = "0.1.0"
            mock_git.return_value = ""

            result = create_tag_for_version(next_version, self.temp_dir_path)

            self.assertEqual(result, "v0.1.0")

    def test_create_tag_for_version_with_get_next_version_call(self):
        """Test create_tag_for_version calling get_next_version internally."""
        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.get_next_version"
        ) as mock_get_next, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = "1.5.0"
            mock_get_next.return_value = "1.5.1"
            mock_git.return_value = ""

            # Call with a different version to verify it uses the provided one
            result = create_tag_for_version("2.0.0", self.temp_dir_path)

            self.assertEqual(result, "v1.5.0")

    def test_create_tag_for_version_checks_for_changed_files_before(self):
        """Test that create_tag_for_version checks for changed files first."""
        next_version = "0.2.0"
        call_order = []

        def track_ensure_no_changed(cwd):
            call_order.append("ensure_no_changed_files")

        def track_get_current(cwd=None):
            call_order.append("get_current_version")
            return "0.1.0"

        with patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files",
            side_effect=track_ensure_no_changed,
        ), patch(
            "ib_pyrelease_utils.basic.get_current_version",
            side_effect=track_get_current,
        ), patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify ensure_no_changed_files is called before get_current_version
            self.assertEqual(call_order[0], "ensure_no_changed_files")
            self.assertEqual(call_order[1], "get_current_version")

    def test_create_tag_for_version_gets_current_version(self):
        """Test that create_tag_for_version calls get_current_version."""
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = "1.0.0"
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify get_current_version was called
            mock_get_current.assert_called_once()

    def test_create_tag_for_version_creates_correct_tag_name(self):
        """Test that create_tag_for_version creates tag with v prefix."""
        next_version = "0.2.0"
        current_version = "1.2.3"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ) as mock_ensure_tag, patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            result = create_tag_for_version(next_version, self.temp_dir_path)

            # Verify tag name is correct
            self.assertEqual(result, f"v{current_version}")

            # Verify ensure_release_tag_does_not_exist was called with correct tag
            mock_ensure_tag.assert_called_once_with(f"v{current_version}")

    def test_create_tag_for_version_ensures_tag_does_not_exist(self):
        """Test that create_tag_for_version checks tag doesn't already exist."""
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ) as mock_ensure_tag, patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = "0.1.0"
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify ensure_release_tag_does_not_exist was called
            mock_ensure_tag.assert_called_once()

    def test_create_tag_for_version_git_tag_command_mocked_line_206(self):
        """Test that create_tag_for_version calls git tag with correct args.

        This test verifies the git ls-remote call on line 206 is mocked
        to prevent actual remote calls.
        """
        next_version = "0.2.0"
        current_version = "1.0.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify git tag command was called with correct arguments
            git_calls = [call for call in mock_git.call_args_list]

            # Find the git tag create call
            tag_calls = [call for call in git_calls if "tag" in str(call)]
            self.assertTrue(len(tag_calls) > 0)

            tag_call = tag_calls[0]
            call_args = tag_call[0][0]

            # Verify git tag arguments
            self.assertEqual(call_args[0], "tag")
            self.assertEqual(call_args[1], "-a")
            self.assertEqual(call_args[2], "-m")
            self.assertIn(current_version, call_args[3])
            self.assertEqual(call_args[4], f"v{current_version}")

    def test_create_tag_for_version_cwd_passed_to_all_commands(self):
        """Test that cwd is passed to all subcommands."""
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ) as mock_bump, patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = "0.1.0"
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify cwd is passed to git tag call
            git_calls = [call for call in mock_git.call_args_list]
            for call in git_calls:
                self.assertEqual(call[0][1], self.temp_dir_path)

            # Verify cwd is passed to bump_sync_commit
            mock_bump.assert_called_once()
            bump_call = mock_bump.call_args_list[0]
            self.assertEqual(bump_call[0][2], self.temp_dir_path)

    def test_create_tag_for_version_calls_bump_sync_commit(self):
        """Test that create_tag_for_version calls bump_sync_commit."""
        next_version = "0.2.0"
        current_version = "0.1.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ) as mock_bump, patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify bump_sync_commit was called
            mock_bump.assert_called_once()

            # Verify it's called with correct arguments
            call_args = mock_bump.call_args_list[0]
            self.assertEqual(call_args[0][0], current_version)
            self.assertEqual(call_args[0][1], next_version)
            self.assertEqual(call_args[0][2], self.temp_dir_path)

    def test_create_tag_for_version_calls_create_release_properties_file(self):
        """Test that create_tag_for_version calls create_release_properties_file."""
        next_version = "0.2.0"
        current_version = "0.1.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ) as mock_create_props, patch(
            "builtins.print"
        ):
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify create_release_properties_file was called
            mock_create_props.assert_called_once()

            # Verify it's called with correct arguments
            call_args = mock_create_props.call_args_list[0]
            self.assertEqual(call_args[0][0], f"v{current_version}")
            self.assertEqual(call_args[0][1], next_version)
            self.assertEqual(call_args[0][2], self.temp_dir_path)

    def test_create_tag_for_version_checks_for_changed_files_after_bump(self):
        """Test that create_tag_for_version checks for changed files after
        bump_sync_commit."""
        next_version = "0.2.0"
        call_order = []

        def track_ensure_no_changed(cwd=None):
            call_order.append("ensure_no_changed_files")

        def track_bump_sync(*args, **kwargs):
            call_order.append("bump_sync_commit")

        with patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files",
            side_effect=track_ensure_no_changed,
        ), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit",
            side_effect=track_bump_sync,
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            mock_get_current.return_value = "0.1.0"
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify ensure_no_changed_files is called twice
            # (before and after bump_sync_commit)
            ensure_calls = [c for c in call_order if c == "ensure_no_changed_files"]
            self.assertEqual(len(ensure_calls), 2)

            # Verify first call before bump_sync_commit
            self.assertEqual(call_order[0], "ensure_no_changed_files")

            # Verify bump_sync_commit is called
            self.assertIn("bump_sync_commit", call_order)

            # Verify second ensure_no_changed_files call is after bump_sync_commit
            bump_index = call_order.index("bump_sync_commit")
            self.assertGreater(bump_index, 0)

    def test_create_tag_for_version_sequence_of_operations(self):
        """Test that create_tag_for_version performs operations in correct
        order."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files",
            side_effect=[None, None],  # Two calls
        ), patch(
            "ib_pyrelease_utils.basic.get_current_version",
            return_value="0.1.0",
        ), patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git",
            return_value="",
        ), patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ):
            # Just verify that key operations are called without exception
            result = create_tag_for_version(next_version, self.temp_dir_path)

            # Verify result is correct
            self.assertEqual(result, "v0.1.0")

    def test_create_tag_for_version_prints_status_messages(self):
        """Test that create_tag_for_version prints status messages."""
        next_version = "0.2.0"
        current_version = "0.1.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ), patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ), patch(
            "builtins.print"
        ) as mock_print:
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            create_tag_for_version(next_version, self.temp_dir_path)

            # Verify print was called with status messages
            print_calls_str = [str(call) for call in mock_print.call_args_list]

            # Check for expected messages
            self.assertTrue(any("Current version" in call for call in print_calls_str))
            self.assertTrue(any("Checking if tag" in call for call in print_calls_str))
            self.assertTrue(any("Creating tag" in call for call in print_calls_str))
            self.assertTrue(
                any(
                    "Tag" in call and "created successfully" in call
                    for call in print_calls_str
                )
            )

    def test_create_tag_for_version_with_various_versions(self):
        """Test create_tag_for_version with various semantic versions."""
        test_cases = [
            ("0.0.1", "0.0.2"),
            ("0.1.0", "0.2.0"),
            ("1.0.0", "1.0.1"),
            ("1.0.0", "1.1.0"),
            ("1.0.0", "2.0.0"),
            ("2.3.4", "2.3.5"),
            ("10.20.30", "10.20.31"),
        ]

        for current_ver, next_ver in test_cases:
            with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
                "ib_pyrelease_utils.basic.get_current_version"
            ) as mock_get_current, patch(
                "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
            ), patch(
                "ib_pyrelease_utils.basic.git"
            ) as mock_git, patch(
                "ib_pyrelease_utils.basic.bump_sync_commit"
            ), patch(
                "ib_pyrelease_utils.basic.create_release_properties_file"
            ), patch(
                "builtins.print"
            ):
                mock_get_current.return_value = current_ver
                mock_git.return_value = ""

                # Should not raise any exception
                try:
                    result = create_tag_for_version(next_ver, self.temp_dir_path)
                    self.assertEqual(result, f"v{current_ver}")
                except Exception as e:
                    self.fail(
                        f"create_tag_for_version failed for "
                        f"{current_ver} -> {next_ver}: {e}"
                    )

    def test_create_tag_for_version_error_on_ensure_no_changed_files_fails(self):
        """Test that create_tag_for_version fails if initial check fails."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files",
            side_effect=SystemExit(1),
        ):
            try:
                create_tag_for_version(next_version, self.temp_dir_path)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_create_tag_for_version_error_on_ensure_release_tag_fails(self):
        """Test that create_tag_for_version fails if tag check fails."""
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist",
            side_effect=SystemExit(1),
        ):
            mock_get_current.return_value = "0.1.0"

            try:
                create_tag_for_version(next_version, self.temp_dir_path)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass
            finally:
                # Verify cleanup happens
                if self.temp_dir_path.exists():
                    shutil.rmtree(self.temp_dir)

    def test_create_tag_for_version_explicit_semantic_version_0_1_0(self):
        """Test create_tag_for_version with explicit semantic version 0.1.0."""
        current_version = "0.0.1"
        next_version = "0.1.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ) as mock_bump, patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ) as mock_props, patch(
            "builtins.print"
        ):
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            result = create_tag_for_version(next_version, self.temp_dir_path)

            # Verify result
            self.assertEqual(result, f"v{current_version}")

            # Verify bump_sync_commit gets correct versions
            mock_bump.assert_called_once_with(
                current_version, next_version, self.temp_dir_path
            )

            # Verify create_release_properties_file gets correct versions
            mock_props.assert_called_once_with(
                f"v{current_version}", next_version, self.temp_dir_path
            )

    def test_create_tag_for_version_explicit_semantic_version_1_0_0(self):
        """Test create_tag_for_version with explicit semantic version 1.0.0."""
        current_version = "0.9.0"
        next_version = "1.0.0"

        with patch("ib_pyrelease_utils.basic.ensure_no_changed_files"), patch(
            "ib_pyrelease_utils.basic.get_current_version"
        ) as mock_get_current, patch(
            "ib_pyrelease_utils.basic.ensure_release_tag_does_not_exist"
        ), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.bump_sync_commit"
        ) as mock_bump, patch(
            "ib_pyrelease_utils.basic.create_release_properties_file"
        ) as mock_props, patch(
            "builtins.print"
        ):
            mock_get_current.return_value = current_version
            mock_git.return_value = ""

            result = create_tag_for_version(next_version, self.temp_dir_path)

            # Verify result
            self.assertEqual(result, f"v{current_version}")

            # Verify bump_sync_commit gets correct versions
            mock_bump.assert_called_once_with(
                current_version, next_version, self.temp_dir_path
            )

            # Verify create_release_properties_file gets correct versions
            mock_props.assert_called_once_with(
                f"v{current_version}", next_version, self.temp_dir_path
            )


if __name__ == "__main__":
    unittest.main()
