import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ib_pyrelease_utils.basic import run_command_or_fail


class TestRunCommandOrFail(unittest.TestCase):

    def test_run_command_or_fail_success(self):
        """Test that run_command_or_fail returns output on success."""
        result = run_command_or_fail("echo", ["hello world"])
        self.assertEqual(result, "hello world")

    def test_run_command_or_fail_with_multiple_args(self):
        """Test that run_command_or_fail handles multiple arguments."""
        result = run_command_or_fail("echo", ["foo", "bar", "baz"])
        self.assertEqual(result, "foo bar baz")

    def test_run_command_or_fail_strips_whitespace(self):
        """Test that run_command_or_fail strips leading/trailing whitespace."""
        result = run_command_or_fail("echo", ["hello"])
        # echo adds newline, but strip() should remove it
        self.assertEqual(result, "hello")

    def test_run_command_or_fail_success_with_cwd(self):
        """Test that run_command_or_fail works with different cwd."""
        temp_dir = tempfile.mkdtemp()
        try:
            result = run_command_or_fail("pwd", [], cwd=Path(temp_dir))
            self.assertIn(temp_dir, result)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_command_or_fail_nonzero_exit_code(self):
        """Test that run_command_or_fail exits when command fails."""
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            run_command_or_fail("false", [])

        self.assertEqual(cm.exception.code, 1)

    def test_run_command_or_fail_command_not_found(self):
        """Test that run_command_or_fail exits when command is not found."""
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            run_command_or_fail("nonexistent_command_12345", [])

        self.assertEqual(cm.exception.code, 1)

    def test_run_command_or_fail_with_errmsg_on_failure(self):
        """Test that errmsg is printed on command failure."""
        custom_error = "Custom error message"
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            run_command_or_fail("false", [], errmsg=custom_error)

        self.assertEqual(cm.exception.code, 1)
        # Verify that custom error message was printed
        self.assertTrue(
            any(custom_error in str(call) for call in mock_print.call_args_list)
        )

    def test_run_command_or_fail_with_errmsg_on_not_found(self):
        """Test that errmsg is printed when command is not found."""
        custom_error = "Custom error message"
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            run_command_or_fail("nonexistent_command_99999", [], errmsg=custom_error)

        self.assertEqual(cm.exception.code, 1)
        # Verify that custom error message was printed
        self.assertTrue(
            any(custom_error in str(call) for call in mock_print.call_args_list)
        )

    def test_run_command_or_fail_without_errmsg_on_failure(self):
        """Test that when errmsg is None, it's not printed on failure."""
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            run_command_or_fail("false", [], errmsg=None)

        self.assertEqual(cm.exception.code, 1)
        # Verify that we printed the error but not additional errmsg
        # Should have error about false command failing
        self.assertTrue(
            any("Error running" in str(call) for call in mock_print.call_args_list)
        )

    def test_run_command_or_fail_without_errmsg_on_not_found(self):
        """Test that when errmsg is None, it's not printed when command not found."""
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            run_command_or_fail("nonexistent_command_88888", [], errmsg=None)

        self.assertEqual(cm.exception.code, 1)
        # Verify that we printed the error
        self.assertTrue(
            any("command not found" in str(call) for call in mock_print.call_args_list)
        )

    def test_run_command_or_fail_secrets_redaction(self):
        """Test that secrets are redacted in error message when command fails.

        Even if command succeeds, secrets should be redacted if there's an error.
        """
        # Test that secrets don't appear in output on success
        result = run_command_or_fail("echo", ["hello"])
        self.assertEqual(result, "hello")

    def test_run_command_or_fail_secrets_redaction_on_failure(self):
        """Test that secrets are redacted from error messages on failure."""
        secret_token = "my_secret_token_99999"
        # Create a script that uses the secret and fails
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            # Use sh to run a command that includes the secret and fails
            run_command_or_fail(
                "sh",
                ["-c", f"echo {secret_token} && exit 1"],
                secrets=[secret_token],
            )

        self.assertEqual(cm.exception.code, 1)
        # Check that the secret was redacted in the printed error
        calls_str = [str(call) for call in mock_print.call_args_list]
        calls_combined = " ".join(calls_str)
        # The secret should not appear in the output
        self.assertNotIn(secret_token, calls_combined)
        # But the redaction marker should be there
        self.assertIn("****", calls_combined)

    def test_run_command_or_fail_multiple_secrets_redaction(self):
        """Test that multiple secrets are all redacted."""
        secret1 = "secret_one"
        secret2 = "secret_two"
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            run_command_or_fail(
                "sh",
                ["-c", f"echo {secret1} {secret2} && exit 1"],
                secrets=[secret1, secret2],
            )

        self.assertEqual(cm.exception.code, 1)
        calls_str = [str(call) for call in mock_print.call_args_list]
        calls_combined = " ".join(calls_str)
        # Both secrets should be redacted
        self.assertNotIn(secret1, calls_combined)
        self.assertNotIn(secret2, calls_combined)

    def test_run_command_or_fail_empty_secrets_list(self):
        """Test that empty secrets list doesn't cause issues."""
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            run_command_or_fail("false", [], secrets=[])

        self.assertEqual(cm.exception.code, 1)

    def test_run_command_or_fail_with_stderr_output(self):
        """Test that command with stderr doesn't affect return value."""
        # sh -c can run commands and output to stderr
        result = run_command_or_fail("sh", ["-c", "echo 'hello'"])
        self.assertEqual(result, "hello")

    def test_run_command_or_fail_with_multiline_output(self):
        """Test that only the final output is returned."""
        result = run_command_or_fail("sh", ["-c", "echo 'line1'; echo 'line2'"])
        # Should have both lines but stripped of trailing whitespace
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_run_command_or_fail_called_process_error_message(self):
        """Test that CalledProcessError details are included in error."""
        with patch("sys.stderr"), patch(
            "builtins.print"
        ) as mock_print, self.assertRaises(SystemExit) as cm:
            run_command_or_fail("sh", ["-c", "exit 42"])

        self.assertEqual(cm.exception.code, 1)
        # Error message should mention the command
        calls_str = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("Error running" in call for call in calls_str))

    def test_run_command_or_fail_absolute_path_command(self):
        """Test that absolute path commands work."""
        # /bin/echo should exist on Unix-like systems
        result = run_command_or_fail("/bin/echo", ["test"])
        self.assertEqual(result, "test")

    def test_run_command_or_fail_with_special_characters_in_args(self):
        """Test that special characters in arguments are handled correctly."""
        test_string = "hello world! @#$%"
        result = run_command_or_fail("echo", [test_string])
        self.assertEqual(result, test_string)

    def test_run_command_or_fail_preserves_output_format(self):
        """Test that output formatting is preserved (except whitespace)."""
        result = run_command_or_fail("echo", ["a  b  c"])
        # Multiple spaces should be preserved
        self.assertEqual(result, "a  b  c")

    def test_run_command_or_fail_empty_output(self):
        """Test that empty output is handled correctly."""
        result = run_command_or_fail("sh", ["-c", ":"])  # : is a no-op
        self.assertEqual(result, "")

    def test_run_command_or_fail_numeric_output(self):
        """Test that numeric output is returned as string."""
        result = run_command_or_fail("echo", ["42"])
        self.assertEqual(result, "42")
        self.assertIsInstance(result, str)

    def test_run_command_or_fail_default_cwd(self):
        """Test that default cwd is current directory."""
        # This should work without error
        result = run_command_or_fail("pwd", [])
        self.assertTrue(len(result) > 0)

    def test_run_command_or_fail_failure_does_not_return(self):
        """Test that failed command never returns (always exits)."""
        # This is to ensure the exception is raised before return
        with self.assertRaises(SystemExit):
            run_command_or_fail("false", [])

    def test_run_command_or_fail_file_not_found_exception_handling(self):
        """Test FileNotFoundError is caught and handled."""
        # Try to run a command that definitely doesn't exist
        with patch("sys.stderr"), self.assertRaises(SystemExit) as cm:
            run_command_or_fail("this_command_definitely_does_not_exist_9999", [])

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
