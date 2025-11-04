"""Property-based tests for Message class using Hypothesis.

This module uses Hypothesis to generate arbitrary Message instances and
verify invariants that should hold across all valid message configurations.

Test Classes:
    - TestMessageInvariants: Property-based invariants for Message creation
    - TestMessageImmutability: Property-based immutability verification
    - TestMessageDataHandling: Property-based data handling and transformation

DOMAINS: ["testing", "message", "properties"]
"""

from datetime import datetime, timezone
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from splurge_pub_sub import Message
from splurge_pub_sub.types import MessageData, Topic

DOMAINS = ["testing", "message", "properties"]


# Custom strategies for generating valid message components
@st.composite
def message_topics(draw: Any) -> Topic:
    """Strategy for generating valid topic strings.

    Topics are dot-separated hierarchical identifiers.
    """
    segments = draw(
        st.lists(
            st.text(alphabet="a-z0-9_", min_size=1, max_size=10),
            min_size=1,
            max_size=5,
        )
    )
    return Topic(".".join(segments))


@st.composite
def message_data(draw: Any) -> MessageData:
    """Strategy for generating valid message data.

    Message data must be a dict with string keys.
    """
    return draw(
        st.dictionaries(
            st.text(alphabet="a-z_", min_size=1, max_size=10),
            st.integers() | st.text() | st.floats(allow_nan=False, allow_infinity=False),
            min_size=0,
            max_size=5,
        )
    )


class TestMessageInvariants:
    """Property-based tests for Message invariants."""

    @given(topic=message_topics(), data=message_data())
    def test_message_creation_always_succeeds(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that Message creation always succeeds with valid inputs."""
        message = Message(topic=topic, data=data)
        assert message is not None

    @given(topic=message_topics(), data=message_data())
    def test_message_stores_topic_unchanged(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that topic is stored exactly as provided."""
        message = Message(topic=topic, data=data)
        assert message.topic == topic

    @given(topic=message_topics(), data=message_data())
    def test_message_stores_data_unchanged(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that data is stored exactly as provided."""
        message = Message(topic=topic, data=data)
        assert message.data == data

    @given(topic=message_topics(), data=message_data())
    def test_message_timestamp_is_recent(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that timestamp is set to recent time (within last 10 seconds)."""
        now_before = datetime.now(timezone.utc)
        message = Message(topic=topic, data=data)
        now_after = datetime.now(timezone.utc)

        # Timestamp should be between before and after creation
        assert now_before <= message.timestamp <= now_after

    @given(
        topic=message_topics(),
        data=message_data(),
        metadata=st.dictionaries(st.text(min_size=1), st.text(), max_size=5),
    )
    def test_message_metadata_matches_provided(
        self,
        topic: Topic,
        data: MessageData,
        metadata: dict[str, Any],
    ) -> None:
        """Test that metadata is stored exactly as provided."""
        message = Message(topic=topic, data=data, metadata=metadata)
        assert message.metadata == metadata

    @given(topic=message_topics(), data=message_data())
    def test_message_metadata_defaults_to_empty_dict(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that metadata defaults to empty dict when not provided."""
        message = Message(topic=topic, data=data)
        assert message.metadata == {}
        assert isinstance(message.metadata, dict)


class TestMessageImmutability:
    """Property-based tests for Message immutability."""

    @given(topic=message_topics(), data=message_data())
    def test_message_is_frozen(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that Message instances are immutable (frozen dataclass)."""
        message = Message(topic=topic, data=data)

        with pytest.raises((AttributeError, TypeError)):
            message.topic = "new.topic"

    @given(topic=message_topics(), data=message_data())
    def test_message_data_cannot_be_modified(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that message data cannot be modified after creation."""
        message = Message(topic=topic, data=data)

        with pytest.raises((AttributeError, TypeError)):
            message.data = "new data"

    @given(topic=message_topics(), data=message_data())
    def test_message_timestamp_cannot_be_modified(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that timestamp cannot be modified after creation."""
        message = Message(topic=topic, data=data)

        with pytest.raises((AttributeError, TypeError)):
            message.timestamp = datetime.now(timezone.utc)


class TestMessageDataHandling:
    """Property-based tests for Message data handling."""

    @given(
        topic=message_topics(),
        data1=message_data(),
        data2=message_data(),
    )
    def test_different_data_creates_different_messages(
        self,
        topic: Topic,
        data1: MessageData,
        data2: MessageData,
    ) -> None:
        """Test that different data creates messages with different data (when data differs)."""
        message1 = Message(topic=topic, data=data1)
        message2 = Message(topic=topic, data=data2)

        # If data differs, messages should have different data
        if data1 != data2:
            assert message1.data != message2.data

    @given(
        topic1=message_topics(),
        topic2=message_topics(),
        data=message_data(),
    )
    def test_different_topics_creates_different_messages(
        self,
        topic1: Topic,
        topic2: Topic,
        data: MessageData,
    ) -> None:
        """Test that different topics are preserved in messages."""
        message1 = Message(topic=topic1, data=data)
        message2 = Message(topic=topic2, data=data)

        # If topics differ, messages should have different topics
        if topic1 != topic2:
            assert message1.topic != message2.topic

    @given(topic=message_topics(), data=message_data())
    def test_message_has_valid_string_representation(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that Message has valid string representation."""
        message = Message(topic=topic, data=data)
        str_repr = str(message)

        # String representation should contain key information
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestMessageTopicValidation:
    """Property-based tests for topic validation and matching."""

    @given(
        segments1=st.lists(st.text(alphabet="a-z0-9", min_size=1), min_size=1, max_size=3),
        segments2=st.lists(st.text(alphabet="a-z0-9", min_size=1), min_size=1, max_size=3),
    )
    def test_topics_with_different_segments_are_different(
        self,
        segments1: list[str],
        segments2: list[str],
    ) -> None:
        """Test that topics with different segment counts are handled correctly."""
        topic1 = Topic(".".join(segments1))
        topic2 = Topic(".".join(segments2))

        message1 = Message(topic=topic1, data={})
        message2 = Message(topic=topic2, data={})

        if len(segments1) != len(segments2):
            assert message1.topic != message2.topic
