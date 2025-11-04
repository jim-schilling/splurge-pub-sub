"""Unit tests for exception hierarchy.

Test Cases:
    - Base exception inheritance
    - All exception variants
    - Exception catching
    - Message preservation
"""

import pytest

from splurge_pub_sub import (
    SplurgePubSubError,
    SplurgePubSubLookupError,
    SplurgePubSubOSError,
    SplurgePubSubRuntimeError,
    SplurgePubSubTypeError,
    SplurgePubSubValueError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_base_exception_inherits_correctly(self) -> None:
        """Test that base exception inherits from Exception."""
        assert issubclass(SplurgePubSubError, Exception)

    def test_valueerror_variant_inherits_from_base(self) -> None:
        """Test SplurgePubSubValueError inheritance."""
        assert issubclass(SplurgePubSubValueError, SplurgePubSubError)
        assert issubclass(SplurgePubSubValueError, ValueError)

    def test_typeerror_variant_inherits_from_base(self) -> None:
        """Test SplurgePubSubTypeError inheritance."""
        assert issubclass(SplurgePubSubTypeError, SplurgePubSubError)
        assert issubclass(SplurgePubSubTypeError, TypeError)

    def test_lookuperror_variant_inherits_from_base(self) -> None:
        """Test SplurgePubSubLookupError inheritance."""
        assert issubclass(SplurgePubSubLookupError, SplurgePubSubError)
        assert issubclass(SplurgePubSubLookupError, LookupError)

    def test_runtimeerror_variant_inherits_from_base(self) -> None:
        """Test SplurgePubSubRuntimeError inheritance."""
        assert issubclass(SplurgePubSubRuntimeError, SplurgePubSubError)
        assert issubclass(SplurgePubSubRuntimeError, RuntimeError)

    def test_oserror_variant_inherits_from_base(self) -> None:
        """Test SplurgePubSubOSError inheritance."""
        assert issubclass(SplurgePubSubOSError, SplurgePubSubError)
        assert issubclass(SplurgePubSubOSError, OSError)


class TestExceptionCatching:
    """Tests for exception catching behavior."""

    def test_exception_can_be_caught_by_base(self) -> None:
        """Test that specific exceptions can be caught by base."""

        def raises_value_error() -> None:
            raise SplurgePubSubValueError("test")

        with pytest.raises(SplurgePubSubError):
            raises_value_error()

    def test_exception_can_be_caught_by_parent_type(self) -> None:
        """Test that exceptions can be caught by parent Python type."""

        def raises_value_error() -> None:
            raise SplurgePubSubValueError("test")

        with pytest.raises(ValueError):
            raises_value_error()

    def test_valueerror_caught_specifically(self) -> None:
        """Test catching specific ValueError variant."""

        def raises_type_error() -> None:
            raise SplurgePubSubTypeError("test")

        # Should not catch ValueError if raising TypeError
        with pytest.raises(SplurgePubSubTypeError):
            raises_type_error()

    def test_multiple_exception_types_with_base(self) -> None:
        """Test catching multiple exception types with base."""

        def raises_error(error_type: int) -> None:
            if error_type == 1:
                raise SplurgePubSubValueError("value error")
            elif error_type == 2:
                raise SplurgePubSubTypeError("type error")
            elif error_type == 3:
                raise SplurgePubSubLookupError("lookup error")

        # All can be caught by base
        for error_type in [1, 2, 3]:
            with pytest.raises(SplurgePubSubError):
                raises_error(error_type)


class TestExceptionMessages:
    """Tests for exception message handling."""

    def test_exception_message_preserved(self) -> None:
        """Test that exception message is preserved."""
        message = "This is a test error message"

        try:
            raise SplurgePubSubValueError(message)
        except SplurgePubSubValueError as e:
            # SplurgeError includes the domain code in the message
            assert message in str(e)

    def test_exception_with_empty_message(self) -> None:
        """Test exception with empty message."""
        exc = SplurgePubSubError("")
        assert isinstance(exc, Exception)

    def test_exception_str_representation(self) -> None:
        """Test str() representation of exceptions."""
        exc = SplurgePubSubValueError("test message")
        assert "test message" in str(exc)


class TestExceptionInstantiation:
    """Tests for creating exception instances."""

    def test_all_exceptions_can_be_instantiated(self) -> None:
        """Test that all exception types can be instantiated."""
        exceptions = [
            SplurgePubSubError("error"),
            SplurgePubSubValueError("value error"),
            SplurgePubSubTypeError("type error"),
            SplurgePubSubLookupError("lookup error"),
            SplurgePubSubRuntimeError("runtime error"),
            SplurgePubSubOSError("os error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_exception_with_args(self) -> None:
        """Test creating exceptions with error_code and details."""
        exc = SplurgePubSubError(message="arg1", error_code="arg2", details={"key": "arg3"})
        assert exc.message == "arg1"
        assert exc.error_code == "arg2"
        assert exc.details == {"key": "arg3"}
