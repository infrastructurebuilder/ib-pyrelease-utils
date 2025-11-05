import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import bump_sync_commit


class TestBumpSyncCommit(unittest.TestCase):

    def setUp(self):
        """Create a temporary git repository with testbmv content."""
        # Create a temporary directory in the project's target directory
        target_dir = Path.cwd() / "target"
        target_dir.mkdir(exist_ok=True)

        # Create a temporary git repo with a random name
        self.temp_dir = tempfile.mkdtemp(dir=target_dir, prefix="test_bump_")
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
        shutil.rmtree(self.temp_dir)

    def test_bump_sync_commit_with_explicit_version(self):
        """Test bump_sync_commit with an explicitly provided next version."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ):
            # Mock bmv to update pyproject.toml version
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Verify bmv was called to bump version
            self.assertTrue(
                any("bump" in str(call) for call in mock_bmv.call_args_list)
            )

            # Verify uv sync was called
            self.assertTrue(any("sync" in str(call) for call in mock_uv.call_args_list))

            # Verify git add and commit were called
            git_calls_str = [str(call) for call in mock_git.call_args_list]
            self.assertTrue(any("add" in call for call in git_calls_str))
            self.assertTrue(any("commit" in call for call in git_calls_str))

            # Verify the commit message includes both versions
            self.assertTrue(
                any(
                    current_version in call and next_version in call
                    for call in git_calls_str
                )
            )

    def test_bump_sync_commit_with_get_next_version(self):
        """Test bump_sync_commit with version from get_next_version."""
        current_version = "0.1.0"
        next_version_from_func = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "ib_pyrelease_utils.basic.get_next_version"
        ) as mock_get_next:
            mock_get_next.return_value = next_version_from_func
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            # Call with get_next_version result
            bump_sync_commit(
                current_version,
                next_version_from_func,
                self.temp_dir_path,
            )

            # Verify bmv was called with the next version
            bump_calls = [
                call for call in mock_bmv.call_args_list if "bump" in str(call)
            ]
            self.assertTrue(
                any(next_version_from_func in str(call) for call in bump_calls)
            )

    def test_bump_sync_commit_calls_bmv_correctly(self):
        """Test that bump_sync_commit calls bmv with correct arguments."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Check that bmv was called with bump arguments
            bump_call = mock_bmv.call_args_list[0]
            call_args = bump_call[0][0]

            self.assertIn("bump", call_args)
            self.assertIn("--no-commit", call_args)
            self.assertIn("--no-tag", call_args)
            self.assertIn("--allow-dirty", call_args)
            self.assertIn("--new-version", call_args)
            self.assertIn(next_version, call_args)

    def test_bump_sync_commit_calls_uv_sync(self):
        """Test that bump_sync_commit calls uv sync."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Check that uv sync was called
            uv_calls = [call for call in mock_uv.call_args_list if "sync" in str(call)]
            self.assertTrue(len(uv_calls) > 0)

            # Verify the sync call
            sync_call = uv_calls[0]
            self.assertEqual(sync_call[0][0], ["sync"])

    def test_bump_sync_commit_git_add_files(self):
        """Test that bump_sync_commit adds correct files."""
        current_version = "0.1.0"
        next_version = "0.2.0"
        files_to_commit = ["pyproject.toml", "uv.lock"]

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(
                current_version,
                next_version,
                self.temp_dir_path,
                files_to_commit,
            )

            # Find the git add call
            git_add_calls = [
                call for call in mock_git.call_args_list if "add" in str(call)
            ]
            self.assertTrue(len(git_add_calls) > 0)

            # Verify files are in the add call
            add_call = git_add_calls[0]
            call_args = add_call[0][0]
            self.assertEqual(call_args[0], "add")
            for file in files_to_commit:
                self.assertIn(file, call_args)

    def test_bump_sync_commit_git_commit_message(self):
        """Test that bump_sync_commit creates commit with correct message."""
        current_version = "1.0.0"
        next_version = "1.1.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Find the git commit call
            git_commit_calls = [
                call for call in mock_git.call_args_list if "commit" in str(call)
            ]
            self.assertTrue(len(git_commit_calls) > 0)

            # Verify message content
            commit_call = git_commit_calls[0]
            call_args = commit_call[0][0]
            self.assertEqual(call_args[0], "commit")
            self.assertEqual(call_args[1], "-m")

            # Message should contain both versions
            message = call_args[2]
            self.assertIn(current_version, message)
            self.assertIn(next_version, message)

    def test_bump_sync_commit_cwd_passed_correctly(self):
        """Test that bump_sync_commit passes cwd to all subcommands."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Verify cwd is passed to bmv
            for call in mock_bmv.call_args_list:
                self.assertEqual(call[0][1], self.temp_dir_path)

            # Verify cwd is passed to uv
            for call in mock_uv.call_args_list:
                self.assertEqual(call[0][1], self.temp_dir_path)

            # Verify cwd is passed to git
            for call in mock_git.call_args_list:
                self.assertEqual(call[0][1], self.temp_dir_path)

    def test_bump_sync_commit_default_cwd(self):
        """Test bump_sync_commit with default cwd."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            # Call without cwd parameter (should default to Path("."))
            bump_sync_commit(current_version, next_version)

            # Verify default cwd is passed
            for call in mock_bmv.call_args_list:
                self.assertEqual(call[0][1], Path("."))

            for call in mock_uv.call_args_list:
                self.assertEqual(call[0][1], Path("."))

            for call in mock_git.call_args_list:
                self.assertEqual(call[0][1], Path("."))

    def test_bump_sync_commit_default_files_to_commit(self):
        """Test bump_sync_commit with default files_to_commit."""
        current_version = "0.1.0"
        next_version = "0.2.0"
        default_files = ["pyproject.toml", "uv.lock"]

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            # Call without files_to_commit parameter
            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Find the git add call
            git_add_calls = [
                call for call in mock_git.call_args_list if "add" in str(call)
            ]
            self.assertTrue(len(git_add_calls) > 0)

            add_call = git_add_calls[0]
            call_args = add_call[0][0]

            # Verify default files are included
            for file in default_files:
                self.assertIn(file, call_args)

    def test_bump_sync_commit_custom_files_to_commit(self):
        """Test bump_sync_commit with custom files_to_commit."""
        current_version = "0.1.0"
        next_version = "0.2.0"
        custom_files = ["custom_file.txt", "another_file.md"]

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(
                current_version,
                next_version,
                self.temp_dir_path,
                custom_files,
            )

            # Find the git add call
            git_add_calls = [
                call for call in mock_git.call_args_list if "add" in str(call)
            ]
            self.assertTrue(len(git_add_calls) > 0)

            add_call = git_add_calls[0]
            call_args = add_call[0][0]

            # Verify custom files are included instead of defaults
            for file in custom_files:
                self.assertIn(file, call_args)

    def test_bump_sync_commit_sequence_of_operations(self):
        """Test that bump_sync_commit performs operations in correct order."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        call_sequence = []

        def track_bmv(*args, **kwargs):
            call_sequence.append("bmv")
            return ""

        def track_uv(*args, **kwargs):
            call_sequence.append("uv")
            return ""

        def track_git(*args, **kwargs):
            call_sequence.append("git")
            return ""

        with patch("ib_pyrelease_utils.basic.bmv", side_effect=track_bmv), patch(
            "ib_pyrelease_utils.basic.uv", side_effect=track_uv
        ), patch("ib_pyrelease_utils.basic.git", side_effect=track_git):
            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Verify order: bmv (bump), uv (sync), then git operations
            # bmv appears once for bump
            # uv appears once for sync
            # git appears twice (add and commit)
            self.assertEqual(
                call_sequence,
                ["bmv", "uv", "git", "git"],
            )

    def test_bump_sync_commit_prints_status_messages(self):
        """Test that bump_sync_commit prints status messages."""
        current_version = "0.1.0"
        next_version = "0.2.0"

        with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ) as mock_print:
            mock_bmv.return_value = ""
            mock_uv.return_value = ""
            mock_git.return_value = ""

            bump_sync_commit(current_version, next_version, self.temp_dir_path)

            # Verify print was called with status messages
            print_calls_str = [str(call) for call in mock_print.call_args_list]

            # Check for expected messages
            self.assertTrue(any("Bumping version" in call for call in print_calls_str))
            self.assertTrue(any("Version bumped" in call for call in print_calls_str))
            self.assertTrue(any("Syncing" in call for call in print_calls_str))

    def test_bump_sync_commit_with_semantic_versions(self):
        """Test bump_sync_commit with various semantic versions."""
        test_cases = [
            ("1.0.0", "1.0.1"),
            ("1.0.0", "1.1.0"),
            ("1.0.0", "2.0.0"),
            ("0.1.0", "0.1.1"),
            ("0.1.0", "0.2.0"),
            ("0.0.1", "0.0.2"),
        ]

        for current, next_ver in test_cases:
            with patch("ib_pyrelease_utils.basic.bmv") as mock_bmv, patch(
                "ib_pyrelease_utils.basic.uv"
            ) as mock_uv, patch("ib_pyrelease_utils.basic.git") as mock_git:
                mock_bmv.return_value = ""
                mock_uv.return_value = ""
                mock_git.return_value = ""

                # Should not raise any exception
                try:
                    bump_sync_commit(current, next_ver, self.temp_dir_path)
                except Exception as e:
                    self.fail(
                        f"bump_sync_commit failed for {current} -> " f"{next_ver}: {e}"
                    )


if __name__ == "__main__":
    unittest.main()
