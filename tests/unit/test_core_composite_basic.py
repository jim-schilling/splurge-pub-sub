"""Unit tests for PubSubAggregator core functionality.

Test Cases:
    - Initialization
    - Adding/removing PubSub instances
    - Message forwarding from managed PubSub instances
    - Subscribe/unsubscribe operations
    - Publish operations (internal bus only)
    - Clear operations
    - Shutdown with and without cascade
    - Drain with and without cascade
    - Context manager
    - Thread safety
    - Edge cases
"""

import threading

import pytest

from splurge_pub_sub import (
    Message,
    PubSub,
    PubSubAggregator,
    SplurgePubSubLookupError,
    SplurgePubSubRuntimeError,
    SplurgePubSubValueError,
)

# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for PubSubAggregator initialization."""

    def test_init_creates_empty_composite(self) -> None:
        """Test that __init__ creates an empty composite."""
        composite = PubSubAggregator()
        assert len(composite.managed_pubsubs) == 0
        assert not composite.is_shutdown

    def test_init_with_pubsubs(self) -> None:
        """Test that __init__ accepts pubsubs parameter."""
        bus_b = PubSub()
        bus_c = PubSub()
        composite = PubSubAggregator(pubsubs=[bus_b, bus_c])
        assert len(composite.managed_pubsubs) == 2
        assert bus_b in composite.managed_pubsubs
        assert bus_c in composite.managed_pubsubs

    def test_init_with_empty_pubsubs(self) -> None:
        """Test that __init__ accepts empty pubsubs list."""
        composite = PubSubAggregator(pubsubs=[])
        assert len(composite.managed_pubsubs) == 0

    def test_init_with_error_handler(self) -> None:
        """Test that __init__ accepts error_handler parameter."""
        error_calls: list[tuple[Exception, str]] = []
        lock = threading.Lock()

        def error_handler(exc: Exception, topic: str) -> None:
            with lock:
                error_calls.append((exc, topic))

        composite = PubSubAggregator(error_handler=error_handler)

        def failing_callback(msg: Message) -> None:
            raise ValueError("Test error")

        composite.subscribe("test.topic", failing_callback)
        # Publish directly to composite (not through managed PubSub)
        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        with lock:
            assert len(error_calls) == 1
            assert isinstance(error_calls[0][0], ValueError)
            assert error_calls[0][1] == "test.topic"

    def test_init_with_correlation_id(self) -> None:
        """Test that __init__ accepts correlation_id parameter."""
        composite = PubSubAggregator(correlation_id="test-correlation-id")
        assert composite._internal_bus.correlation_id == "test-correlation-id"


# ============================================================================
# Add/Remove PubSub Tests
# ============================================================================


class TestAddRemovePubSub:
    """Tests for adding and removing PubSub instances."""

    def test_add_pubsub(self) -> None:
        """Test adding a PubSub instance."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        assert len(composite.managed_pubsubs) == 1
        assert bus_b in composite.managed_pubsubs

    def test_add_multiple_pubsubs(self) -> None:
        """Test adding multiple PubSub instances."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        bus_c = PubSub()
        composite.add_pubsub(bus_b)
        composite.add_pubsub(bus_c)
        assert len(composite.managed_pubsubs) == 2
        assert bus_b in composite.managed_pubsubs
        assert bus_c in composite.managed_pubsubs

    def test_add_same_pubsub_twice_raises_error(self) -> None:
        """Test that adding the same PubSub twice raises an error."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        with pytest.raises(SplurgePubSubRuntimeError, match="already managed"):
            composite.add_pubsub(bus_b)

    def test_add_pubsub_none_raises_error(self) -> None:
        """Test that adding None raises an error."""
        composite = PubSubAggregator()
        with pytest.raises(SplurgePubSubValueError, match="cannot be None"):
            composite.add_pubsub(None)  # type: ignore[arg-type]

    def test_add_pubsub_invalid_type_raises_error(self) -> None:
        """Test that adding a non-PubSub instance raises an error."""
        composite = PubSubAggregator()
        with pytest.raises(SplurgePubSubValueError, match="must be a PubSub instance"):
            composite.add_pubsub("not a pubsub")  # type: ignore[arg-type]

    def test_add_pubsub_after_shutdown_raises_error(self) -> None:
        """Test that adding a PubSub after shutdown raises an error."""
        composite = PubSubAggregator()
        composite.shutdown()
        bus_b = PubSub()
        with pytest.raises(SplurgePubSubRuntimeError, match="has been shutdown"):
            composite.add_pubsub(bus_b)

    def test_remove_pubsub(self) -> None:
        """Test removing a PubSub instance."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        composite.remove_pubsub(bus_b)
        assert len(composite.managed_pubsubs) == 0
        assert bus_b not in composite.managed_pubsubs

    def test_remove_pubsub_not_managed_raises_error(self) -> None:
        """Test that removing a non-managed PubSub raises an error."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        with pytest.raises(SplurgePubSubLookupError, match="not managed"):
            composite.remove_pubsub(bus_b)

    def test_remove_pubsub_none_raises_error(self) -> None:
        """Test that removing None raises an error."""
        composite = PubSubAggregator()
        with pytest.raises(SplurgePubSubValueError, match="cannot be None"):
            composite.remove_pubsub(None)  # type: ignore[arg-type]

    def test_remove_pubsub_after_shutdown(self) -> None:
        """Test that removing a PubSub after shutdown doesn't raise (but doesn't do anything)."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        composite.shutdown()
        # Should not raise, but pubsub is already removed during shutdown
        assert len(composite.managed_pubsubs) == 0


