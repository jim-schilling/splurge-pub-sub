"""Unit tests for correlation_id feature.

Test Cases:
    - Constructor correlation_id handling
    - Auto-generation of correlation_id
    - Validation of correlation_id pattern
    - Publish with correlation_id
    - Subscribe with correlation_id filter
    - Topic wildcard with correlation_id
    - Matching logic
"""

import pytest

from splurge_pub_sub import Message, PubSub, SplurgePubSubValueError
from splurge_pub_sub.utility import is_valid_correlation_id, validate_correlation_id


class TestCorrelationIdConstructor:
    """Tests for correlation_id in PubSub constructor."""

    def test_auto_generate_correlation_id_when_none(self) -> None:
        """Test that correlation_id is auto-generated when None."""
        bus = PubSub()
        assert bus.correlation_id is not None
        assert isinstance(bus.correlation_id, str)
        assert len(bus.correlation_id) > 0

    def test_auto_generate_correlation_id_when_empty_string(self) -> None:
        """Test that correlation_id is auto-generated when empty string."""
        bus = PubSub(correlation_id="")
        assert bus.correlation_id is not None
        assert isinstance(bus.correlation_id, str)
        assert len(bus.correlation_id) > 0

    def test_custom_correlation_id(self) -> None:
        """Test providing custom correlation_id."""
        bus = PubSub(correlation_id="my-correlation-id")
        assert bus.correlation_id == "my-correlation-id"

    def test_correlation_id_in_set(self) -> None:
        """Test that instance correlation_id is in correlation_ids set."""
        bus = PubSub(correlation_id="test-123")
        assert "test-123" in bus.correlation_ids
        assert bus.correlation_id in bus.correlation_ids

    def test_uuid_format_correlation_id(self) -> None:
        """Test that UUID format correlation_id is accepted."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        bus = PubSub(correlation_id=uuid_str)
        assert bus.correlation_id == uuid_str

    def test_correlation_id_starts_with_digit(self) -> None:
        """Test that correlation_id can start with digit."""
        bus = PubSub(correlation_id="123abc")
        assert bus.correlation_id == "123abc"

    def test_invalid_correlation_id_starts_with_separator(self) -> None:
        """Test that correlation_id cannot start with separator."""
        with pytest.raises(SplurgePubSubValueError, match="pattern"):
            PubSub(correlation_id="-invalid")

    def test_invalid_correlation_id_too_long(self) -> None:
        """Test that correlation_id length is limited to 64 chars."""
        long_id = "a" * 65
        with pytest.raises(SplurgePubSubValueError, match="length"):
            PubSub(correlation_id=long_id)

    def test_invalid_correlation_id_consecutive_dots(self) -> None:
        """Test that correlation_id cannot have consecutive dots."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive"):
            PubSub(correlation_id="abc..def")

    def test_invalid_correlation_id_consecutive_dashes(self) -> None:
        """Test that correlation_id cannot have consecutive dashes."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive"):
            PubSub(correlation_id="abc--def")

    def test_invalid_correlation_id_consecutive_underscores(self) -> None:
        """Test that correlation_id cannot have consecutive underscores."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive"):
            PubSub(correlation_id="abc__def")

    def test_invalid_correlation_id_mixed_consecutive_separators(self) -> None:
        """Test that correlation_id cannot have consecutive different separators."""
        with pytest.raises(SplurgePubSubValueError, match="consecutive"):
            PubSub(correlation_id="abc.-def")
        with pytest.raises(SplurgePubSubValueError, match="consecutive"):
            PubSub(correlation_id="abc_.def")
        with pytest.raises(SplurgePubSubValueError, match="consecutive"):
            PubSub(correlation_id="abc-_def")

    def test_invalid_correlation_id_wildcard_in_constructor(self) -> None:
        """Test that '*' cannot be used as correlation_id in constructor."""
        with pytest.raises(SplurgePubSubValueError, match="\\*"):
            PubSub(correlation_id="*")


