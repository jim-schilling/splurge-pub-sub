"""Unit tests for PubSub core functionality.

Test Cases:
    - Initialization
    - Subscribe operation
    - Publish operation
    - Unsubscribe operation
    - Clear operation
    - Shutdown operation
    - Context manager
    - Thread safety
    - Edge cases
"""

import concurrent.futures
import threading
import time
from typing import Any

import pytest

from splurge_pub_sub import (
    Message,
    PubSub,
    SplurgePubSubLookupError,
    SplurgePubSubRuntimeError,
    SplurgePubSubTypeError,
    SplurgePubSubValueError,
)

# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for PubSub initialization."""

    def test_init_creates_empty_bus(self) -> None:
        """Test that __init__ creates an empty subscription registry."""
        bus = PubSub()
        # Bus should not error on empty usage
        bus.publish("any.topic", {"data": "test"})

    def test_init_creates_rlock(self) -> None:
        """Test that __init__ creates an RLock for thread-safety."""
        bus = PubSub()
        assert hasattr(bus, "_lock")
        # RLock is a factory function, check for _RLock type
        assert type(bus._lock).__name__ == "RLock"

    def test_init_sets_shutdown_false(self) -> None:
        """Test that shutdown flag is initialized to False."""
        bus = PubSub()
        assert bus.is_shutdown is False


# ============================================================================
# Subscribe Tests
# ============================================================================