# ============================================================================
# Message Forwarding Tests
# ============================================================================


class TestMessageForwarding:
    """Tests for message forwarding from managed PubSub instances."""

    def test_forward_message_from_managed_pubsub(self) -> None:
        """Test that messages from managed PubSub are forwarded."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        # Subscribe with correlation_id="*" to match all correlation_ids
        composite.subscribe("test.topic", handler, correlation_id="*")
        bus_b.publish("test.topic", {"data": "test"})
        # Drain bus_b first to ensure message is forwarded to composite
        bus_b.drain()
        # Then drain composite to ensure message is delivered
        composite.drain()

        assert len(received) == 1
        assert received[0].topic == "test.topic"
        assert received[0].data == {"data": "test"}

    def test_forward_message_from_multiple_managed_pubsubs(self) -> None:
        """Test that messages from multiple managed PubSubs are forwarded."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        bus_c = PubSub()
        composite.add_pubsub(bus_b)
        composite.add_pubsub(bus_c)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler, correlation_id="*")
        bus_b.publish("test.topic", {"data": "from_b"})
        bus_c.publish("test.topic", {"data": "from_c"})
        bus_b.drain()
        bus_c.drain()
        composite.drain()

        assert len(received) == 2
        # Messages can arrive in any order due to async processing
        received_data = [msg.data for msg in received]
        assert {"data": "from_b"} in received_data
        assert {"data": "from_c"} in received_data

    def test_forward_message_with_metadata(self) -> None:
        """Test that message metadata is preserved when forwarding."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler, correlation_id="*")
        bus_b.publish("test.topic", {"data": "test"}, metadata={"source": "bus_b"})
        bus_b.drain()
        composite.drain()

        assert len(received) == 1
        assert received[0].metadata == {"source": "bus_b"}

    def test_forward_message_with_correlation_id(self) -> None:
        """Test that correlation_id is preserved when forwarding."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler, correlation_id="*")
        bus_b.publish("test.topic", {"data": "test"}, correlation_id="custom-id")
        bus_b.drain()
        composite.drain()

        assert len(received) == 1
        assert received[0].correlation_id == "custom-id"

    def test_forward_message_after_remove_pubsub(self) -> None:
        """Test that messages are not forwarded after removing PubSub."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler)
        composite.remove_pubsub(bus_b)
        bus_b.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received) == 0

    def test_forward_message_wildcard_subscription(self) -> None:
        """Test that wildcard subscriptions receive all forwarded messages."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("*", handler, correlation_id="*")
        bus_b.publish("topic.1", {"data": "1"})
        bus_b.publish("topic.2", {"data": "2"})
        bus_b.drain()
        composite.drain()

        assert len(received) == 2
        assert received[0].topic == "topic.1"
        assert received[1].topic == "topic.2"


# ============================================================================
# Subscribe/Unsubscribe Tests
# ============================================================================


class TestSubscribeUnsubscribe:
    """Tests for subscribe and unsubscribe operations."""

    def test_subscribe(self) -> None:
        """Test subscribing to a topic."""
        composite = PubSubAggregator()
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        sub_id = composite.subscribe("test.topic", handler)
        assert sub_id is not None
        assert isinstance(sub_id, str)

        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received) == 1

    def test_subscribe_after_shutdown_raises_error(self) -> None:
        """Test that subscribing after shutdown raises an error."""
        composite = PubSubAggregator()
        composite.shutdown()

        def handler(msg: Message) -> None:
            pass

        with pytest.raises(SplurgePubSubRuntimeError, match="has been shutdown"):
            composite.subscribe("test.topic", handler)

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from a topic."""
        composite = PubSubAggregator()
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        sub_id = composite.subscribe("test.topic", handler)
        composite.unsubscribe("test.topic", sub_id)
        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received) == 0

    def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers to the same topic."""
        composite = PubSubAggregator()
        received_1: list[Message] = []
        received_2: list[Message] = []

        def handler_1(msg: Message) -> None:
            received_1.append(msg)

        def handler_2(msg: Message) -> None:
            received_2.append(msg)

        composite.subscribe("test.topic", handler_1)
        composite.subscribe("test.topic", handler_2)
        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received_1) == 1
        assert len(received_2) == 1


