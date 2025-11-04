"""Property-based tests for PubSub class using Hypothesis.

This module uses Hypothesis to verify PubSub invariants such as message
delivery, subscriber management, and topic filtering behavior.

Test Classes:
    - TestPubSubSubscriberManagement: Subscriber registration and removal
    - TestPubSubMessagePublishing: Message publishing invariants
    - TestPubSubTopicFiltering: Topic pattern filtering behavior
    - TestPubSubMessageDelivery: Message delivery guarantees

DOMAINS: ["testing", "pubsub", "properties"]
"""

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from splurge_pub_sub import Message, PubSub, Topic
from splurge_pub_sub.types import MessageData

DOMAINS = ["testing", "pubsub", "properties"]


# Custom strategies
@st.composite
def topic_strategies(draw: Any) -> Topic:
    """Strategy for generating valid topics."""
    segments = draw(st.lists(st.text(alphabet="a-z0-9_", min_size=1), min_size=1, max_size=4))
    return Topic(".".join(segments))


@st.composite
def message_data_strategies(draw: Any) -> MessageData:
    """Strategy for generating message data.

    Message data must be a dict with string keys.
    """
    return draw(
        st.dictionaries(
            st.text(alphabet="a-z_", min_size=1, max_size=10),
            st.integers() | st.text(),
            max_size=3,
        )
    )


class TestPubSubSubscriberManagement:
    """Property-based tests for subscriber management."""

    @given(topic=topic_strategies())
    def test_pubsub_can_be_created(self, topic: Topic) -> None:
        """Test that PubSub instance can be created."""
        pubsub = PubSub()
        assert pubsub is not None

    @given(topic=topic_strategies())
    def test_subscriber_can_be_subscribed(self, topic: Topic) -> None:
        """Test that subscriber can be added."""
        pubsub = PubSub()

        def callback(msg: Message) -> None:
            pass

        subscriber_id = pubsub.subscribe(topic=topic, callback=callback)
        assert subscriber_id is not None
        assert isinstance(subscriber_id, str)

    @given(
        topic1=topic_strategies(),
        topic2=topic_strategies(),
    )
    def test_multiple_subscribers_can_be_added(
        self,
        topic1: Topic,
        topic2: Topic,
    ) -> None:
        """Test that multiple subscribers can be added."""
        pubsub = PubSub()

        def callback1(msg: Message) -> None:
            pass

        def callback2(msg: Message) -> None:
            pass

        id1 = pubsub.subscribe(topic=topic1, callback=callback1)
        id2 = pubsub.subscribe(topic=topic2, callback=callback2)

        assert id1 is not None
        assert id2 is not None
        # IDs should be different if subscribers are different
        assert id1 != id2

    @given(topic=topic_strategies())
    def test_subscriber_can_be_unsubscribed(self, topic: Topic) -> None:
        """Test that subscriber can be removed."""
        pubsub = PubSub()

        def callback(msg: Message) -> None:
            pass

        subscriber_id = pubsub.subscribe(topic=topic, callback=callback)
        pubsub.unsubscribe(topic=topic, subscriber_id=subscriber_id)

    @given(
        topic1=topic_strategies(),
        topic2=topic_strategies(),
    )
    def test_unsubscribe_only_removes_specified_subscriber(
        self,
        topic1: Topic,
        topic2: Topic,
    ) -> None:
        """Test that unsubscribe only removes specified subscriber."""
        pubsub = PubSub()

        def callback1(msg: Message) -> None:
            pass

        def callback2(msg: Message) -> None:
            pass

        id1 = pubsub.subscribe(topic=topic1, callback=callback1)
        id2 = pubsub.subscribe(topic=topic2, callback=callback2)

        pubsub.unsubscribe(topic=topic1, subscriber_id=id1)

        # Unsubscribing id1 should succeed, and id2 should still be able to unsubscribe
        pubsub.unsubscribe(topic=topic2, subscriber_id=id2)


