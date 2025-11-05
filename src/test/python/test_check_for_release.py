import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import check_for_release


class TestCheckForRelease(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        # Clean up temporary files and directories
        shutil.rmtree(self.temp_dir)

    def test_check_for_release_directory_not_exists(self):
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            check_for_release("nonexistent_directory")
        self.assertEqual(cm.exception.code, 1)

    def test_check_for_release_not_directory(self):
        # Create a file instead of directory
        test_file = self.temp_dir_path / "test_file.txt"
        test_file.write_text("test")

        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            check_for_release(str(test_file))
        self.assertEqual(cm.exception.code, 1)

    def test_check_for_release_properties_exists(self):
        # Create release.properties file
        release_props = self.temp_dir_path / "release.properties"
        release_props.write_text("test=value")

        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            check_for_release(str(self.temp_dir_path))
        self.assertEqual(cm.exception.code, 1)

    def test_check_for_release_success(self):
        # Test when directory exists and no release.properties file
        try:
            check_for_release(str(self.temp_dir_path))
        except SystemExit:
            self.fail("check_for_release() raised SystemExit unexpectedly")


if __name__ == "__main__":
    unittest.main()