class TestCorrelationIdPublish:
    """Tests for correlation_id in publish()."""

    def test_publish_with_default_correlation_id(self) -> None:
        """Test publish uses instance correlation_id by default."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback)
        bus.publish("test.topic", {"key": "value"})
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "instance-id"

    def test_publish_with_custom_correlation_id(self) -> None:
        """Test publish with custom correlation_id."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        # Subscribe with wildcard to match any correlation_id
        bus.subscribe("test.topic", callback, correlation_id="*")
        bus.publish("test.topic", {"key": "value"}, correlation_id="custom-id")
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "custom-id"

    def test_publish_adds_to_correlation_ids_set(self) -> None:
        """Test that published correlation_ids are added to set."""
        bus = PubSub(correlation_id="instance-id")
        bus.publish("test.topic", {}, correlation_id="custom-1")
        bus.publish("test.topic", {}, correlation_id="custom-2")

        assert "instance-id" in bus.correlation_ids
        assert "custom-1" in bus.correlation_ids
        assert "custom-2" in bus.correlation_ids

    def test_publish_normalizes_empty_string(self) -> None:
        """Test that empty string correlation_id uses instance default."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback)
        bus.publish("test.topic", {}, correlation_id="")
        bus.drain()

        assert received[0].correlation_id == "instance-id"

    def test_publish_rejects_wildcard(self) -> None:
        """Test that '*' cannot be used in publish()."""
        bus = PubSub()
        with pytest.raises(SplurgePubSubValueError, match="\\*"):
            bus.publish("test.topic", {}, correlation_id="*")


class TestCorrelationIdSubscribe:
    """Tests for correlation_id filtering in subscribe()."""

    def test_subscribe_defaults_to_instance_correlation_id(self) -> None:
        """Test subscribe defaults to instance correlation_id filter."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback)
        bus.publish("test.topic", {}, correlation_id="instance-id")
        bus.publish("test.topic", {}, correlation_id="other-id")
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "instance-id"

    def test_subscribe_with_specific_correlation_id(self) -> None:
        """Test subscribe with specific correlation_id filter."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback, correlation_id="target-id")
        bus.publish("test.topic", {}, correlation_id="target-id")
        bus.publish("test.topic", {}, correlation_id="other-id")
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "target-id"

    def test_subscribe_with_wildcard_correlation_id(self) -> None:
        """Test subscribe with '*' matches any correlation_id."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback, correlation_id="*")
        bus.publish("test.topic", {}, correlation_id="id-1")
        bus.publish("test.topic", {}, correlation_id="id-2")
        bus.publish("test.topic", {}, correlation_id="id-3")
        bus.drain()

        assert len(received) == 3

    def test_subscribe_normalizes_empty_string(self) -> None:
        """Test that empty string correlation_id uses instance default."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback, correlation_id="")
        bus.publish("test.topic", {}, correlation_id="instance-id")
        bus.publish("test.topic", {}, correlation_id="other-id")
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "instance-id"

    def test_multiple_subscribers_different_filters(self) -> None:
        """Test multiple subscribers with different correlation_id filters."""
        bus = PubSub(correlation_id="default-id")
        received_a: list[Message] = []
        received_b: list[Message] = []
        received_c: list[Message] = []

        def callback_a(msg: Message) -> None:
            received_a.append(msg)

        def callback_b(msg: Message) -> None:
            received_b.append(msg)

        def callback_c(msg: Message) -> None:
            received_c.append(msg)

        bus.subscribe("test.topic", callback_a, correlation_id="id-a")
        bus.subscribe("test.topic", callback_b, correlation_id="id-b")
        bus.subscribe("test.topic", callback_c, correlation_id="*")

        bus.publish("test.topic", {}, correlation_id="id-a")
        bus.publish("test.topic", {}, correlation_id="id-b")
        bus.publish("test.topic", {}, correlation_id="id-c")
        bus.drain()

        assert len(received_a) == 1
        assert len(received_b) == 1
        assert len(received_c) == 3  # Wildcard matches all


class TestCorrelationIdWildcardTopic:
    """Tests for topic='*' wildcard with correlation_id."""

    def test_wildcard_topic_with_correlation_id_filter(self) -> None:
        """Test topic='*' subscribes to all topics with correlation_id filter."""
        bus = PubSub(correlation_id="instance-id")
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("*", callback, correlation_id="target-id")
        bus.publish("topic.a", {}, correlation_id="target-id")
        bus.publish("topic.b", {}, correlation_id="target-id")
        bus.publish("topic.c", {}, correlation_id="other-id")
        bus.drain()

        assert len(received) == 2
        assert all(msg.correlation_id == "target-id" for msg in received)

    def test_wildcard_topic_with_wildcard_correlation_id(self) -> None:
        """Test topic='*' with correlation_id='*' matches everything."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("*", callback, correlation_id="*")
        bus.publish("topic.a", {}, correlation_id="id-1")
        bus.publish("topic.b", {}, correlation_id="id-2")
        bus.publish("topic.c", {}, correlation_id="id-3")
        bus.drain()

        assert len(received) == 3

    def test_wildcard_topic_unsubscribe(self) -> None:
        """Test unsubscribing from wildcard topic."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        sub_id = bus.subscribe("*", callback)
        bus.publish("test.topic", {})
        bus.drain()
        bus.unsubscribe("*", sub_id)
        bus.publish("test.topic", {})
        bus.drain()

        assert len(received) == 1

    def test_wildcard_topic_clear(self) -> None:
        """Test clearing wildcard subscribers."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("*", callback)
        bus.publish("test.topic", {})
        bus.drain()
        bus.clear("*")
        bus.publish("test.topic", {})
        bus.drain()

        assert len(received) == 1


