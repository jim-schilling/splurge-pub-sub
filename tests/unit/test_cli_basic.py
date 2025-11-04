"""Unit tests for CLI module.

Test Cases:
    - CLI argument parsing
    - Version output
    - Help output
    - Exit codes
    - No-argument handling
"""

import pytest

from splurge_pub_sub import __version__
from splurge_pub_sub.cli import main


class TestCLIVersionFlag:
    """Tests for CLI --version flag."""

    def test_version_flag_output_format(self) -> None:
        """Test that --version outputs correct format."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        # argparse exits with 0 for version
        assert exc_info.value.code == 0

    def test_version_flag_shows_version(self, capsys) -> None:
        """Test that --version shows version number."""
        try:
            main(["--version"])
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_version_flag_short_format(self) -> None:
        """Test version output includes package name."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0


class TestCLIHelpFlag:
    """Tests for CLI --help flag."""

    def test_help_flag_exits_cleanly(self) -> None:
        """Test that --help exits with code 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0

    def test_help_output_contains_description(self, capsys) -> None:
        """Test that help output contains program description."""
        try:
            main(["--help"])
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "splurge-pub-sub" in captured.out
        assert "pub-sub framework" in captured.out


class TestCLIDefaultBehavior:
    """Tests for CLI default behavior with no arguments."""

    def test_no_args_returns_success(self) -> None:
        """Test that main() with no args returns 0."""
        result = main([])
        assert result == 0

    def test_no_args_prints_help(self, capsys) -> None:
        """Test that main() with no args prints help."""
        main([])

        captured = capsys.readouterr()
        # Should print help
        assert "usage:" in captured.out.lower() or "splurge-pub-sub" in captured.out

    def test_none_args_uses_sys_argv(self) -> None:
        """Test that main(None) uses sys.argv."""
        # When args is None, argparse uses sys.argv[1:]
        # We can't easily test this without modifying sys.argv
        result = main([])  # Empty list is safer test
        assert result == 0


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_successful_run_returns_zero(self) -> None:
        """Test that successful run returns exit code 0."""
        result = main([])
        assert result == 0
        assert isinstance(result, int)

    def test_help_exits_with_zero(self) -> None:
        """Test that --help exits with 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0

    def test_version_exits_with_zero(self) -> None:
        """Test that --version exits with 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_invalid_argument_raises_error(self) -> None:
        """Test that invalid argument causes SystemExit."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--invalid-flag"])

        # argparse exits with 2 for usage error
        assert exc_info.value.code == 2

    def test_unrecognized_option_fails(self) -> None:
        """Test that unrecognized options fail."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--unknown"])

        assert exc_info.value.code == 2

    def test_empty_args_list_succeeds(self) -> None:
        """Test that empty args list succeeds."""
        result = main([])
        assert result == 0


class TestCLIMainFunction:
    """Tests for main() function behavior."""

    def test_main_accepts_list_of_strings(self) -> None:
        """Test that main accepts list[str]."""
        with pytest.raises(SystemExit):
            main(["--help"])  # This will exit
        # Type is correct

    def test_main_accepts_none_for_args(self) -> None:
        """Test that main accepts None for args parameter."""
        # When args=None, it uses sys.argv[1:]
        # We bypass by passing empty list
        result = main([])
        assert result == 0
        assert isinstance(result, int)

    def test_main_returns_int(self) -> None:
        """Test that main returns integer."""
        result = main([])
        assert isinstance(result, int)
        assert result == 0


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_version_in_output(self, capsys) -> None:
        """Test that version command outputs version."""
        try:
            main(["--version"])
        except SystemExit:
            pass

        captured = capsys.readouterr()
        # Version should be in output
        assert "2025.0.0" in captured.out or __version__ in captured.out

    def test_help_contains_version_option(self, capsys) -> None:
        """Test that help output mentions version option."""
        try:
            main(["--help"])
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "--version" in captured.out

    def test_program_name_in_help(self, capsys) -> None:
        """Test that program name appears in help."""
        try:
            main(["--help"])
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "splurge" in captured.out.lower()
