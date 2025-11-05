"""Unit tests for package root module (__init__.py).

Test Cases:
    - Package version
    - Package metadata (author, license)
    - Public API exports (__all__)
    - Importable symbols
"""

import splurge_pub_sub
from splurge_pub_sub import (
    Callback,
    ErrorHandler,
    Message,
    MessageData,
    PubSub,
    SplurgePubSubError,
    SplurgePubSubLookupError,
    SplurgePubSubOSError,
    SplurgePubSubPatternError,
    SplurgePubSubRuntimeError,
    SplurgePubSubTypeError,
    SplurgePubSubValueError,
    SubscriberId,
    Topic,
    TopicDecorator,
    TopicPattern,
    default_error_handler,
)


class TestPackageVersion:
    """Tests for package version."""

    def test_version_attribute_exists(self) -> None:
        """Test that __version__ attribute exists."""
        assert hasattr(splurge_pub_sub, "__version__")

    def test_version_is_string(self) -> None:
        """Test that version is a string."""
        assert isinstance(splurge_pub_sub.__version__, str)

    def test_version_format(self) -> None:
        """Test that version follows expected format."""
        version = splurge_pub_sub.__version__
        # Should be in format like "2025.0.0" (CalVer)
        assert "." in version
        parts = version.split(".")
        assert len(parts) >= 2

    def test_version_not_empty(self) -> None:
        """Test that version is not empty."""
        assert len(splurge_pub_sub.__version__) > 0


class TestPackageMetadata:
    """Tests for package metadata."""

    def test_author_attribute_exists(self) -> None:
        """Test that __author__ attribute exists."""
        assert hasattr(splurge_pub_sub, "__author__")

    def test_author_is_string(self) -> None:
        """Test that author is a string."""
        assert isinstance(splurge_pub_sub.__author__, str)

    def test_author_value(self) -> None:
        """Test that author is Jim Schilling."""
        assert splurge_pub_sub.__author__ == "Jim Schilling"

    def test_license_attribute_exists(self) -> None:
        """Test that __license__ attribute exists."""
        assert hasattr(splurge_pub_sub, "__license__")

    def test_license_is_string(self) -> None:
        """Test that license is a string."""
        assert isinstance(splurge_pub_sub.__license__, str)

    def test_license_value(self) -> None:
        """Test that license is MIT."""
        assert splurge_pub_sub.__license__ == "MIT"


class TestPublicAPI:
    """Tests for public API (__all__)."""

    def test_all_list_exists(self) -> None:
        """Test that __all__ is defined."""
        assert hasattr(splurge_pub_sub, "__all__")

    def test_all_is_list(self) -> None:
        """Test that __all__ is a list."""
        assert isinstance(splurge_pub_sub.__all__, list)

    def test_all_not_empty(self) -> None:
        """Test that __all__ is not empty."""
        assert len(splurge_pub_sub.__all__) > 0

    def test_all_contains_pubsub(self) -> None:
        """Test that __all__ contains PubSub."""
        assert "PubSub" in splurge_pub_sub.__all__

    def test_all_contains_message(self) -> None:
        """Test that __all__ contains Message."""
        assert "Message" in splurge_pub_sub.__all__

    def test_all_contains_exceptions(self) -> None:
        """Test that __all__ contains exception types."""
        assert "SplurgePubSubError" in splurge_pub_sub.__all__
        assert "SplurgePubSubValueError" in splurge_pub_sub.__all__
        assert "SplurgePubSubTypeError" in splurge_pub_sub.__all__

    def test_all_contains_types(self) -> None:
        """Test that __all__ contains type aliases."""
        assert "MessageData" in splurge_pub_sub.__all__
        assert "Topic" in splurge_pub_sub.__all__
        assert "SubscriberId" in splurge_pub_sub.__all__

    def test_all_contains_topic_pattern(self) -> None:
        """Test that __all__ contains TopicPattern."""
        assert "TopicPattern" in splurge_pub_sub.__all__


class TestPublicExports:
    """Tests for public exports from package."""

    def test_pubsub_importable(self) -> None:
        """Test that PubSub is importable."""
        assert PubSub is not None

    def test_message_importable(self) -> None:
        """Test that Message is importable."""
        assert Message is not None

    def test_all_exceptions_importable(self) -> None:
        """Test that all exceptions are importable."""
        assert SplurgePubSubError is not None
        assert SplurgePubSubValueError is not None
        assert SplurgePubSubTypeError is not None
        assert SplurgePubSubLookupError is not None
        assert SplurgePubSubRuntimeError is not None
        assert SplurgePubSubOSError is not None
        assert SplurgePubSubPatternError is not None

    def test_type_aliases_importable(self) -> None:
        """Test that type aliases are importable."""
        assert MessageData is not None
        assert Topic is not None
        assert SubscriberId is not None

    def test_error_handler_importable(self) -> None:
        """Test that ErrorHandler is importable."""
        assert ErrorHandler is not None

    def test_default_error_handler_importable(self) -> None:
        """Test that default_error_handler is importable."""
        assert default_error_handler is not None

    def test_topic_pattern_importable(self) -> None:
        """Test that TopicPattern is importable."""
        assert TopicPattern is not None

    def test_callback_importable(self) -> None:
        """Test that Callback is importable."""
        assert Callback is not None

    def test_topic_decorator_importable(self) -> None:
        """Test that TopicDecorator is importable."""
        assert TopicDecorator is not None


class TestImportVariations:
    """Tests for different import styles."""

    def test_import_from_package_root(self) -> None:
        """Test importing from package root."""
        from splurge_pub_sub import PubSub as PS1
        from splurge_pub_sub.pubsub import PubSub as PS2

        # Should be same class
        assert PS1 is PS2

    def test_import_message_from_root(self) -> None:
        """Test importing Message from package root."""
        from splurge_pub_sub import Message as M1
        from splurge_pub_sub.message import Message as M2

        assert M1 is M2

    def test_import_exceptions_from_root(self) -> None:
        """Test importing exceptions from package root."""
        from splurge_pub_sub import SplurgePubSubError as E1
        from splurge_pub_sub.exceptions import SplurgePubSubError as E2

        assert E1 is E2


class TestPackageIntegrity:
    """Tests for overall package integrity."""

    def test_package_has_version(self) -> None:
        """Test package has version."""
        assert hasattr(splurge_pub_sub, "__version__")
        assert len(splurge_pub_sub.__version__) > 0

    def test_package_has_author(self) -> None:
        """Test package has author."""
        assert hasattr(splurge_pub_sub, "__author__")

    def test_package_has_license(self) -> None:
        """Test package has license."""
        assert hasattr(splurge_pub_sub, "__license__")

    def test_package_has_all(self) -> None:
        """Test package defines __all__."""
        assert hasattr(splurge_pub_sub, "__all__")

    def test_all_items_are_strings(self) -> None:
        """Test that all __all__ items are strings."""
        for item in splurge_pub_sub.__all__:
            assert isinstance(item, str)

    def test_all_items_are_accessible(self) -> None:
        """Test that all __all__ items are accessible."""
        for item_name in splurge_pub_sub.__all__:
            assert hasattr(splurge_pub_sub, item_name)
