import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import ensure_release_tag_does_not_exist


class TestEnsureReleaseTagDoesNotExist(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.release_tag = "v1.0.0"
        self.test_cwd = Path(".")

    def test_ensure_release_tag_does_not_exist_success(self):
        """Test success when tag doesn't exist locally or remotely."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ) as mock_print:
            # Mock git commands to return empty results
            mock_git.side_effect = ["", ""]

            # Should not raise any exception
            try:
                ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)
            except SystemExit:
                self.fail(
                    "ensure_release_tag_does_not_exist() raised SystemExit "
                    "unexpectedly"
                )

            # Verify that success message was printed
            self.assertTrue(
                any(
                    "does not exist locally or at origin" in str(call)
                    for call in mock_print.call_args_list
                )
            )

    def test_ensure_release_tag_exists_locally(self):
        """Test that function exits when tag exists locally."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "sys.stderr"
        ), self.assertRaises(SystemExit) as cm:
            # Mock git tag -l to return the tag (meaning it exists)
            mock_git.return_value = self.release_tag

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_release_tag_exists_remotely(self):
        """Test that function exits when tag exists remotely."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "sys.stderr"
        ), self.assertRaises(SystemExit) as cm:
            # First call (local check) returns empty
            # Second call (remote check) returns multiline output with tags
            # Note: remote_result.splitlines() is called in the function
            remote_output = (
                "abc123 refs/tags/v0.9.0\n" "def456 refs/tags/v1.0.0\n" "ghi789 HEAD"
            )
            mock_git.side_effect = ["", remote_output]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_release_tag_exists_locally_error_message(self):
        """Test error message when tag exists locally."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            mock_git.return_value = self.release_tag

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

        self.assertEqual(cm.exception.code, 1)
        # Verify error message contains tag name and helpful instructions
        calls_str = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any(self.release_tag in call for call in calls_str))
        self.assertTrue(any("already exists locally" in call for call in calls_str))
        self.assertTrue(any("git tag -d" in call for call in calls_str))

    def test_ensure_release_tag_exists_remotely_error_message(self):
        """Test error message when tag exists remotely."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            # Multiline output with tags separated by newlines
            remote_output = "abc123 refs/tags/v0.9.0\n" "def456 refs/tags/v1.0.0\n"
            mock_git.side_effect = ["", remote_output]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

        self.assertEqual(cm.exception.code, 1)
        # Verify error message contains appropriate text
        calls_str = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("already exists at origin" in call for call in calls_str))

    def test_ensure_release_tag_calls_git_with_correct_args(self):
        """Test that git is called with correct arguments."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_git.side_effect = ["", ""]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

            # Verify git was called with correct arguments
            self.assertEqual(mock_git.call_count, 2)

            # First call should be git tag -l
            first_call = mock_git.call_args_list[0]
            self.assertIn("tag", first_call[0][0])
            self.assertIn("-l", first_call[0][0])
            self.assertIn(self.release_tag, first_call[0][0])

            # Second call should be git ls-remote
            second_call = mock_git.call_args_list[1]
            self.assertIn("ls-remote", second_call[0][0])
            self.assertIn("--tags", second_call[0][0])
            self.assertIn("origin", second_call[0][0])

    def test_ensure_release_tag_uses_provided_cwd(self):
        """Test that provided cwd is passed to git commands."""
        custom_cwd = Path("/tmp/custom_repo")

        with patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_git.side_effect = ["", ""]

            ensure_release_tag_does_not_exist(self.release_tag, custom_cwd)

            # Verify cwd was passed to both git calls (as positional arg)
            for call in mock_git.call_args_list:
                self.assertEqual(call[0][1], custom_cwd)

    def test_ensure_release_tag_uses_default_cwd(self):
        """Test that default cwd is used when not provided."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_git.side_effect = ["", ""]

            ensure_release_tag_does_not_exist(self.release_tag)

            # Verify cwd defaults to current directory (as positional arg)
            for call in mock_git.call_args_list:
                self.assertEqual(call[0][1], Path("."))

    def test_ensure_release_tag_empty_string_is_not_found(self):
        """Test that empty string from git means tag not found."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ) as mock_print:
            # Empty strings indicate tag not found
            mock_git.side_effect = ["", ""]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

            # Should print success message
            self.assertTrue(
                any("does not exist" in str(call) for call in mock_print.call_args_list)
            )

    def test_ensure_release_tag_multiple_remote_tags(self):
        """Test function with multiple tags in remote output."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "sys.stderr"
        ), self.assertRaises(SystemExit) as cm:
            # Multiline output with our tag present
            remote_output = (
                "abc123 refs/tags/v0.8.0\n"
                "def456 refs/heads/main\n"
                "ghi789 refs/tags/v1.0.0\n"
                "jkl012 refs/tags/v1.1.0\n"
            )
            mock_git.side_effect = ["", remote_output]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

        self.assertEqual(cm.exception.code, 1)

    def test_ensure_release_tag_remote_without_matching_tag(self):
        """Test success when remote has other tags but not this one."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "builtins.print"
        ) as mock_print:
            # Multiline output without our tag
            remote_output = (
                "abc123 refs/tags/v0.9.0\n"
                "def456 refs/tags/v1.1.0\n"
                "ghi789 refs/heads/main\n"
            )
            mock_git.side_effect = ["", remote_output]

            try:
                ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)
            except SystemExit:
                self.fail(
                    "ensure_release_tag_does_not_exist() raised SystemExit "
                    "unexpectedly when tag not in remote"
                )

            # Should print success message
            self.assertTrue(
                any("does not exist" in str(call) for call in mock_print.call_args_list)
            )

    def test_ensure_release_tag_different_tag_names(self):
        """Test with different tag name formats."""
        test_tags = ["v1.0.0", "release-1.0.0", "1.0.0", "myapp-v2.5.3"]

        for tag in test_tags:
            with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
                "builtins.print"
            ):
                mock_git.side_effect = ["", ""]

                try:
                    ensure_release_tag_does_not_exist(tag, self.test_cwd)
                except SystemExit:
                    self.fail(
                        f"ensure_release_tag_does_not_exist() raised "
                        f"SystemExit unexpectedly for tag {tag}"
                    )

    def test_ensure_release_tag_succeeds_does_not_exit(self):
        """Test that function doesn't call sys.exit on success."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch("builtins.print"):
            mock_git.side_effect = ["", ""]

            # This should not raise SystemExit
            result = ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

            # Function should return None
            self.assertIsNone(result)

    def test_ensure_release_tag_local_check_happens_first(self):
        """Test that local check is performed before remote check."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git:
            mock_git.side_effect = ["", ""]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)

            # First call should be for local tag check
            first_call_args = mock_git.call_args_list[0][0][0]
            self.assertEqual(first_call_args[0], "tag")

            # Second call should be for remote tag check
            second_call_args = mock_git.call_args_list[1][0][0]
            self.assertEqual(second_call_args[0], "ls-remote")

    def test_ensure_release_tag_refs_format_in_remote(self):
        """Test that remote check looks for refs/tags/ format."""
        with patch("ib_pyrelease_utils.basic.git") as mock_git, patch(
            "sys.stderr"
        ), self.assertRaises(SystemExit):
            # Remote output in git ls-remote format (as multiline string)
            remote_output = "abc123 refs/tags/v1.0.0"
            mock_git.side_effect = ["", remote_output]

            ensure_release_tag_does_not_exist(self.release_tag, self.test_cwd)


if __name__ == "__main__":
    unittest.main()