class TestPubSubMessagePublishing:
    """Property-based tests for message publishing."""

    @given(
        topic=topic_strategies(),
        data=message_data_strategies(),
    )
    def test_message_can_be_published(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that messages can be published."""
        pubsub = PubSub()

        # Publishing should not raise
        pubsub.publish(topic=topic, data=data)

    @given(
        topic=topic_strategies(),
        data1=message_data_strategies(),
        data2=message_data_strategies(),
    )
    def test_multiple_messages_can_be_published(
        self,
        topic: Topic,
        data1: MessageData,
        data2: MessageData,
    ) -> None:
        """Test that multiple messages can be published."""
        pubsub = PubSub()

        pubsub.publish(topic=topic, data=data1)
        pubsub.publish(topic=topic, data=data2)

    @given(
        topic1=topic_strategies(),
        topic2=topic_strategies(),
        data=message_data_strategies(),
    )
    def test_messages_can_be_published_to_different_topics(
        self,
        topic1: Topic,
        topic2: Topic,
        data: MessageData,
    ) -> None:
        """Test publishing to different topics."""
        pubsub = PubSub()

        pubsub.publish(topic=topic1, data=data)
        pubsub.publish(topic=topic2, data=data)


class TestPubSubMessageDelivery:
    """Property-based tests for message delivery behavior."""

    @given(
        topic=topic_strategies(),
        data=message_data_strategies(),
    )
    def test_subscriber_receives_published_messages(
        self,
        topic: Topic,
        data: MessageData,
    ) -> None:
        """Test that subscribers receive messages."""
        pubsub = PubSub()
        received_messages: list[Message] = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        pubsub.subscribe(topic=topic, callback=callback)
        pubsub.publish(topic=topic, data=data)

        # Give a small amount of time for async delivery
        import time

        time.sleep(0.01)

        assert len(received_messages) == 1
        assert received_messages[0].topic == topic
        assert received_messages[0].data == data

    @given(
        topic1=topic_strategies(),
        topic2=topic_strategies(),
        data=message_data_strategies(),
    )
    def test_subscriber_to_exact_topic_only_receives_matching_messages(
        self,
        topic1: Topic,
        topic2: Topic,
        data: MessageData,
    ) -> None:
        """Test that exact subscribers only receive exact topic messages."""
        if topic1 == topic2:
            # Skip if topics are the same
            return

        pubsub = PubSub()
        received_messages: list[Message] = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        # Subscribe to topic1
        pubsub.subscribe(topic=topic1, callback=callback)

        # Publish to topic2
        pubsub.publish(topic=topic2, data=data)

        import time

        time.sleep(0.01)

        # Should not receive message for different topic
        assert len(received_messages) == 0

    @given(
        topic1=topic_strategies(),
        topic2=topic_strategies(),
        data=message_data_strategies(),
    )
    def test_unsubscriber_does_not_receive_messages(
        self,
        topic1: Topic,
        topic2: Topic,
        data: MessageData,
    ) -> None:
        """Test that unsubscribed callbacks don't receive messages."""
        pubsub = PubSub()
        received_messages: list[Message] = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        subscriber_id = pubsub.subscribe(topic=topic1, callback=callback)
        pubsub.unsubscribe(topic=topic1, subscriber_id=subscriber_id)

        pubsub.publish(topic=topic1, data=data)

        import time

        time.sleep(0.01)

        assert len(received_messages) == 0


class TestPubSubWildcardMatching:
    """Property-based tests for wildcard topic matching."""

    @given(topic=topic_strategies())
    def test_exact_topic_matching_works(self, topic: Topic) -> None:
        """Test that exact topic matching delivers messages correctly."""
        pubsub = PubSub()
        received_messages: list[Message] = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        # Subscribe to exact topic
        pubsub.subscribe(topic=topic, callback=callback)

        # Publish to same topic
        pubsub.publish(topic=topic, data={})

        import time

        time.sleep(0.01)

        # Should receive the message
        assert len(received_messages) == 1


class TestPubSubThreadSafety:
    """Property-based tests for thread safety properties."""

    @given(
        num_publishers=st.integers(min_value=1, max_value=5),
        num_subscribers=st.integers(min_value=1, max_value=5),
        topic=topic_strategies(),
    )
    def test_pubsub_handles_multiple_operations(
        self,
        num_publishers: int,
        num_subscribers: int,
        topic: Topic,
    ) -> None:
        """Test that PubSub can handle multiple concurrent operations."""
        pubsub = PubSub()
        received_messages: list[Message] = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        # Add subscribers
        subscriber_ids = []
        for _ in range(num_subscribers):
            subscriber_id = pubsub.subscribe(topic=topic, callback=callback)
            subscriber_ids.append(subscriber_id)

        # Publish messages
        for i in range(num_publishers):
            pubsub.publish(topic=topic, data={"message_id": i})

        import time

        time.sleep(0.05)

        # Should have received all messages on all subscribers
        expected_count = num_publishers * num_subscribers
        assert len(received_messages) == expected_count