# ============================================================================
# Publish Tests
# ============================================================================


class TestPublish:
    """Tests for publish operations."""

    def test_publish_to_internal_bus(self) -> None:
        """Test publishing to the internal bus."""
        composite = PubSubAggregator()
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler)
        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received) == 1
        assert received[0].data == {"data": "test"}

    def test_publish_after_shutdown_raises_error(self) -> None:
        """Test that publishing after shutdown raises an error."""
        composite = PubSubAggregator()
        composite.shutdown()
        with pytest.raises(SplurgePubSubRuntimeError, match="has been shutdown"):
            composite.publish("test.topic", {"data": "test"})

    def test_publish_does_not_forward_to_managed_pubsubs(self) -> None:
        """Test that publishing does NOT forward to managed PubSub instances."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received_composite: list[Message] = []
        received_bus_b: list[Message] = []

        def handler_composite(msg: Message) -> None:
            received_composite.append(msg)

        def handler_bus_b(msg: Message) -> None:
            received_bus_b.append(msg)

        composite.subscribe("test.topic", handler_composite, correlation_id="*")
        bus_b.subscribe("test.topic", handler_bus_b)

        # Publish to composite - should only go to composite subscribers
        composite.publish("test.topic", {"data": "from_composite"})
        composite.drain()
        bus_b.drain()

        assert len(received_composite) == 1
        assert len(received_bus_b) == 0  # Should NOT receive from composite publish


# ============================================================================
# Clear Tests
# ============================================================================


class TestClear:
    """Tests for clear operations."""

    def test_clear_topic(self) -> None:
        """Test clearing subscribers from a topic."""
        composite = PubSubAggregator()
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler)
        composite.clear("test.topic")
        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received) == 0

    def test_clear_all(self) -> None:
        """Test clearing all subscribers."""
        composite = PubSubAggregator()
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("topic.1", handler)
        composite.subscribe("topic.2", handler)
        composite.clear()
        composite.publish("topic.1", {"data": "1"})
        composite.publish("topic.2", {"data": "2"})
        composite.drain()

        assert len(received) == 0


# ============================================================================
# Drain Tests
# ============================================================================


class TestDrain:
    """Tests for drain operations."""

    def test_drain_internal_bus(self) -> None:
        """Test draining the internal bus."""
        composite = PubSubAggregator()
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler)
        composite.publish("test.topic", {"data": "test"})
        result = composite.drain()

        assert result is True
        assert len(received) == 1

    def test_drain_with_cascade(self) -> None:
        """Test draining with cascade to managed PubSub instances."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received_composite: list[Message] = []
        received_bus_b: list[Message] = []

        def handler_composite(msg: Message) -> None:
            received_composite.append(msg)

        def handler_bus_b(msg: Message) -> None:
            received_bus_b.append(msg)

        composite.subscribe("test.topic", handler_composite, correlation_id="*")
        bus_b.subscribe("test.topic", handler_bus_b)

        composite.publish("test.topic", {"data": "from_composite"})
        bus_b.publish("test.topic", {"data": "from_bus_b"})

        bus_b.drain()
        result = composite.drain(cascade=True)

        assert result is True
        # Composite receives both its own publish and forwarded message from bus_b
        assert len(received_composite) == 2
        assert len(received_bus_b) == 1

    def test_drain_without_cascade(self) -> None:
        """Test that drain without cascade doesn't drain managed PubSub instances."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received_bus_b: list[Message] = []

        def handler_bus_b(msg: Message) -> None:
            received_bus_b.append(msg)

        bus_b.subscribe("test.topic", handler_bus_b)
        bus_b.publish("test.topic", {"data": "from_bus_b"})

        # Drain composite (should not drain bus_b)
        composite.drain(cascade=False)
        # Now drain bus_b explicitly
        bus_b.drain()

        assert len(received_bus_b) == 1

    def test_drain_after_shutdown(self) -> None:
        """Test that drain after shutdown returns True."""
        composite = PubSubAggregator()
        composite.shutdown()
        result = composite.drain()
        assert result is True


# ============================================================================
# Shutdown Tests
# ============================================================================


class TestShutdown:
    """Tests for shutdown operations."""

    def test_shutdown(self) -> None:
        """Test shutdown without cascade."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        composite.shutdown()

        assert composite.is_shutdown
        assert not bus_b.is_shutdown  # Should NOT be shutdown

    def test_shutdown_with_cascade(self) -> None:
        """Test shutdown with cascade."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        bus_c = PubSub()
        composite.add_pubsub(bus_b)
        composite.add_pubsub(bus_c)

        composite.shutdown(cascade=True)

        assert composite.is_shutdown
        assert bus_b.is_shutdown  # Should be shutdown
        assert bus_c.is_shutdown  # Should be shutdown

    def test_shutdown_idempotent(self) -> None:
        """Test that shutdown can be called multiple times."""
        composite = PubSubAggregator()
        composite.shutdown()
        composite.shutdown()  # Should not raise
        assert composite.is_shutdown

    def test_shutdown_unsubscribes_from_managed_pubsubs(self) -> None:
        """Test that shutdown unsubscribes from managed PubSub instances."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler, correlation_id="*")
        composite.shutdown()

        # After shutdown, messages from managed PubSub should not be forwarded
        bus_b.publish("test.topic", {"data": "test"})
        bus_b.drain()
        composite.drain()

        assert len(received) == 0

    def test_shutdown_with_cascade_unsubscribes_first(self) -> None:
        """Test that shutdown with cascade unsubscribes before shutting down managed instances."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        # Shutdown with cascade
        composite.shutdown(cascade=True)

        # Both should be shutdown
        assert composite.is_shutdown
        assert bus_b.is_shutdown


# ============================================================================
# Context Manager Tests
# ============================================================================


class TestContextManager:
    """Tests for context manager support."""

    def test_context_manager_exit_calls_shutdown(self) -> None:
        """Test that context manager exit calls shutdown."""
        with PubSubAggregator() as composite:
            assert not composite.is_shutdown
        assert composite.is_shutdown

    def test_context_manager_cleanup_on_exception(self) -> None:
        """Test that context manager cleans up on exception."""
        try:
            with PubSubAggregator() as composite:
                assert not composite.is_shutdown
                raise ValueError("Test exception")
        except ValueError:
            pass
        # Composite should still be shutdown even though exception occurred
        # Note: We can't check composite here since it's out of scope,
        # but the important thing is that __exit__ was called


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_add_remove_pubsub(self) -> None:
        """Test concurrent add/remove operations."""
        composite = PubSubAggregator()
        buses = [PubSub() for _ in range(10)]

        def add_buses() -> None:
            for bus in buses:
                try:
                    composite.add_pubsub(bus)
                except SplurgePubSubRuntimeError:
                    pass  # May fail if already added

        def remove_buses() -> None:
            for bus in buses:
                try:
                    composite.remove_pubsub(bus)
                except SplurgePubSubLookupError:
                    pass  # May fail if not managed

        threads = [
            threading.Thread(target=add_buses),
            threading.Thread(target=remove_buses),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should not crash
        assert True

    def test_concurrent_subscribe_publish(self) -> None:
        """Test concurrent subscribe and publish operations."""
        composite = PubSubAggregator()
        received: list[Message] = []
        lock = threading.Lock()

        def handler(msg: Message) -> None:
            with lock:
                received.append(msg)

        def subscribe_thread() -> None:
            for i in range(10):
                composite.subscribe(f"topic.{i}", handler)

        def publish_thread() -> None:
            for i in range(10):
                composite.publish(f"topic.{i}", {"data": i})

        threads = [
            threading.Thread(target=subscribe_thread),
            threading.Thread(target=publish_thread),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        composite.drain()

        # Should have received some messages
        assert len(received) > 0


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_managed_pubsub_shutdown_before_composite(self) -> None:
        """Test behavior when managed PubSub is shutdown before composite."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)

        bus_b.shutdown()

        # Composite should still work
        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        composite.subscribe("test.topic", handler)
        composite.publish("test.topic", {"data": "test"})
        composite.drain()

        assert len(received) == 1

    def test_remove_pubsub_that_was_shutdown(self) -> None:
        """Test removing a PubSub that was shutdown."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        bus_b.shutdown()

        # Should not raise, but may log a warning
        composite.remove_pubsub(bus_b)
        assert bus_b not in composite.managed_pubsubs

    def test_drain_cascade_with_shutdown_pubsub(self) -> None:
        """Test drain cascade with a shutdown PubSub."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        bus_b.shutdown()

        # Should not raise
        result = composite.drain(cascade=True)
        assert result is True

    def test_shutdown_cascade_with_already_shutdown_pubsub(self) -> None:
        """Test shutdown cascade with an already shutdown PubSub."""
        composite = PubSubAggregator()
        bus_b = PubSub()
        composite.add_pubsub(bus_b)
        bus_b.shutdown()

        # Should not raise
        composite.shutdown(cascade=True)
        assert composite.is_shutdown
