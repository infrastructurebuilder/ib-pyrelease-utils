import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import ensure_empty_directory


class TestEnsureEmptyDirectory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        # Clean up temporary files and directories
        shutil.rmtree(self.temp_dir)

    def test_ensure_empty_directory_creates_new_directory(self):
        """Test that ensure_empty_directory creates a new directory.

        Tests the case when the directory doesn't exist initially.
        """
        new_dir = self.temp_dir_path / "new_directory"

        # Ensure the directory doesn't exist initially
        self.assertFalse(new_dir.exists())

        # Call the function
        ensure_empty_directory(str(new_dir))

        # Verify the directory was created and is empty
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
        self.assertEqual(list(new_dir.iterdir()), [])

    def test_ensure_empty_directory_creates_nested_directories(self):
        """Test that ensure_empty_directory creates nested directories.

        Tests the case when nested directories don't exist initially.
        """
        nested_dir = self.temp_dir_path / "level1" / "level2" / "level3"

        # Ensure the directory doesn't exist initially
        self.assertFalse(nested_dir.exists())

        # Call the function
        ensure_empty_directory(str(nested_dir))

        # Verify the nested directory was created and is empty
        self.assertTrue(nested_dir.exists())
        self.assertTrue(nested_dir.is_dir())
        self.assertEqual(list(nested_dir.iterdir()), [])

    def test_ensure_empty_directory_empties_existing_directory_with_files(self):
        """Test that ensure_empty_directory removes files from an existing directory."""
        test_dir = self.temp_dir_path / "test_directory"
        test_dir.mkdir()

        # Create some test files
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        # Verify files exist
        self.assertEqual(len(list(test_dir.iterdir())), 2)

        # Call the function
        ensure_empty_directory(str(test_dir))

        # Verify the directory is now empty
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])

    def test_ensure_empty_directory_empties_existing_directory_with_subdirectories(
        self,
    ):
        """Test that ensure_empty_directory removes subdirectories.

        Tests removal of subdirectories from an existing directory.
        """
        test_dir = self.temp_dir_path / "test_directory"
        test_dir.mkdir()

        # Create some test subdirectories with files
        subdir1 = test_dir / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file1.txt").write_text("content1")

        subdir2 = test_dir / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file2.txt").write_text("content2")

        # Verify subdirectories exist
        self.assertEqual(len(list(test_dir.iterdir())), 2)
        self.assertTrue((test_dir / "subdir1").exists())
        self.assertTrue((test_dir / "subdir2").exists())

        # Call the function
        ensure_empty_directory(str(test_dir))

        # Verify the directory is now empty
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])

    def test_ensure_empty_directory_empties_directory_with_mixed_content(self):
        """Test that ensure_empty_directory removes both files and subdirectories."""
        test_dir = self.temp_dir_path / "test_directory"
        test_dir.mkdir()

        # Create mixed content: files and subdirectories
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.txt").write_text("nested content")

        nested_subdir = subdir / "nested_subdir"
        nested_subdir.mkdir()
        (nested_subdir / "deep_file.txt").write_text("deep content")

        # Verify mixed content exists
        self.assertEqual(len(list(test_dir.iterdir())), 3)  # 2 files + 1 subdir
        self.assertTrue((test_dir / "subdir").exists())

        # Call the function
        ensure_empty_directory(str(test_dir))

        # Verify the directory is now empty
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])

    def test_ensure_empty_directory_handles_already_empty_directory(self):
        """Test that ensure_empty_directory works correctly on empty directory."""
        test_dir = self.temp_dir_path / "empty_directory"
        test_dir.mkdir()

        # Verify directory is empty
        self.assertEqual(list(test_dir.iterdir()), [])

        # Call the function
        ensure_empty_directory(str(test_dir))

        # Verify the directory is still empty and exists
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])

    def test_ensure_empty_directory_fails_when_path_is_file(self):
        """Test that ensure_empty_directory exits with error when path is a file."""
        test_file = self.temp_dir_path / "test_file.txt"
        test_file.write_text("test content")

        # Verify it's a file, not a directory
        self.assertTrue(test_file.exists())
        self.assertFalse(test_file.is_dir())

        # Call the function and expect it to exit with error
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            ensure_empty_directory(str(test_file))

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_empty_directory_handles_symlinks(self):
        """Test that ensure_empty_directory properly handles symbolic links."""
        test_dir = self.temp_dir_path / "test_directory"
        test_dir.mkdir()

        # Create a regular file and a symlink
        regular_file = test_dir / "regular_file.txt"
        regular_file.write_text("regular content")

        symlink_file = test_dir / "symlink_file.txt"
        symlink_file.symlink_to(regular_file)

        # Verify both exist
        self.assertEqual(len(list(test_dir.iterdir())), 2)
        self.assertTrue(symlink_file.is_symlink())

        # Call the function
        ensure_empty_directory(str(test_dir))

        # Verify the directory is now empty (both regular file and symlink removed)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])

    def test_ensure_empty_directory_handles_readonly_files(self):
        """Test that ensure_empty_directory can remove read-only files."""
        test_dir = self.temp_dir_path / "test_directory"
        test_dir.mkdir()

        # Create a read-only file
        readonly_file = test_dir / "readonly_file.txt"
        readonly_file.write_text("readonly content")
        readonly_file.chmod(0o444)  # Read-only permissions

        # Verify file exists and is read-only
        self.assertTrue(readonly_file.exists())
        self.assertEqual(len(list(test_dir.iterdir())), 1)

        # Call the function
        ensure_empty_directory(str(test_dir))

        # Verify the directory is now empty (read-only file was removed)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])

    def test_ensure_empty_directory_with_pathlib_path_object(self):
        """Test that ensure_empty_directory works when passed a Path as string."""
        test_dir = self.temp_dir_path / "test_directory"
        test_dir.mkdir()

        # Create some content
        (test_dir / "file.txt").write_text("content")

        # Call the function with Path object converted to string
        ensure_empty_directory(str(test_dir))

        # Verify the directory is empty
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        self.assertEqual(list(test_dir.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
