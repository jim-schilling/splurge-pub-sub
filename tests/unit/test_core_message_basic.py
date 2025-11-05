"""Unit tests for Message class.

Test Cases:
    - Creation with all fields
    - Creation without optional fields
    - Timestamp auto-generation
    - Topic validation
    - Immutability
    - String representation
    - Message data validation (dict with string keys)
"""

from datetime import datetime, timezone

import pytest

from splurge_pub_sub import Message, SplurgePubSubTypeError, SplurgePubSubValueError


class TestMessageCreation:
    """Tests for Message creation and initialization."""

    def test_message_creation_with_all_fields(self) -> None:
        """Test creating message with all fields."""
        metadata = {"source": "api", "version": 1}
        msg = Message(
            topic="user.created",
            data={"id": 123},
            timestamp=datetime.now(timezone.utc),
            metadata=metadata,
        )

        assert msg.topic == "user.created"
        assert msg.data == {"id": 123}
        assert msg.metadata == metadata
        assert isinstance(msg.timestamp, datetime)

    def test_message_creation_without_optional_fields(self) -> None:
        """Test creating message with only required fields."""
        msg = Message(topic="order.created", data={"order_id": 42})

        assert msg.topic == "order.created"
        assert msg.data == {"order_id": 42}
        assert msg.metadata == {}
        assert isinstance(msg.timestamp, datetime)

    def test_message_timestamp_auto_generated(self) -> None:
        """Test that timestamp is auto-generated if not provided."""
        before = datetime.now(timezone.utc)
        msg = Message(topic="test", data={"value": "test"})
        after = datetime.now(timezone.utc)

        assert before <= msg.timestamp <= after

    def test_message_empty_topic_raises_error(self) -> None:
        """Test that empty topic raises SplurgePubSubValueError."""
        with pytest.raises(SplurgePubSubValueError):
            Message(topic="", data={"value": "test"})

    def test_message_double_dot_topic_raises_error(self) -> None:
        """Test that topic with double dots raises error."""
        with pytest.raises(SplurgePubSubValueError):
            Message(topic="user..created", data={"value": "test"})

    def test_message_leading_dot_topic_raises_error(self) -> None:
        """Test that topic starting with dot raises error."""
        with pytest.raises(SplurgePubSubValueError):
            Message(topic=".user.created", data={"value": "test"})

    def test_message_trailing_dot_topic_raises_error(self) -> None:
        """Test that topic ending with dot raises error."""
        with pytest.raises(SplurgePubSubValueError):
            Message(topic="user.created.", data={"value": "test"})


class TestMessagePayloadValidation:
    """Tests for Message data payload validation (dict[str, Any])."""

    def test_message_with_dict_data_succeeds(self) -> None:
        """Test that dict payload is accepted."""
        msg = Message(topic="test", data={"key": "value"})
        assert msg.data == {"key": "value"}

    def test_message_with_empty_dict_succeeds(self) -> None:
        """Test that empty dict is accepted."""
        msg = Message(topic="test", data={})
        assert msg.data == {}

    def test_message_with_complex_dict_succeeds(self) -> None:
        """Test that nested dict with various value types is accepted."""
        data = {
            "id": 123,
            "name": "Alice",
            "tags": ["admin", "user"],
            "metadata": {"created": "2025-11-04", "version": 1},
            "status": None,
        }
        msg = Message(topic="test", data=data)
        assert msg.data == data

    def test_message_with_string_data_raises_error(self) -> None:
        """Test that string payload raises SplurgePubSubTypeError."""
        with pytest.raises(SplurgePubSubTypeError, match="dict\\[str, Any\\]"):
            Message(topic="test", data="string data")

    def test_message_with_int_data_raises_error(self) -> None:
        """Test that int payload raises SplurgePubSubTypeError."""
        with pytest.raises(SplurgePubSubTypeError, match="dict\\[str, Any\\]"):
            Message(topic="test", data=42)

    def test_message_with_list_data_raises_error(self) -> None:
        """Test that list payload raises SplurgePubSubTypeError."""
        with pytest.raises(SplurgePubSubTypeError, match="dict\\[str, Any\\]"):
            Message(topic="test", data=[1, 2, 3])

    def test_message_with_none_data_raises_error(self) -> None:
        """Test that None payload raises SplurgePubSubTypeError."""
        with pytest.raises(SplurgePubSubTypeError, match="dict\\[str, Any\\]"):
            Message(topic="test", data=None)

    def test_message_with_non_string_keys_raises_error(self) -> None:
        """Test that dict with non-string keys raises SplurgePubSubTypeError."""
        with pytest.raises(SplurgePubSubTypeError, match="keys must be strings"):
            Message(topic="test", data={1: "value"})

    def test_message_with_mixed_key_types_raises_error(self) -> None:
        """Test that dict with mixed key types raises error."""
        with pytest.raises(SplurgePubSubTypeError, match="keys must be strings"):
            Message(topic="test", data={"valid": "value", 123: "invalid"})


