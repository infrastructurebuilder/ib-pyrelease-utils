import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import ensure_no_changed_files


class TestEnsureNoChangedFiles(unittest.TestCase):

    def setUp(self):
        """Create a temporary git repository for testing."""
        # Create a temporary directory in the project's target directory
        target_dir = Path.cwd() / "target"
        target_dir.mkdir(exist_ok=True)

        # Create a temporary git repo with a random name
        self.temp_dir = tempfile.mkdtemp(dir=target_dir, prefix="test_repo_")
        self.temp_dir_path = Path(self.temp_dir)

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

        # Create some random test files and commit them
        self._create_and_commit_test_files()

    def tearDown(self):
        """Clean up temporary git repository."""
        shutil.rmtree(self.temp_dir)

    def _create_and_commit_test_files(self):
        """Helper method to create and commit test files."""
        # Create test files
        file1 = self.temp_dir_path / "file1.txt"
        file1.write_text("content1")

        file2 = self.temp_dir_path / "file2.txt"
        file2.write_text("content2")

        subdir = self.temp_dir_path / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        file3.write_text("content3")

        # Add and commit files
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

    def test_ensure_no_changed_files_success(self):
        """Test that ensure_no_changed_files succeeds when repo is clean."""
        # Should not raise any exception
        try:
            ensure_no_changed_files(self.temp_dir_path)
        except SystemExit:
            self.fail("ensure_no_changed_files() raised SystemExit unexpectedly")

    def test_ensure_no_changed_files_modified_file(self):
        """Test that ensure_no_changed_files fails when a file is modified."""
        # Modify a file
        file1 = self.temp_dir_path / "file1.txt"
        file1.write_text("modified content")

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_untracked_file(self):
        """Test that ensure_no_changed_files fails with untracked files.

        Untracked files show up in git status --porcelain with ??.
        """
        # Create an untracked file
        untracked = self.temp_dir_path / "untracked.txt"
        untracked.write_text("untracked content")

        # Should exit with code 1 (untracked files count as changes)
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_staged_changes(self):
        """Test that ensure_no_changed_files fails with staged changes."""
        # Modify and stage a file
        file1 = self.temp_dir_path / "file1.txt"
        file1.write_text("modified content")

        subprocess.run(
            ["git", "add", "file1.txt"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_deleted_file(self):
        """Test that ensure_no_changed_files fails when a file is deleted."""
        # Delete a file
        file1 = self.temp_dir_path / "file1.txt"
        file1.unlink()

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_new_file(self):
        """Test that ensure_no_changed_files fails with new untracked files.

        New untracked files show up in git status --porcelain with ??.
        """
        # Create a new file without staging it
        new_file = self.temp_dir_path / "new_file.txt"
        new_file.write_text("new content")

        # Should exit with code 1 (untracked files count as changes)
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_renamed_file(self):
        """Test that ensure_no_changed_files fails when a file is renamed."""
        # Rename a file using git
        subprocess.run(
            ["git", "mv", "file1.txt", "file1_renamed.txt"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

        # Should exit with code 1 (git status shows this as a change)
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_multiple_changes(self):
        """Test that ensure_no_changed_files fails with multiple changes."""
        # Make multiple changes
        file1 = self.temp_dir_path / "file1.txt"
        file1.write_text("modified")

        file2 = self.temp_dir_path / "file2.txt"
        file2.unlink()

        new_file = self.temp_dir_path / "new_file.txt"
        new_file.write_text("new")

        subprocess.run(
            ["git", "add", "new_file.txt"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_nonexistent_directory(self):
        """Test that ensure_no_changed_files fails with nonexistent directory."""
        nonexistent = self.temp_dir_path / "nonexistent"

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(nonexistent)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_file_instead_of_dir(self):
        """Test that ensure_no_changed_files fails when path is a file."""
        # Create a file instead of using a directory
        test_file = self.temp_dir_path / "test_file.txt"
        test_file.write_text("test")

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(test_file)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_modified_in_subdirectory(self):
        """Test that ensure_no_changed_files detects changes in subdirectories."""
        # Modify a file in a subdirectory
        subdir_file = self.temp_dir_path / "subdir" / "file3.txt"
        subdir_file.write_text("modified content")

        # Should exit with code 1
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_no_changed_files_after_adding_then_removing(self):
        """Test that ensure_no_changed_files succeeds after adding then removing.

        Create a file, stage it, then delete it without staging the deletion.
        This leaves git in a state where the file shows as deleted in the index
        and doesn't exist in the working directory.
        """
        # Create a new file
        new_file = self.temp_dir_path / "temp_file.txt"
        new_file.write_text("temporary")

        # Stage it
        subprocess.run(
            ["git", "add", "temp_file.txt"],
            cwd=self.temp_dir_path,
            capture_output=True,
            check=True,
        )

        # Delete it without staging the deletion
        new_file.unlink()

        # Should exit with code 1 (file is deleted but not staged)
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_no_changed_files(self.temp_dir_path)

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