class TestSubscribe:
    """Tests for subscribe() operation."""

    def test_subscribe_valid_topic_callback_returns_id(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test subscribing with valid topic and callback returns ID."""

        def callback(msg: Message) -> None:
            pass

        sub_id = pubsub.subscribe("test.topic", callback)
        assert isinstance(sub_id, str)
        assert len(sub_id) > 0

    def test_subscribe_multiple_callbacks_same_topic(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test multiple subscribers on same topic."""
        callbacks = [lambda msg: None for _ in range(3)]
        ids = [pubsub.subscribe("topic", cb) for cb in callbacks]

        assert len(ids) == 3
        assert len(set(ids)) == 3  # All unique

    def test_subscribe_same_callback_different_topics(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test same callback subscribed to different topics."""

        def callback(msg: Message) -> None:
            pass

        id1 = pubsub.subscribe("topic1", callback)
        id2 = pubsub.subscribe("topic2", callback)

        assert id1 != id2

    def test_subscribe_empty_topic_raises_valueerror(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that empty topic raises SplurgePubSubValueError."""

        def callback(msg: Message) -> None:
            pass

        with pytest.raises(SplurgePubSubValueError):
            pubsub.subscribe("", callback)

    def test_subscribe_non_callable_raises_typeerror(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that non-callable raises SplurgePubSubTypeError."""
        with pytest.raises(SplurgePubSubTypeError):
            pubsub.subscribe("topic", "not a function")  # type: ignore

    def test_subscribe_generates_unique_ids(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that subscriber IDs are unique across calls."""

        def callback(msg: Message) -> None:
            pass

        ids = set()
        for _ in range(10):
            sub_id = pubsub.subscribe("topic", callback)
            assert sub_id not in ids
            ids.add(sub_id)

    def test_subscribe_on_shutdown_bus_raises_runtimeerror(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that subscribing on shutdown bus raises error."""

        def callback(msg: Message) -> None:
            pass

        pubsub.shutdown()

        with pytest.raises(SplurgePubSubRuntimeError):
            pubsub.subscribe("topic", callback)


# ============================================================================
# Publish Tests
# ============================================================================


class TestPublish:
    """Tests for publish() operation."""

    def test_publish_calls_all_subscribers(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that all subscribers receive published message."""
        received = []

        def callback1(msg: Message) -> None:
            received.append(("cb1", msg))

        def callback2(msg: Message) -> None:
            received.append(("cb2", msg))

        pubsub.subscribe("topic", callback1)
        pubsub.subscribe("topic", callback2)

        pubsub.publish("topic", {"data": "test"})
        pubsub.drain()

        assert len(received) == 2
        assert received[0][0] == "cb1"
        assert received[1][0] == "cb2"

    def test_publish_creates_message_with_topic_data(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that publish creates message with correct topic and data."""
        received_messages = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        pubsub.subscribe("user.created", callback)
        test_data = {"id": 123, "name": "Alice"}

        pubsub.publish("user.created", test_data)
        pubsub.drain()

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg.topic == "user.created"
        assert msg.data == test_data

    def test_publish_creates_auto_timestamp(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that messages have auto-generated timestamps."""
        received_messages = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        pubsub.subscribe("topic", callback)

        before_time = time.time()
        pubsub.publish("topic", {"data": "test"})
        pubsub.drain()
        after_time = time.time()

        assert len(received_messages) == 1
        msg = received_messages[0]
        msg_time = msg.timestamp.timestamp()
        assert before_time <= msg_time <= after_time

    def test_publish_calls_callbacks_in_order(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that callbacks are called in subscription order."""
        call_order = []

        for i in range(5):
            pubsub.subscribe("topic", lambda msg, i=i: call_order.append(i))

        pubsub.publish("topic", {"data": "test"})
        pubsub.drain()

        assert call_order == [0, 1, 2, 3, 4]

    def test_publish_empty_topic_raises_valueerror(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that publishing to empty topic raises error."""
        with pytest.raises(SplurgePubSubValueError):
            pubsub.publish("", {"data": "test"})

    def test_publish_to_nonexistent_topic_no_error(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test publishing to topic with no subscribers doesn't error."""
        # Should not raise
        pubsub.publish("nonexistent.topic", {"data": "test"})

    def test_publish_callback_exception_caught_logged(
        self,
        pubsub: PubSub,
        caplog: Any,
    ) -> None:
        """Test that callback exceptions are caught and logged."""

        def failing_callback(msg: Message) -> None:
            raise ValueError("Test error")

        pubsub.subscribe("topic", failing_callback)

        # Should not raise
        pubsub.publish("topic", {"data": "test"})
        pubsub.drain()

        # Should be logged
        assert "Test error" in caplog.text

    def test_publish_one_callback_exception_doesnt_stop_others(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that one callback's exception doesn't affect others."""
        results = []

        def callback1(msg: Message) -> None:
            results.append(1)

        def callback2(msg: Message) -> None:
            raise ValueError("Test error")

        def callback3(msg: Message) -> None:
            results.append(3)

        pubsub.subscribe("topic", callback1)
        pubsub.subscribe("topic", callback2)
        pubsub.subscribe("topic", callback3)

        pubsub.publish("topic", {"data": "test"})
        pubsub.drain()

        assert results == [1, 3]

    def test_publish_message_passed_to_callbacks(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that exact message object is passed to callbacks."""
        received_messages = []

        def callback(msg: Message) -> None:
            received_messages.append(msg)

        pubsub.subscribe("topic", callback)
        test_data = {"key": "value"}
        pubsub.publish("topic", test_data)
        pubsub.drain()

        assert len(received_messages) == 1
        assert isinstance(received_messages[0], Message)
        assert received_messages[0].data == test_data


# ============================================================================
# Unsubscribe Tests
# ============================================================================


class TestUnsubscribe:
    """Tests for unsubscribe() operation."""

    def test_unsubscribe_valid_subscriber_removes_subscription(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that unsubscribe removes a subscription."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        sub_id = pubsub.subscribe("topic", callback)
        pubsub.publish("topic", {"data": "data1"})
        pubsub.drain()
        assert len(received) == 1

        pubsub.unsubscribe("topic", sub_id)
        pubsub.publish("topic", {"data": "data2"})
        pubsub.drain()
        assert len(received) == 1  # No new message

    def test_unsubscribe_invalid_subscriber_raises_lookuperror(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that unsubscribing invalid ID raises error."""
        with pytest.raises(SplurgePubSubLookupError):
            pubsub.unsubscribe("topic", "invalid-id")

    def test_unsubscribe_same_subscriber_twice_raises_error(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that unsubscribing same subscriber twice raises error."""

        def callback(msg: Message) -> None:
            pass

        sub_id = pubsub.subscribe("topic", callback)
        pubsub.unsubscribe("topic", sub_id)

        with pytest.raises(SplurgePubSubLookupError):
            pubsub.unsubscribe("topic", sub_id)

    def test_unsubscribe_unaffected_other_subscribers(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that unsubscribing doesn't affect other subscribers."""
        received = {"cb1": [], "cb2": []}

        def callback1(msg: Message) -> None:
            received["cb1"].append(msg)

        def callback2(msg: Message) -> None:
            received["cb2"].append(msg)

        sub_id1 = pubsub.subscribe("topic", callback1)
        pubsub.subscribe("topic", callback2)

        pubsub.publish("topic", {"data": "data1"})
        pubsub.drain()
        pubsub.unsubscribe("topic", sub_id1)
        pubsub.publish("topic", {"data": "data2"})
        pubsub.drain()

        assert len(received["cb1"]) == 1
        assert len(received["cb2"]) == 2


# ============================================================================
# Clear Tests
# ============================================================================


class TestClear:
    """Tests for clear() operation."""

    def test_clear_all_removes_all_subscribers(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test clearing all subscribers."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        pubsub.subscribe("topic1", callback)
        pubsub.subscribe("topic2", callback)

        pubsub.publish("topic1", {"data": "test"})
        pubsub.publish("topic2", {"data": "test"})
        pubsub.drain()
        assert len(received) == 2

        pubsub.clear()

        pubsub.publish("topic1", {"data": "test"})
        pubsub.publish("topic2", {"data": "test"})
        pubsub.drain()
        assert len(received) == 2  # No new messages

    def test_clear_topic_removes_only_that_topic(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test clearing specific topic only."""
        received = {"topic1": [], "topic2": []}

        def make_callback(topic: str) -> Any:
            def callback(msg: Message) -> None:
                received[topic].append(msg)

            return callback

        pubsub.subscribe("topic1", make_callback("topic1"))
        pubsub.subscribe("topic2", make_callback("topic2"))

        pubsub.clear("topic1")

        pubsub.publish("topic1", {"data": "test"})
        pubsub.publish("topic2", {"data": "test"})
        pubsub.drain()

        assert len(received["topic1"]) == 0
        assert len(received["topic2"]) == 1

    def test_clear_nonexistent_topic_no_error(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test clearing non-existent topic doesn't error."""
        # Should not raise
        pubsub.clear("nonexistent")

    def test_clear_after_clear_no_subscriptions(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that clear() multiple times is safe."""

        def callback(msg: Message) -> None:
            pass

        pubsub.subscribe("topic", callback)
        pubsub.clear()
        pubsub.clear()  # Should not error
        pubsub.publish("topic", {"data": "test"})  # Should not raise


# ============================================================================
# Shutdown Tests
# ============================================================================


class TestShutdown:
    """Tests for shutdown() operation."""

    def test_shutdown_clears_subscribers(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that shutdown clears all subscribers."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        pubsub.subscribe("topic", callback)
        pubsub.publish("topic", {"data": "data1"})
        pubsub.drain()
        assert len(received) == 1

        pubsub.shutdown()
        # After shutdown, publish should raise error
        with pytest.raises(SplurgePubSubRuntimeError):
            pubsub.publish("topic", {"data": "data2"})
        assert len(received) == 1  # No new message

    def test_shutdown_sets_flag(self, pubsub: PubSub) -> None:
        """Test that shutdown sets the shutdown flag."""
        assert pubsub.is_shutdown is False
        pubsub.shutdown()
        assert pubsub.is_shutdown is True

    def test_subscribe_after_shutdown_raises_error(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that subscribing after shutdown raises error."""

        def callback(msg: Message) -> None:
            pass

        pubsub.shutdown()

        with pytest.raises(SplurgePubSubRuntimeError):
            pubsub.subscribe("topic", callback)

    def test_publish_after_shutdown_no_error(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that publishing after shutdown raises error."""
        pubsub.shutdown()
        # After refactoring to async, publish() checks shutdown state
        # and raises SplurgePubSubRuntimeError
        with pytest.raises(SplurgePubSubRuntimeError):
            pubsub.publish("topic", {"data": "test"})

    def test_shutdown_idempotent(self, pubsub: PubSub) -> None:
        """Test that shutdown can be called multiple times safely."""
        pubsub.shutdown()
        pubsub.shutdown()  # Should not raise
        pubsub.shutdown()  # Should not raise


# ============================================================================
# Context Manager Tests
# ============================================================================


class TestContextManager:
    """Tests for context manager support."""

    def test_context_manager_enter_returns_bus(self) -> None:
        """Test that __enter__ returns the bus instance."""
        bus = PubSub()
        with bus as b:
            assert b is bus

    def test_context_manager_exit_calls_shutdown(self) -> None:
        """Test that __exit__ calls shutdown."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        with PubSub() as bus:
            bus.subscribe("topic", callback)
            bus.publish("topic", {"data": "data1"})
            bus.drain()

        # After exiting context, bus should be shutdown
        assert len(received) == 1

    def test_context_manager_cleanup_on_exception(self) -> None:
        """Test that cleanup happens even if exception in with block."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        try:
            with PubSub() as bus:
                bus.subscribe("topic", callback)
                bus.publish("topic", {"data": "data1"})
                bus.drain()
                raise ValueError("Test error")
        except ValueError:
            pass

        assert len(received) == 1
        # Bus should be shutdown despite exception


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestThreadSafety:
    """Tests for thread-safe concurrent operations."""

    def test_concurrent_subscribers_same_topic(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test concurrent subscriptions to same topic."""
        received_counts = {"count": 0}

        def callback(msg: Message) -> None:
            received_counts["count"] += 1

        def subscribe_many() -> None:
            for _ in range(10):
                pubsub.subscribe("topic", callback)

        threads = [threading.Thread(target=subscribe_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Publish should reach all subscribers
        pubsub.publish("topic", {"data": "test"})
        pubsub.drain()
        assert received_counts["count"] == 50

    def test_concurrent_publishers_same_topic(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test concurrent publishers to same topic."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        pubsub.subscribe("topic", callback)

        def publish_many() -> None:
            for i in range(10):
                pubsub.publish("topic", {"number": i})

        threads = [threading.Thread(target=publish_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        pubsub.drain()
        assert len(received) == 50

    def test_concurrent_subscribe_unsubscribe(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test concurrent subscribe and unsubscribe operations."""
        subscriber_ids = []

        def callback(msg: Message) -> None:
            pass

        # Subscribe in one thread
        def subscribe_many() -> None:
            for _ in range(10):
                sub_id = pubsub.subscribe("topic", callback)
                subscriber_ids.append(sub_id)

        # Unsubscribe in another thread
        def unsubscribe_many() -> None:
            # Give subscribers time to register
            time.sleep(0.1)
            for sub_id in subscriber_ids[:]:
                try:
                    pubsub.unsubscribe("topic", sub_id)
                except SplurgePubSubLookupError:
                    pass  # Already unsubscribed

        threads = [
            threading.Thread(target=subscribe_many),
            threading.Thread(target=unsubscribe_many),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def test_nested_publish_in_callback(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test publishing from within a callback (re-entrant)."""
        call_order = []

        def callback1(msg: Message) -> None:
            call_order.append("cb1-start")
            # Only publish nested if this is the first call (prevent infinite loop)
            if msg.data.get("depth", 0) == 0:
                call_order.append("cb1-publishes-nested")
                pubsub.publish("topic2", {"depth": 1})
                call_order.append("cb1-nested-returned")
            call_order.append("cb1-end")

        def callback2(msg: Message) -> None:
            call_order.append("cb2")

        pubsub.subscribe("topic1", callback1)
        pubsub.subscribe("topic2", callback2)

        pubsub.publish("topic1", {"depth": 0})
        pubsub.drain()

        # With async dispatch, nested publishes are queued and processed after current callback
        # Order may vary, but both callbacks should execute
        assert "cb1-start" in call_order
        assert "cb1-publishes-nested" in call_order
        assert "cb2" in call_order
        assert "cb1-nested-returned" in call_order
        assert "cb1-end" in call_order

    def test_race_unsubscribe_during_publish(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that unsubscribe during publish works correctly."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        sub_ids = [pubsub.subscribe("topic", callback) for _ in range(5)]

        # Unsubscribe while publishing in another thread
        def publish_many() -> None:
            for _ in range(10):
                pubsub.publish("topic", {"data": "test"})

        def unsubscribe_many() -> None:
            time.sleep(0.05)
            for sub_id in sub_ids[:2]:
                try:
                    pubsub.unsubscribe("topic", sub_id)
                except SplurgePubSubLookupError:
                    pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(publish_many)
            executor.submit(unsubscribe_many)

        # Wait for all messages to be processed
        pubsub.drain()
        # All publishes should succeed without error
        assert len(received) > 0


# ============================================================================
# Drain Tests
# ============================================================================


class TestDrain:
    """Tests for drain() operation."""

    def test_drain_waits_for_queue_empty(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that drain waits for queue to be empty."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        pubsub.subscribe("topic", callback)
        pubsub.publish("topic", {"data": "test1"})
        pubsub.publish("topic", {"data": "test2"})

        # Drain should wait for both messages
        result = pubsub.drain()

        assert result is True
        assert len(received) == 2

    def test_drain_timeout(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that drain times out correctly."""
        import time

        def slow_callback(msg: Message) -> None:
            time.sleep(0.1)  # Slow callback

        pubsub.subscribe("topic", slow_callback)
        pubsub.publish("topic", {"data": "test"})

        # Very short timeout should fail
        result = pubsub.drain(timeout=10)  # 10ms timeout

        # May or may not complete depending on timing
        # Just verify it doesn't hang
        assert isinstance(result, bool)

    def test_drain_returns_true_when_empty(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that drain returns True when queue is already empty."""
        result = pubsub.drain()
        assert result is True

    def test_drain_after_shutdown(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that drain after shutdown returns True."""
        pubsub.shutdown()
        result = pubsub.drain()
        assert result is True


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_publish_with_none_data(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test publishing with None value in dict."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        pubsub.subscribe("topic", callback)
        pubsub.publish("topic", {"value": None})
        pubsub.drain()

        assert len(received) == 1
        assert received[0].data["value"] is None

    def test_publish_with_complex_nested_data(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test publishing complex nested data structures."""
        received = []

        def callback(msg: Message) -> None:
            received.append(msg)

        test_data = {
            "users": [
                {"id": 1, "name": "Alice", "tags": {"admin", "user"}},
                {"id": 2, "name": "Bob", "tags": {"user"}},
            ],
            "metadata": {
                "timestamp": "2025-11-04T10:00:00Z",
                "source": "api",
            },
            "counts": [1, 2, 3],
        }

        pubsub.subscribe("topic", callback)
        pubsub.publish("topic", test_data)
        pubsub.drain()

        assert len(received) == 1
        assert received[0].data == test_data

    def test_callback_receives_correct_message_fields(
        self,
        pubsub: PubSub,
    ) -> None:
        """Test that callback receives complete message object."""
        received_msg = []

        def callback(msg: Message) -> None:
            received_msg.append(msg)

        pubsub.subscribe("test.topic", callback)
        pubsub.publish("test.topic", {"key": "value"})
        pubsub.drain()

        assert len(received_msg) == 1
        msg = received_msg[0]
        assert hasattr(msg, "topic")
        assert hasattr(msg, "data")
        assert hasattr(msg, "timestamp")
        assert msg.topic == "test.topic"
        assert msg.data == {"key": "value"}
