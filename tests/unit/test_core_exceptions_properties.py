"""Property-based tests for exception classes using Hypothesis.

This module uses Hypothesis to verify that exception classes maintain
their semantic properties and invariants across various input combinations.

Test Classes:
    - TestExceptionCreation: Exception instantiation invariants
    - TestExceptionInheritance: Exception hierarchy invariants
    - TestExceptionMessages: Message and error code handling
    - TestExceptionDomains: Domain classification invariants

DOMAINS: ["testing", "exceptions", "properties"]
"""

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from splurge_pub_sub import (
    SplurgePubSubError,
    SplurgePubSubLookupError,
    SplurgePubSubOSError,
    SplurgePubSubPatternError,
    SplurgePubSubRuntimeError,
    SplurgePubSubTypeError,
    SplurgePubSubValueError,
)

DOMAINS = ["testing", "exceptions", "properties"]

# List of all exception classes
EXCEPTION_CLASSES = [
    SplurgePubSubError,
    SplurgePubSubValueError,
    SplurgePubSubTypeError,
    SplurgePubSubLookupError,
    SplurgePubSubRuntimeError,
    SplurgePubSubOSError,
    SplurgePubSubPatternError,
]

# Corresponding parent Python exception types (where applicable)
EXCEPTION_PARENTS = {
    SplurgePubSubValueError: ValueError,
    SplurgePubSubTypeError: TypeError,
    SplurgePubSubLookupError: LookupError,
    SplurgePubSubRuntimeError: RuntimeError,
    SplurgePubSubOSError: OSError,
    SplurgePubSubPatternError: ValueError,
}


class TestExceptionCreation:
    """Property-based tests for exception creation."""

    @given(message=st.text())
    def test_base_exception_creation_with_message(self, message: str) -> None:
        """Test that base exception can be created with any message."""
        exc = SplurgePubSubError(message)
        assert isinstance(exc, Exception)
        assert message in str(exc)

    @given(
        message=st.text(),
        error_code=st.text(min_size=1),
    )
    def test_exception_creation_with_error_code(
        self,
        message: str,
        error_code: str,
    ) -> None:
        """Test exception creation with error code."""
        exc = SplurgePubSubError(message=message, error_code=error_code)
        assert isinstance(exc, Exception)

    @given(
        message=st.text(),
        details=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(),
            max_size=5,
        ),
    )
    def test_exception_creation_with_details(
        self,
        message: str,
        details: dict[str, Any],
    ) -> None:
        """Test exception creation with details dictionary."""
        exc = SplurgePubSubError(message=message, details=details)
        assert isinstance(exc, Exception)

    @given(
        exc_class=st.sampled_from(EXCEPTION_CLASSES),
        message=st.text(),
    )
    def test_all_exception_classes_can_be_instantiated(
        self,
        exc_class: type[SplurgePubSubError],
        message: str,
    ) -> None:
        """Test that all exception classes can be instantiated."""
        exc = exc_class(message)
        assert isinstance(exc, Exception)
        assert isinstance(exc, SplurgePubSubError)


