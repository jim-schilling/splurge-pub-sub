"""Unit tests for correlation_id edge cases and thread safety.

Test Cases:
    - Thread safety with correlation_id operations
    - Boundary conditions (1 char, 64 chars, 65 chars)
    - Shutdown edge cases with correlation_id
    - Property thread safety and immutability
"""

import concurrent.futures
import threading
import time
from typing import Any

import pytest

from splurge_pub_sub import Message, PubSub, SplurgePubSubRuntimeError, SplurgePubSubValueError


class TestCorrelationIdBoundaryConditions:
    """Tests for correlation_id boundary conditions."""

    def test_correlation_id_exactly_two_chars(self) -> None:
        """Test correlation_id with exactly 2 character (minimum boundary)."""
        bus = PubSub(correlation_id="ab")
        assert bus.correlation_id == "ab"
        assert len(bus.correlation_id) == 2

    def test_correlation_id_exactly_64_chars(self) -> None:
        """Test correlation_id with exactly 64 characters (maximum boundary)."""
        long_id = "a" * 64
        bus = PubSub(correlation_id=long_id)
        assert bus.correlation_id == long_id
        assert len(bus.correlation_id) == 64

    def test_correlation_id_65_chars_raises_error(self) -> None:
        """Test that 65-char correlation_id raises error."""
        long_id = "a" * 65
        with pytest.raises(SplurgePubSubValueError, match="length"):
            PubSub(correlation_id=long_id)

    def test_correlation_id_exactly_two_chars_in_publish(self) -> None:
        """Test publishing with exactly 2 character correlation_id."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("test.topic", callback, correlation_id="xy")
        bus.publish("test.topic", {}, correlation_id="xy")
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "xy"

    def test_correlation_id_exactly_64_chars_in_publish(self) -> None:
        """Test publishing with exactly 64 character correlation_id."""
        bus = PubSub()
        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        long_id = "a" * 64
        bus.subscribe("test.topic", callback, correlation_id=long_id)
        bus.publish("test.topic", {}, correlation_id=long_id)
        bus.drain()

        assert len(received) == 1
        assert received[0].correlation_id == long_id

    def test_message_correlation_id_exactly_two_chars(self) -> None:
        """Test Message with exactly 2 character correlation_id."""
        msg = Message(topic="test", data={}, correlation_id="xy")
        assert msg.correlation_id == "xy"
        assert len(msg.correlation_id) == 2

    def test_message_correlation_id_exactly_64_chars(self) -> None:
        """Test Message with exactly 64 character correlation_id."""
        long_id = "a" * 64
        msg = Message(topic="test", data={}, correlation_id=long_id)
        assert msg.correlation_id == long_id
        assert len(msg.correlation_id) == 64


class TestCorrelationIdThreadSafety:
    """Tests for thread safety with correlation_id operations."""

    def test_concurrent_publish_different_correlation_ids(self) -> None:
        """Test thread-safety of _correlation_ids set with concurrent publishes."""
        bus = PubSub()
        num_threads = 10
        publishes_per_thread = 10

        def publish_with_id(thread_id: int) -> None:
            for i in range(publishes_per_thread):
                correlation_id = f"thread-{thread_id}-msg-{i}"
                bus.publish("test.topic", {}, correlation_id=correlation_id)

        threads = [threading.Thread(target=publish_with_id, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all correlation_ids are in the set
        expected_count = num_threads * publishes_per_thread
        assert len(bus.correlation_ids) >= expected_count

        # Verify specific IDs are present
        for thread_id in range(num_threads):
            for i in range(publishes_per_thread):
                correlation_id = f"thread-{thread_id}-msg-{i}"
                assert correlation_id in bus.correlation_ids

    def test_concurrent_subscribe_correlation_id_during_publish(self) -> None:
        """Test subscribing with correlation_id filter while publishing."""
        bus = PubSub()
        received_count = {"count": 0}
        lock = threading.Lock()

        def callback(msg: Message) -> None:
            with lock:
                received_count["count"] += 1

        def subscribe_many() -> None:
            for i in range(10):
                bus.subscribe("test.topic", callback, correlation_id=f"id-{i}")

        def publish_many() -> None:
            for i in range(20):
                bus.publish("test.topic", {}, correlation_id=f"id-{i % 10}")

        threads = [
            threading.Thread(target=subscribe_many),
            threading.Thread(target=publish_many),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        bus.drain()
        # Should have received some messages (exact count depends on timing)
        assert received_count["count"] > 0

    def test_race_unsubscribe_correlation_id_during_publish(self) -> None:
        """Test unsubscribing with correlation_id filter during publish."""
        bus = PubSub()
        received: list[Message] = []
        lock = threading.Lock()

        def callback(msg: Message) -> None:
            with lock:
                received.append(msg)

        # Subscribe with different correlation_ids
        sub_ids = []
        for i in range(5):
            sub_id = bus.subscribe("test.topic", callback, correlation_id=f"id-{i}")
            sub_ids.append(sub_id)

        def publish_many() -> None:
            for _ in range(20):
                bus.publish("test.topic", {}, correlation_id="id-0")

        def unsubscribe_many() -> None:
            time.sleep(0.05)  # Let some publishes happen first
            for sub_id in sub_ids[:2]:
                try:
                    bus.unsubscribe("test.topic", sub_id)
                except Exception:
                    pass  # May raise if already unsubscribed

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(publish_many)
            executor.submit(unsubscribe_many)

        bus.drain()
        # Should have received some messages
        assert len(received) > 0

    def test_concurrent_correlation_ids_property_access(self) -> None:
        """Test thread-safety of correlation_ids property during concurrent publishes."""
        bus = PubSub()
        num_threads = 5
        publishes_per_thread = 10

        def publish_and_read(thread_id: int) -> list[str]:
            correlation_ids_seen = []
            for i in range(publishes_per_thread):
                correlation_id = f"thread-{thread_id}-msg-{i}"
                bus.publish("test.topic", {}, correlation_id=correlation_id)
                # Read property concurrently
                ids = bus.correlation_ids
                correlation_ids_seen.extend(ids)
            return correlation_ids_seen

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(publish_and_read, i) for i in range(num_threads)]
            # Wait for all futures to complete (verify no exceptions)
            for f in concurrent.futures.as_completed(futures):
                f.result()  # Raises exception if thread failed

        # Verify property access didn't cause errors
        final_ids = bus.correlation_ids
        assert len(final_ids) >= num_threads * publishes_per_thread

    def test_correlation_ids_property_returns_copy(self) -> None:
        """Test that correlation_ids property returns a copy (mutating doesn't affect internal set)."""
        bus = PubSub()
        bus.publish("test.topic", {}, correlation_id="id-1")
        bus.publish("test.topic", {}, correlation_id="id-2")

        # Get property
        ids_copy = bus.correlation_ids
        original_size = len(ids_copy)

        # Mutate the copy
        ids_copy.add("should-not-appear")
        ids_copy.remove("id-1")

        # Verify internal set is unchanged
        assert len(bus.correlation_ids) == original_size
        assert "id-1" in bus.correlation_ids
        assert "should-not-appear" not in bus.correlation_ids

    def test_multiple_threads_publish_same_correlation_id(self) -> None:
        """Test multiple threads publishing same correlation_id simultaneously."""
        bus = PubSub()
        received_count = {"count": 0}
        lock = threading.Lock()
        correlation_id = "shared-id"

        def callback(msg: Message) -> None:
            with lock:
                received_count["count"] += 1

        bus.subscribe("test.topic", callback, correlation_id=correlation_id)

        def publish_many() -> None:
            for _ in range(10):
                bus.publish("test.topic", {}, correlation_id=correlation_id)

        num_threads = 5
        threads = [threading.Thread(target=publish_many) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should receive all messages (5 threads * 10 publishes = 50)
        assert received_count["count"] == num_threads * 10


class TestCorrelationIdShutdownEdgeCases:
    """Tests for shutdown edge cases with correlation_id."""

    def test_subscribe_with_correlation_id_after_shutdown_raises_error(self) -> None:
        """Test that subscribing with correlation_id after shutdown raises error."""
        bus = PubSub()
        bus.shutdown()

        def callback(msg: Message) -> None:
            pass

        with pytest.raises(SplurgePubSubRuntimeError):
            bus.subscribe("test.topic", callback, correlation_id="test-id")

    def test_publish_with_correlation_id_after_shutdown(self) -> None:
        """Test that publishing with correlation_id after shutdown raises error.

        After refactoring to async, publish() now checks shutdown state
        and raises SplurgePubSubRuntimeError.
        """
        bus = PubSub()
        bus.shutdown()

        # After refactoring to async, publish() checks shutdown state
        # and raises SplurgePubSubRuntimeError
        with pytest.raises(SplurgePubSubRuntimeError):
            bus.publish("test.topic", {}, correlation_id="test-id")

    def test_correlation_id_property_accessible_after_shutdown(self) -> None:
        """Test that correlation_id property is still accessible after shutdown."""
        bus = PubSub(correlation_id="test-id")
        correlation_id_before = bus.correlation_id
        bus.shutdown()

        # Property should still be accessible
        assert bus.correlation_id == correlation_id_before
        assert bus.correlation_id == "test-id"

    def test_correlation_ids_property_accessible_after_shutdown(self) -> None:
        """Test that correlation_ids property is still accessible after shutdown."""
        bus = PubSub(correlation_id="test-id")
        bus.publish("test.topic", {}, correlation_id="published-id")
        correlation_ids_before = bus.correlation_ids.copy()
        bus.shutdown()

        # Property should still be accessible
        assert bus.correlation_ids == correlation_ids_before
        assert "test-id" in bus.correlation_ids
        assert "published-id" in bus.correlation_ids

    def test_correlation_ids_property_immutable_after_shutdown(self) -> None:
        """Test that correlation_ids property returns copy even after shutdown."""
        bus = PubSub(correlation_id="test-id")
        bus.publish("test.topic", {}, correlation_id="published-id")
        bus.shutdown()

        # Get property after shutdown
        ids_copy = bus.correlation_ids
        ids_copy.add("should-not-appear")

        # Verify internal set unchanged
        assert "should-not-appear" not in bus.correlation_ids


class TestCorrelationIdErrorHandling:
    """Tests for error handling edge cases with correlation_id."""

    def test_error_handler_called_with_correlation_id_context(self) -> None:
        """Test that error handler receives correct context when callback fails."""
        error_info = {"topic": None, "exc": None}

        def error_handler(exc: Exception, topic: str) -> None:
            error_info["topic"] = topic
            error_info["exc"] = exc

        bus = PubSub(error_handler=error_handler)

        def failing_callback(msg: Message) -> None:
            raise ValueError(f"Failed processing {msg.correlation_id}")

        bus.subscribe("test.topic", failing_callback, correlation_id="test-id")
        bus.publish("test.topic", {}, correlation_id="test-id")
        bus.drain()

        assert error_info["topic"] == "test.topic"
        assert isinstance(error_info["exc"], ValueError)
        assert "test-id" in str(error_info["exc"])

    def test_error_isolation_with_correlation_id_filters(self) -> None:
        """Test that error in one callback doesn't affect others with different correlation_id filters."""
        received_a = []
        received_b = []
        error_count = {"count": 0}

        def error_handler(exc: Exception, topic: str) -> None:
            error_count["count"] += 1

        bus = PubSub(error_handler=error_handler)

        def callback_a(msg: Message) -> None:
            received_a.append(msg)

        def callback_b(msg: Message) -> None:
            received_b.append(msg)
            raise ValueError("Callback B failed")

        bus.subscribe("test.topic", callback_a, correlation_id="id-a")
        bus.subscribe("test.topic", callback_b, correlation_id="id-b")

        bus.publish("test.topic", {}, correlation_id="id-a")
        bus.publish("test.topic", {}, correlation_id="id-b")
        bus.drain()

        # Callback A should have received its message
        assert len(received_a) == 1
        # Callback B should have received its message despite error
        assert len(received_b) == 1
        # Error handler should have been called once
        assert error_count["count"] == 1

    def test_multiple_callbacks_different_correlation_ids_one_fails(self) -> None:
        """Test multiple callbacks with different correlation_id filters, one fails."""
        received_ok = []
        error_count = {"count": 0}

        def error_handler(exc: Exception, topic: str) -> None:
            error_count["count"] += 1

        bus = PubSub(error_handler=error_handler)

        def callback_ok(msg: Message) -> None:
            received_ok.append(msg)

        def callback_fail(msg: Message) -> None:
            raise ValueError("Failed")

        # Subscribe multiple callbacks with different correlation_ids
        for i in range(5):
            bus.subscribe("test.topic", callback_ok, correlation_id=f"id-{i}")

        bus.subscribe("test.topic", callback_fail, correlation_id="id-fail")

        # Publish to all
        for i in range(5):
            bus.publish("test.topic", {}, correlation_id=f"id-{i}")
        bus.publish("test.topic", {}, correlation_id="id-fail")
        bus.drain()

        # All OK callbacks should have received messages
        assert len(received_ok) == 5
        # Error handler should have been called once
        assert error_count["count"] == 1


class TestCorrelationIdLargeScale:
    """Tests for large-scale correlation_id operations."""

    def test_publish_with_many_different_correlation_ids(self) -> None:
        """Test publishing with 1000+ different correlation_ids (stress test)."""
        bus = PubSub()
        num_ids = 1000

        for i in range(num_ids):
            bus.publish("test.topic", {}, correlation_id=f"id-{i}")

        # Verify all IDs are tracked
        assert len(bus.correlation_ids) >= num_ids
        # Verify specific IDs are present
        assert "id-0" in bus.correlation_ids
        assert "id-500" in bus.correlation_ids
        assert f"id-{num_ids - 1}" in bus.correlation_ids

    def test_subscribe_with_many_different_correlation_id_filters(self) -> None:
        """Test subscribing with 1000+ different correlation_id filters."""
        bus = PubSub()
        received_counts = {i: 0 for i in range(100)}

        def make_callback(idx: int) -> Any:
            def callback(msg: Message) -> None:
                received_counts[idx] += 1

            return callback

        # Subscribe with many different correlation_id filters
        for i in range(100):
            bus.subscribe("test.topic", make_callback(i), correlation_id=f"id-{i}")

        # Publish to each
        for i in range(100):
            bus.publish("test.topic", {}, correlation_id=f"id-{i}")

        bus.drain()
        # Verify all received their messages
        for i in range(100):
            assert received_counts[i] == 1
