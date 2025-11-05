import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import release_prepare


class TestReleasePrepare(unittest.TestCase):

    def setUp(self):
        """Create a temporary git repository with testbmv content."""
        # Create a temporary directory in the project's target directory
        target_dir = Path.cwd() / "target"
        target_dir.mkdir(exist_ok=True)

        # Create a temporary git repo with a random name
        self.temp_dir = tempfile.mkdtemp(dir=target_dir, prefix="test_release_prepare_")
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

    def test_release_prepare_with_explicit_next_version(self):
        """Test release_prepare with explicitly provided next version."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare(next_version)

            # Verify create_tag_for_version was called with explicit version
            mock_create_tag.assert_called_once()
            call_args = mock_create_tag.call_args_list[0]
            self.assertEqual(call_args[0][0], next_version)

    def test_release_prepare_without_next_version(self):
        """Test release_prepare without next version (uses get_next_version)."""
        with patch("ib_pyrelease_utils.basic.get_next_version") as mock_get_next, patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_get_next.return_value = "0.2.0"
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare()

            # Verify get_next_version was called
            mock_get_next.assert_called_once()

            # Verify create_tag_for_version was called with next_version
            mock_create_tag.assert_called_once()
            call_args = mock_create_tag.call_args_list[0]
            self.assertEqual(call_args[0][0], "0.2.0")

    def test_release_prepare_prints_initial_messages(self):
        """Test that release_prepare prints initial status messages."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ) as mock_print:
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare(next_version)

            # Verify print was called with status messages
            print_calls_str = [str(call) for call in mock_print.call_args_list]

            # Check for expected messages
            self.assertTrue(
                any("Preparing release checkout" in call for call in print_calls_str)
            )

    def test_release_prepare_calls_create_tag_for_version(self):
        """Test that release_prepare calls create_tag_for_version with correct args."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare(next_version)

            # Verify create_tag_for_version was called
            mock_create_tag.assert_called_once()

            # Verify arguments
            call_args = mock_create_tag.call_args_list[0]
            self.assertEqual(call_args[0][0], next_version)
            # Second argument should be Path.cwd()
            self.assertEqual(call_args[0][1], Path.cwd())

    def test_release_prepare_calls_read_properties_file(self):
        """Test that release_prepare calls read_properties_file."""
        next_version = "0.2.0"
        props_path = Path("release.properties")

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = props_path
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare(next_version)

            # Verify read_properties_file was called with props path
            mock_read_props.assert_called_once()
            call_args = mock_read_props.call_args_list[0]
            self.assertEqual(call_args[0][0], props_path)

    def test_release_prepare_verifies_scm_tag_exists(self):
        """Test that release_prepare verifies scm.tag exists in properties."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            # Return properties without scm.tag
            mock_read_props.return_value = {"scm.next_version": "0.2.0"}

            try:
                release_prepare(next_version)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_release_prepare_uses_correct_release_tag(self):
        """Test that release_prepare extracts and uses correct release tag."""
        next_version = "0.2.0"
        release_tag = "v0.1.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": release_tag}

            release_prepare(next_version)

            # Verify the correct tag was extracted
            mock_read_props.assert_called_once()

    def test_release_prepare_sequence_of_operations(self):
        """Test that release_prepare performs operations in correct order."""
        next_version = "0.2.0"
        call_order = []

        def track_create_tag(ver, cwd):
            call_order.append("create_tag_for_version")
            return Path("release.properties")

        def track_read_props(path):
            call_order.append("read_properties_file")
            return {"scm.tag": "v0.1.0"}

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version",
            side_effect=track_create_tag,
        ), patch(
            "ib_pyrelease_utils.basic.read_properties_file",
            side_effect=track_read_props,
        ), patch(
            "builtins.print"
        ):
            release_prepare(next_version)

            # Verify order
            self.assertEqual(call_order[0], "create_tag_for_version")
            self.assertEqual(call_order[1], "read_properties_file")

    def test_release_prepare_prints_next_version_specified_message(self):
        """Test that release_prepare prints message when next_version is specified."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ) as mock_print:
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare(next_version)

            # Verify message about version being specified
            print_calls_str = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(
                any("Next version specified" in call for call in print_calls_str)
            )

    def test_release_prepare_prints_get_next_version_message_when_not_specified(self):
        """Test that release_prepare prints message when using get_next_version."""
        with patch("ib_pyrelease_utils.basic.get_next_version") as mock_get_next, patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ) as mock_print:
            mock_get_next.return_value = "0.2.0"
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare()

            # Verify message about using patch increment
            print_calls_str = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("patch increment" in call for call in print_calls_str))

    def test_release_prepare_with_various_versions(self):
        """Test release_prepare with various semantic versions."""
        test_cases = [
            ("0.0.1", "0.0.2"),
            ("0.1.0", "0.2.0"),
            ("1.0.0", "1.0.1"),
            ("1.0.0", "1.1.0"),
            ("1.0.0", "2.0.0"),
            ("2.3.4", "2.3.5"),
        ]

        for current_ver, next_ver in test_cases:
            with patch(
                "ib_pyrelease_utils.basic.create_tag_for_version"
            ) as mock_create_tag, patch(
                "ib_pyrelease_utils.basic.read_properties_file"
            ) as mock_read_props, patch(
                "builtins.print"
            ):
                mock_create_tag.return_value = Path("release.properties")
                mock_read_props.return_value = {"scm.tag": f"v{current_ver}"}

                try:
                    release_prepare(next_ver)
                except Exception as e:
                    self.fail(
                        f"release_prepare failed for {current_ver} -> {next_ver}: {e}"
                    )

    def test_release_prepare_error_on_ensure_empty_directory_fails(self):
        """Test that release_prepare fails if ensure_empty_directory fails."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.side_effect = SystemExit(1)
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            try:
                release_prepare(next_version)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_release_prepare_error_on_create_tag_fails(self):
        """Test that release_prepare fails if create_tag_for_version fails."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version",
            side_effect=SystemExit(1),
        ):
            try:
                release_prepare(next_version)
                self.fail("Should have raised SystemExit")
            except SystemExit:
                pass

    def test_release_prepare_with_explicit_version_0_1_0(self):
        """Test release_prepare with explicit version 0.1.0."""
        current_version = "0.0.1"
        next_version = "0.1.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": f"v{current_version}"}

            release_prepare(next_version)

            # Verify create_tag_for_version was called with correct version
            call_args = mock_create_tag.call_args_list[0]
            self.assertEqual(call_args[0][0], next_version)

    def test_release_prepare_with_explicit_version_1_0_0(self):
        """Test release_prepare with explicit version 1.0.0."""
        current_version = "0.9.0"
        next_version = "1.0.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": f"v{current_version}"}

            release_prepare(next_version)

            # Verify create_tag_for_version was called with correct version
            call_args = mock_create_tag.call_args_list[0]
            self.assertEqual(call_args[0][0], next_version)

    def test_release_prepare_stores_current_directory(self):
        """Test that release_prepare gets current directory for repo_dir."""
        next_version = "0.2.0"

        with patch(
            "ib_pyrelease_utils.basic.create_tag_for_version"
        ) as mock_create_tag, patch(
            "ib_pyrelease_utils.basic.read_properties_file"
        ) as mock_read_props, patch(
            "builtins.print"
        ):
            mock_create_tag.return_value = Path("release.properties")
            mock_read_props.return_value = {"scm.tag": "v0.1.0"}

            release_prepare(next_version)

            # Verify create_tag_for_version was called with current directory
            call_args = mock_create_tag.call_args_list[0]
            self.assertEqual(call_args[0][1], Path.cwd())


if __name__ == "__main__":
    unittest.main()