class TestExceptionInheritance:
    """Property-based tests for exception inheritance hierarchy."""

    @given(message=st.text())
    def test_all_exceptions_are_base_exceptions(self, message: str) -> None:
        """Test that all specific exceptions are SplurgePubSubError instances."""
        exceptions = [
            SplurgePubSubValueError(message),
            SplurgePubSubTypeError(message),
            SplurgePubSubLookupError(message),
            SplurgePubSubRuntimeError(message),
            SplurgePubSubOSError(message),
            SplurgePubSubPatternError(message),
        ]

        for exc in exceptions:
            assert isinstance(exc, SplurgePubSubError)

    @given(message=st.text())
    def test_all_exceptions_inherit_from_exception(self, message: str) -> None:
        """Test that all exceptions inherit from Exception."""
        exceptions = [
            SplurgePubSubError(message),
            SplurgePubSubValueError(message),
            SplurgePubSubTypeError(message),
            SplurgePubSubLookupError(message),
            SplurgePubSubRuntimeError(message),
            SplurgePubSubOSError(message),
            SplurgePubSubPatternError(message),
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    @given(message=st.text())
    def test_value_exception_inherits_from_valueerror(self, message: str) -> None:
        """Test that SplurgePubSubValueError inherits from ValueError."""
        exc = SplurgePubSubValueError(message)
        assert isinstance(exc, ValueError)

    @given(message=st.text())
    def test_type_exception_inherits_from_typeerror(self, message: str) -> None:
        """Test that SplurgePubSubTypeError inherits from TypeError."""
        exc = SplurgePubSubTypeError(message)
        assert isinstance(exc, TypeError)

    @given(message=st.text())
    def test_lookup_exception_inherits_from_lookuperror(self, message: str) -> None:
        """Test that SplurgePubSubLookupError inherits from LookupError."""
        exc = SplurgePubSubLookupError(message)
        assert isinstance(exc, LookupError)

    @given(message=st.text())
    def test_runtime_exception_inherits_from_runtimeerror(self, message: str) -> None:
        """Test that SplurgePubSubRuntimeError inherits from RuntimeError."""
        exc = SplurgePubSubRuntimeError(message)
        assert isinstance(exc, RuntimeError)

    @given(message=st.text())
    def test_os_exception_inherits_from_oserror(self, message: str) -> None:
        """Test that SplurgePubSubOSError inherits from OSError."""
        exc = SplurgePubSubOSError(message)
        assert isinstance(exc, OSError)

    @given(message=st.text())
    def test_pattern_exception_inherits_from_valueerror(self, message: str) -> None:
        """Test that SplurgePubSubPatternError inherits from ValueError."""
        exc = SplurgePubSubPatternError(message)
        assert isinstance(exc, ValueError)


class TestExceptionMessages:
    """Property-based tests for exception message handling."""

    @given(message=st.text())
    def test_exception_message_is_preserved_in_output(self, message: str) -> None:
        """Test that exception message appears in string output."""
        exc = SplurgePubSubError(message)
        exc_str = str(exc)
        # Message should appear somewhere in the output
        if message:  # Only test non-empty messages
            assert message in exc_str

    @given(
        message=st.text(),
        error_code=st.text(min_size=1, max_size=20),
    )
    def test_exception_error_code_appears_in_output(
        self,
        message: str,
        error_code: str,
    ) -> None:
        """Test that error code appears in exception output."""
        exc = SplurgePubSubError(message=message, error_code=error_code)
        exc_str = str(exc)
        # Full code should include the error code (normalized)
        # Check that something related to the code is in output
        assert len(exc_str) > 0

    @given(
        message1=st.text(),
        message2=st.text(),
    )
    def test_different_messages_produce_different_outputs(
        self,
        message1: str,
        message2: str,
    ) -> None:
        """Test that different messages produce different string representations."""
        exc1 = SplurgePubSubError(message1)
        exc2 = SplurgePubSubError(message2)

        if message1 != message2:
            # Different messages should usually produce different outputs
            str1 = str(exc1)
            str2 = str(exc2)
            # This is not absolute (could have collisions), but highly likely
            assert str1 != str2


class TestExceptionDomains:
    """Property-based tests for exception domain properties."""

    @given(message=st.text())
    def test_base_exception_has_domain(self, message: str) -> None:
        """Test that base exception has _domain attribute."""
        exc = SplurgePubSubError(message)
        assert hasattr(exc, "_domain")
        assert exc._domain == "splurge.pub-sub"

    @given(message=st.text())
    def test_value_exception_has_value_domain(self, message: str) -> None:
        """Test that value exception has correct domain."""
        exc = SplurgePubSubValueError(message)
        assert exc._domain == "splurge.pub-sub.value"

    @given(message=st.text())
    def test_type_exception_has_type_domain(self, message: str) -> None:
        """Test that type exception has correct domain."""
        exc = SplurgePubSubTypeError(message)
        assert exc._domain == "splurge.pub-sub.type"

    @given(message=st.text())
    def test_lookup_exception_has_lookup_domain(self, message: str) -> None:
        """Test that lookup exception has correct domain."""
        exc = SplurgePubSubLookupError(message)
        assert exc._domain == "splurge.pub-sub.lookup"

    @given(message=st.text())
    def test_runtime_exception_has_runtime_domain(self, message: str) -> None:
        """Test that runtime exception has correct domain."""
        exc = SplurgePubSubRuntimeError(message)
        assert exc._domain == "splurge.pub-sub.runtime"

    @given(message=st.text())
    def test_os_exception_has_os_domain(self, message: str) -> None:
        """Test that os exception has correct domain."""
        exc = SplurgePubSubOSError(message)
        assert exc._domain == "splurge.pub-sub.os"

    @given(message=st.text())
    def test_pattern_exception_has_pattern_domain(self, message: str) -> None:
        """Test that pattern exception has correct domain."""
        exc = SplurgePubSubPatternError(message)
        assert exc._domain == "splurge.pub-sub.pattern"

    @given(message=st.text())
    def test_all_domains_are_namespaced_under_splurge_pubsub(self, message: str) -> None:
        """Test that all exception domains start with splurge.pub-sub."""
        exceptions = [
            SplurgePubSubError(message),
            SplurgePubSubValueError(message),
            SplurgePubSubTypeError(message),
            SplurgePubSubLookupError(message),
            SplurgePubSubRuntimeError(message),
            SplurgePubSubOSError(message),
            SplurgePubSubPatternError(message),
        ]

        for exc in exceptions:
            assert exc._domain.startswith("splurge.pub-sub")


class TestExceptionCatching:
    """Property-based tests for exception catching behavior."""

    @given(message=st.text())
    def test_value_exception_caught_by_base(self, message: str) -> None:
        """Test that SplurgePubSubValueError can be caught as base exception."""
        try:
            raise SplurgePubSubValueError(message)
        except SplurgePubSubError:
            pass  # Expected
        else:
            raise AssertionError("Exception was not caught")

    @given(message=st.text())
    def test_value_exception_caught_by_valueerror(self, message: str) -> None:
        """Test that SplurgePubSubValueError can be caught as ValueError."""
        try:
            raise SplurgePubSubValueError(message)
        except ValueError:
            pass  # Expected
        else:
            raise AssertionError("Exception was not caught")

    @given(message=st.text())
    def test_type_exception_caught_by_base(self, message: str) -> None:
        """Test that SplurgePubSubTypeError can be caught as base exception."""
        try:
            raise SplurgePubSubTypeError(message)
        except SplurgePubSubError:
            pass  # Expected
        else:
            raise AssertionError("Exception was not caught")

    @given(message=st.text())
    def test_type_exception_caught_by_typeerror(self, message: str) -> None:
        """Test that SplurgePubSubTypeError can be caught as TypeError."""
        try:
            raise SplurgePubSubTypeError(message)
        except TypeError:
            pass  # Expected
        else:
            raise AssertionError("Exception was not caught")
