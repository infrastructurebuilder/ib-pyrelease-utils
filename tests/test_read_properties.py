import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import (
    create_release_properties_file,
    read_properties_file,
)


class TestReadPropertiesFile(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        # Clean up temporary files and directories
        shutil.rmtree(self.temp_dir)

    def test_read_properties_file_valid(self):
        # Create a test properties file
        props_file = self.temp_dir_path / "test.properties"
        props_content = """# This is a comment
key1=value1
key2=value with spaces
key3=value=with=equals
! Another comment
key4=value4
"""
        props_file.write_text(props_content)

        result = read_properties_file(props_file)

        expected = {
            "key1": "value1",
            "key2": "value with spaces",
            "key3": "value=with=equals",
            "key4": "value4",
        }
        self.assertEqual(result, expected)

    def test_read_properties_file_empty(self):
        # Create empty properties file
        props_file = self.temp_dir_path / "empty.properties"
        props_file.write_text("")

        result = read_properties_file(props_file)
        self.assertEqual(result, {})

    def test_read_properties_file_not_found(self):
        with patch("sys.stderr"):
            result = read_properties_file(Path("nonexistent.properties"))
            self.assertEqual(result, {})

    def test_read_properties_file_comments_only(self):
        props_file = self.temp_dir_path / "comments.properties"
        props_content = """# Comment 1
! Comment 2

# Another comment
"""
        props_file.write_text(props_content)

        result = read_properties_file(props_file)
        self.assertEqual(result, {})

    def test_read_properties_file_exception_during_read(self):
        """Test exception handling when reading properties file (lines 34-36)."""
        props_file = self.temp_dir_path / "test.properties"
        props_file.write_text("key=value\n")

        with patch("builtins.open", side_effect=OSError("Mock read error")), patch(
            "sys.stderr"
        ):
            with self.assertRaises(SystemExit) as context:
                read_properties_file(props_file)

            # Verify it exits with code 1
            self.assertEqual(context.exception.code, 1)


class TestCreateReleasePropertiesFile(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory in target for testing."""
        target_dir = Path.cwd() / "target"
        target_dir.mkdir(exist_ok=True)

        self.temp_dir = tempfile.mkdtemp(dir=target_dir, prefix="test_props_")
        self.temp_dir_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_create_release_properties_file_basic(self):
        """Test creating release.properties with basic inputs."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        # Verify return value is correct
        self.assertEqual(result_path, self.temp_dir_path / "release.properties")

        # Verify file exists
        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_file())

        # Verify content using read_properties_file
        props = read_properties_file(result_path)
        self.assertEqual(props["scm.tag"], release_tag)
        self.assertEqual(props["scm.next_version"], next_version)

    def test_create_release_properties_file_default_cwd(self):
        """Test creating release.properties with default cwd."""
        release_tag = "v2.0.0"
        next_version = "2.1.0"

        # Change to temp directory to test default cwd
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir_path)

            result_path = create_release_properties_file(release_tag, next_version)

            # Verify file was created in current directory
            self.assertTrue(result_path.exists())

            # Verify content
            props = read_properties_file(result_path)
            self.assertEqual(props["scm.tag"], release_tag)
            self.assertEqual(props["scm.next_version"], next_version)
        finally:
            os.chdir(original_cwd)

    def test_create_release_properties_file_custom_cwd(self):
        """Test creating release.properties with custom cwd."""
        release_tag = "v1.5.0"
        next_version = "1.6.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        # Verify file is in the custom cwd
        self.assertEqual(result_path.parent, self.temp_dir_path)
        self.assertEqual(result_path.name, "release.properties")

    def test_create_release_properties_file_content_format(self):
        """Test that release.properties has correct format."""
        release_tag = "v3.0.0"
        next_version = "3.1.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        # Read raw file content
        raw_content = result_path.read_text(encoding="utf-8")

        # Verify format includes both keys and final newline
        self.assertIn(f"scm.tag={release_tag}", raw_content)
        self.assertIn(f"scm.next_version={next_version}", raw_content)
        self.assertTrue(raw_content.endswith("\n"))

    def test_create_release_properties_file_various_versions(self):
        """Test with various version formats."""
        test_cases = [
            ("v0.1.0", "0.2.0"),
            ("v1.0.0-alpha", "1.0.0"),
            ("v2.5.3", "2.5.4"),
            ("release-v1.0", "1.1.0"),
        ]

        for i, (tag, version) in enumerate(test_cases):
            # Create subdirectory for each test case
            test_dir = self.temp_dir_path / f"case_{i}"
            test_dir.mkdir()

            result_path = create_release_properties_file(tag, version, test_dir)

            # Verify content
            props = read_properties_file(result_path)
            self.assertEqual(props["scm.tag"], tag)
            self.assertEqual(props["scm.next_version"], version)

    def test_create_release_properties_file_overwrites_existing(self):
        """Test that function overwrites existing file."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        # Create initial file
        props_file = self.temp_dir_path / "release.properties"
        props_file.write_text("old.key=old.value\n")

        # Create new properties (should overwrite)
        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        # Verify old content is gone
        props = read_properties_file(result_path)
        self.assertNotIn("old.key", props)

        # Verify new content is present
        self.assertEqual(props["scm.tag"], release_tag)
        self.assertEqual(props["scm.next_version"], next_version)

    def test_create_release_properties_file_returns_path_object(self):
        """Test that return value is a Path object."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        self.assertIsInstance(result_path, Path)

    def test_create_release_properties_file_prints_message(self):
        """Test that function prints success message."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        with patch("builtins.print") as mock_print:
            create_release_properties_file(
                release_tag, next_version, self.temp_dir_path
            )

            # Verify print was called with success message
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            self.assertIn("release.properties", call_args)
            self.assertIn("successfully", call_args)

    def test_create_release_properties_file_in_subdirectory(self):
        """Test creating release.properties in a subdirectory."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        # Create a subdirectory
        subdir = self.temp_dir_path / "subdir"
        subdir.mkdir()

        result_path = create_release_properties_file(release_tag, next_version, subdir)

        # Verify file is in the subdirectory
        self.assertEqual(result_path.parent, subdir)
        self.assertTrue(result_path.exists())

        # Verify content
        props = read_properties_file(result_path)
        self.assertEqual(props["scm.tag"], release_tag)
        self.assertEqual(props["scm.next_version"], next_version)

    def test_create_release_properties_file_exactly_two_keys(self):
        """Test that file contains exactly two keys."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        props = read_properties_file(result_path)
        self.assertEqual(len(props), 2)
        self.assertIn("scm.tag", props)
        self.assertIn("scm.next_version", props)

    def test_create_release_properties_file_encoding(self):
        """Test that file is created with UTF-8 encoding."""
        release_tag = "v1.0.0-α"  # Unicode character
        next_version = "1.1.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        # Read with UTF-8 encoding should work
        props = read_properties_file(result_path)
        self.assertEqual(props["scm.tag"], release_tag)

    def test_create_release_properties_file_special_characters(self):
        """Test with special characters in version strings."""
        release_tag = "v1.0.0-rc.1+build.123"
        next_version = "1.0.0-rc.2+build.124"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        props = read_properties_file(result_path)
        self.assertEqual(props["scm.tag"], release_tag)
        self.assertEqual(props["scm.next_version"], next_version)

    def test_create_release_properties_file_file_permissions(self):
        """Test that created file is readable."""
        release_tag = "v1.0.0"
        next_version = "1.1.0"

        result_path = create_release_properties_file(
            release_tag, next_version, self.temp_dir_path
        )

        # Verify file is readable
        self.assertTrue(result_path.stat().st_mode & 0o400)


if __name__ == "__main__":
    unittest.main()