class TestCorrelationIdMatching:
    """Tests for correlation_id matching logic."""

    def test_exact_match(self) -> None:
        """Test exact correlation_id matching."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback, correlation_id="exact-id")
        bus.publish("test.topic", {}, correlation_id="exact-id")
        bus.publish("test.topic", {}, correlation_id="different-id")
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "exact-id"

    def test_wildcard_match_any(self) -> None:
        """Test wildcard correlation_id matches any."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback, correlation_id="*")
        bus.publish("test.topic", {}, correlation_id="id-1")
        bus.publish("test.topic", {}, correlation_id="id-2")
        bus.publish("test.topic", {}, correlation_id="id-3")
        bus.drain()

        assert len(received) == 3

    def test_topic_and_correlation_id_both_must_match(self) -> None:
        """Test both topic and correlation_id must match."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("topic.a", callback, correlation_id="id-a")
        bus.publish("topic.a", {}, correlation_id="id-a")  # Both match
        bus.publish("topic.a", {}, correlation_id="id-b")  # Topic matches, correlation_id doesn't
        bus.publish("topic.b", {}, correlation_id="id-a")  # Correlation_id matches, topic doesn't
        bus.publish("topic.b", {}, correlation_id="id-b")  # Neither matches
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "id-a"
        assert received[0].topic == "topic.a"


class TestCorrelationIdValidation:
    """Tests for correlation_id validation utility."""

    def test_validate_valid_correlation_id(self) -> None:
        """Test that valid correlation_id passes validation."""
        valid_ids = [
            "abc123",
            "A1.b-C_d",
            "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX.Y-Z",
            "a1",
            "Z9",
        ]
        for cid in valid_ids:
            # Should not raise
            validate_correlation_id(cid)
            assert is_valid_correlation_id(cid) is True

    def test_validate_invalid_correlation_id_empty_string(self) -> None:
        """Test that empty string correlation_id raises error."""
        with pytest.raises(SplurgePubSubValueError, match="empty string"):
            validate_correlation_id("")

    def test_validate_invalid_correlation_id_wildcard(self) -> None:
        """Test that wildcard '*' correlation_id raises error."""
        with pytest.raises(SplurgePubSubValueError, match="\\*"):
            validate_correlation_id("*")

    def test_validate_invalid_correlation_id_too_short(self) -> None:
        """Test that too short correlation_id raises error."""
        with pytest.raises(SplurgePubSubValueError, match="length"):
            validate_correlation_id("a")

    def test_validate_invalid_correlation_id_too_long(self) -> None:
        """Test that too long correlation_id raises error."""
        long_id = "a" * 65
        with pytest.raises(SplurgePubSubValueError, match="length"):
            validate_correlation_id(long_id)

    def test_validate_invalid_correlation_id_pattern(self) -> None:
        """Test that invalid pattern correlation_id raises error."""
        invalid_ids = [
            "-startsWithDash",
            ".startsWithDot",
            "_startsWithUnderscore",
            "endsWithDash-",
            "endsWithDot.",
            "endsWithUnderscore_",
            "consecutive..dots",
            "consecutive--dashes",
            "consecutive__underscores",
            "mixed.-separators",
        ]
        for cid in invalid_ids:
            with pytest.raises(SplurgePubSubValueError, match="pattern|consecutive"):
                validate_correlation_id(cid)
            assert is_valid_correlation_id(cid) is False