class TestMessageImmutability:
    """Tests for Message immutability."""

    def test_message_immutable_frozen(self) -> None:
        """Test that Message is frozen (immutable)."""
        from dataclasses import FrozenInstanceError

        msg = Message(topic="test", data={"key": "value"})

        with pytest.raises(FrozenInstanceError):
            msg.topic = "new.topic"  # type: ignore

        with pytest.raises(FrozenInstanceError):
            msg.data = "new_data"  # type: ignore


class TestMessageRepresentation:
    """Tests for Message string representation."""

    def test_message_repr_readable(self) -> None:
        """Test that repr() produces readable output."""
        msg = Message(topic="test.topic", data={"key": "value"})
        repr_str = repr(msg)

        assert "Message" in repr_str
        assert "test.topic" in repr_str
        assert "key" in repr_str
        assert "value" in repr_str

    def test_message_repr_includes_all_fields(self) -> None:
        """Test that repr includes all fields."""
        metadata = {"source": "test"}
        msg = Message(
            topic="test",
            data={"data": "value"},
            metadata=metadata,
        )
        repr_str = repr(msg)

        assert "topic=" in repr_str
        assert "data=" in repr_str
        assert "timestamp=" in repr_str
        assert "metadata=" in repr_str


class TestMessageMetadata:
    """Tests for Message metadata field."""

    def test_message_metadata_dict_defaults_to_empty(self) -> None:
        """Test that metadata dict defaults to empty dict when not provided."""
        msg1 = Message(topic="test", data={"value": "test"})
        assert msg1.metadata == {}

        msg2 = Message(topic="test", data={"value": "test"}, metadata={"key": "value"})
        assert msg2.metadata == {"key": "value"}


class TestMessageCorrelationId:
    """Tests for Message correlation_id validation."""

    def test_message_with_valid_correlation_id_succeeds(self) -> None:
        """Test that valid correlation_id is accepted."""
        msg = Message(topic="test", data={}, correlation_id="workflow-123")
        assert msg.correlation_id == "workflow-123"

    def test_message_with_none_correlation_id_succeeds(self) -> None:
        """Test that None correlation_id is accepted."""
        msg = Message(topic="test", data={}, correlation_id=None)
        assert msg.correlation_id is None

    def test_message_with_uuid_correlation_id_succeeds(self) -> None:
        """Test that UUID format correlation_id is accepted."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        msg = Message(topic="test", data={}, correlation_id=uuid_str)
        assert msg.correlation_id == uuid_str

    def test_message_with_digit_starting_correlation_id_succeeds(self) -> None:
        """Test that correlation_id starting with digit is accepted."""
        msg = Message(topic="test", data={}, correlation_id="123abc")
        assert msg.correlation_id == "123abc"

    def test_message_with_empty_string_correlation_id_raises_error(self) -> None:
        """Test that empty string correlation_id raises error."""
        with pytest.raises(SplurgePubSubValueError, match="cannot be empty string"):
            Message(topic="test", data={}, correlation_id="")

    def test_message_with_wildcard_correlation_id_raises_error(self) -> None:
        """Test that wildcard '*' correlation_id raises error."""
        with pytest.raises(SplurgePubSubValueError, match="cannot be '\\*'"):
            Message(topic="test", data={}, correlation_id="*")

    def test_message_with_too_long_correlation_id_raises_error(self) -> None:
        """Test that correlation_id longer than 64 chars raises error."""
        long_id = "a" * 65
        with pytest.raises(SplurgePubSubValueError, match="length must be 1-64"):
            Message(topic="test", data={}, correlation_id=long_id)

    def test_message_with_zero_length_correlation_id_raises_error(self) -> None:
        """Test that zero-length correlation_id raises error."""
        # Empty string is caught earlier with a specific error message
        with pytest.raises(SplurgePubSubValueError, match="cannot be empty string"):
            Message(topic="test", data={}, correlation_id="")

    def test_message_with_invalid_pattern_correlation_id_raises_error(self) -> None:
        """Test that correlation_id with invalid pattern raises error."""
        with pytest.raises(SplurgePubSubValueError, match="pattern"):
            Message(topic="test", data={}, correlation_id="-invalid")

    def test_message_with_consecutive_dots_correlation_id_raises_error(self) -> None:
        """Test that correlation_id with consecutive dots raises error."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive separator"):
            Message(topic="test", data={}, correlation_id="test..id")

    def test_message_with_consecutive_dashes_correlation_id_raises_error(self) -> None:
        """Test that correlation_id with consecutive dashes raises error."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive separator"):
            Message(topic="test", data={}, correlation_id="test--id")

    def test_message_with_consecutive_underscores_correlation_id_raises_error(self) -> None:
        """Test that correlation_id with consecutive underscores raises error."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive separator"):
            Message(topic="test", data={}, correlation_id="test__id")

    def test_message_with_mixed_consecutive_separators_correlation_id_raises_error(self) -> None:
        """Test that correlation_id with mixed consecutive separators raises error."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive separator"):
            Message(topic="test", data={}, correlation_id="test.-id")

        with pytest.raises(SplurgePubSubValueError, match="consecutive separator"):
            Message(topic="test", data={}, correlation_id="test_.id")

        with pytest.raises(SplurgePubSubValueError, match="consecutive separator"):
            Message(topic="test", data={}, correlation_id="test-_id")
