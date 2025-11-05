import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import release_perform


class TestReleasePerform(unittest.TestCase):

    def setUp(self):
        """Create a temporary git repository with testbmv content."""
        # Create a temporary directory in the project's target directory
        target_dir = Path.cwd() / "target"
        target_dir.mkdir(exist_ok=True)

        # Create a temporary git repo with a random name
        self.temp_dir = tempfile.mkdtemp(dir=target_dir, prefix="test_release_perform_")
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

        # Create checkout directory
        self.checkout_dir = self.temp_dir_path / "checkout"
        self.checkout_dir.mkdir(exist_ok=True)

        # Create release.properties file
        self.props_file = self.temp_dir_path / "release.properties"
        with open(self.props_file, "w", encoding="utf-8") as f:
            f.write("scm.tag=v0.1.0\n")
            f.write("scm.next_version=0.2.0\n")

    def tearDown(self):
        """Clean up temporary git repository."""
        try:
            # Change back to original directory if in temp dir
            if Path.cwd() == self.checkout_dir or str(self.checkout_dir) in str(
                Path.cwd()
            ):
                os.chdir(self.temp_dir_path)
        except Exception:
            pass

        # Remove the temp directory
        if self.temp_dir_path.exists():
            shutil.rmtree(self.temp_dir)

    def test_release_perform_with_default_checkout_path(self):
        """Test release_perform with default checkout path."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"

        with patch(
            "ib_pyrelease_utils.basic.ensure_empty_directory"
        ) as mock_ensure, patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ) as mock_run_cmd, patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ) as mock_uv, patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_git.return_value = ""
            mock_run_cmd.return_value = ""
            mock_uv.return_value = ""

            # Create checkout directory so ensure_empty_directory succeeds
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Verify ensure_empty_directory was called
            mock_ensure.assert_called_once()

            # Verify git clone was called with correct tag
            clone_calls = [
                call for call in mock_git.call_args_list if "clone" in str(call)
            ]
            self.assertTrue(len(clone_calls) > 0)

            # Verify git push was called
            push_calls = [
                call for call in mock_git.call_args_list if "push" in str(call)
            ]
            self.assertTrue(len(push_calls) > 0)

            # Verify git pull was called
            pull_calls = [
                call for call in mock_git.call_args_list if "pull" in str(call)
            ]
            self.assertTrue(len(pull_calls) > 0)

            # Verify uv publish was called with token
            publish_calls = [
                call for call in mock_uv.call_args_list if "publish" in str(call)
            ]
            self.assertTrue(len(publish_calls) > 0)

    def test_release_perform_with_publish_index(self):
        """Test release_perform with custom publish index."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
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
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_uv.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, publish_index, token)

            # Verify uv publish was called with index parameter
            publish_calls = [
                call for call in mock_uv.call_args_list if "publish" in str(call)
            ]
            self.assertTrue(len(publish_calls) > 0)

            # Check that --index parameter is present
            publish_call_str = str(publish_calls[0])
            self.assertIn("--index", publish_call_str)

    def test_release_perform_missing_scm_tag(self):
        """Test release_perform fails when scm.tag is missing."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch("builtins.print"):
            # Return properties without scm.tag
            mock_read_props.return_value = {"scm.next_version": "0.2.0"}

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            try:
                release_perform(checkout_path, token=token)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_release_perform_empty_scm_tag(self):
        """Test release_perform fails when scm.tag is empty."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch("builtins.print"):
            # Return properties with empty scm.tag
            mock_read_props.return_value = {"scm.tag": ""}

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            try:
                release_perform(checkout_path, token=token)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_release_perform_missing_token(self):
        """Test release_perform fails when token is not provided."""
        checkout_path = self.temp_dir_path / "target" / "checkout"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ), patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            try:
                release_perform(checkout_path)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_release_perform_envrc_file_exists(self):
        """Test release_perform handles .envrc file if it exists."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"

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
        ), patch(
            "pathlib.Path.exists"
        ) as mock_exists:
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_run_cmd.return_value = ""
            # Mock Path.exists to return True for .envrc checks
            mock_exists.side_effect = lambda: True

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Verify direnv allow was called
            direnv_calls = [
                call for call in mock_run_cmd.call_args_list if "direnv" in str(call)
            ]
            self.assertTrue(len(direnv_calls) > 0)

    def test_release_perform_no_envrc_file(self):
        """Test release_perform when .envrc file does not exist."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"

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
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_run_cmd.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Verify direnv allow was NOT called
            direnv_calls = [
                call for call in mock_run_cmd.call_args_list if "direnv" in str(call)
            ]
            self.assertEqual(len(direnv_calls), 0)

    def test_release_perform_with_publish_index_and_token(self):
        """Test release_perform with both publish_index and token."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
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
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_uv.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, publish_index, token)

            # Verify both index and token are used
            self.assertTrue(mock_uv.called)

    def test_release_perform_checkout_path_made_absolute(self):
        """Test that relative checkout_path is converted to absolute."""
        relative_path = Path("target") / "checkout"
        token = "test_token_123"

        with patch(
            "ib_pyrelease_utils.basic.ensure_empty_directory"
        ) as mock_ensure, patch("ib_pyrelease_utils.basic.git"), patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ), patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            # Create the relative path directory
            relative_path.mkdir(parents=True, exist_ok=True)

            release_perform(relative_path, token=token)

            # Verify ensure_empty_directory was called with absolute path
            call_args = mock_ensure.call_args_list[0]
            called_path = call_args[0][0]
            self.assertTrue(called_path.is_absolute())

    def test_release_perform_calls_all_git_operations(self):
        """Test that release_perform calls all required git operations."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"

        with patch("ib_pyrelease_utils.basic.ensure_empty_directory"), patch(
            "ib_pyrelease_utils.basic.git"
        ) as mock_git, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "ib_pyrelease_utils.basic.run_command_or_fail"
        ), patch(
            "ib_pyrelease_utils.basic.ensure_no_changed_files"
        ), patch(
            "ib_pyrelease_utils.basic.uv"
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ):
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}
            mock_git.return_value = ""

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Count git operations
            git_calls = mock_git.call_args_list
            self.assertTrue(len(git_calls) >= 3)  # clone, push, pull

    def test_release_perform_changes_directory_correctly(self):
        """Test that release_perform changes to checkout directory."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
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
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ) as mock_chdir:
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Verify os.chdir was called to change to checkout directory
            chdir_calls = [
                call
                for call in mock_chdir.call_args_list
                if str(checkout_path) in str(call)
            ]
            self.assertTrue(len(chdir_calls) > 0)

    def test_release_perform_returns_to_previous_directory(self):
        """Test that release_perform returns to previous directory after operations."""
        checkout_path = self.temp_dir_path / "target" / "checkout"
        token = "test_token_123"
        original_dir = Path.cwd()

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
        ), patch(
            "builtins.print"
        ), patch(
            "os.chdir"
        ) as mock_chdir:
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            # Create checkout directory
            checkout_path.mkdir(parents=True, exist_ok=True)

            release_perform(checkout_path, token=token)

            # Verify os.chdir was called to return to original directory
            # The last call should be to the original directory
            last_chdir_call = mock_chdir.call_args_list[-1]
            self.assertIn(str(original_dir), str(last_chdir_call))


if __name__ == "__main__":
    unittest.main()
