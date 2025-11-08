"""Unit tests for PubSubSolo scoped singleton functionality.

Test Cases:
    - Initialization (prevent direct instantiation)
    - get_instance() with mandatory scope
    - Same scope returns same instance
    - Different scopes return different instances
    - Thread-safety of instance creation
    - Configuration parameters only applied on first call
    - is_initialized() and get_all_scopes()
    - All delegation methods (subscribe, publish, unsubscribe, clear, drain, shutdown, on)
    - All delegation properties
    - Integration with PubSubAggregator
"""

import threading

import pytest

from splurge_pub_sub import (
    Message,
    PubSub,
    PubSubAggregator,
    PubSubSolo,
    SplurgePubSubRuntimeError,
)

# ============================================================================
# Initialization Tests
# ============================================================================


class TestInitialization:
    """Tests for PubSubSolo initialization."""

    def test_cannot_instantiate_directly(self) -> None:
        """Test that PubSubSolo cannot be instantiated directly."""
        with pytest.raises(RuntimeError, match="cannot be instantiated directly"):
            PubSubSolo()  # type: ignore

    def test_get_instance_requires_scope(self) -> None:
        """Test that get_instance() requires scope parameter."""
        with pytest.raises(TypeError):
            PubSubSolo.get_instance()  # type: ignore

    def test_get_instance_with_scope_returns_pubsub(self) -> None:
        """Test that get_instance() with scope returns PubSub instance."""
        # Reset any existing instances
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus = PubSubSolo.get_instance(scope="test_scope")
        assert isinstance(bus, PubSub)

    def test_same_scope_returns_same_instance(self) -> None:
        """Test that same scope returns same instance."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus1 = PubSubSolo.get_instance(scope="test_scope")
        bus2 = PubSubSolo.get_instance(scope="test_scope")
        assert bus1 is bus2

    def test_different_scopes_return_different_instances(self) -> None:
        """Test that different scopes return different instances."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus_a = PubSubSolo.get_instance(scope="scope_a")
        bus_b = PubSubSolo.get_instance(scope="scope_b")
        assert bus_a is not bus_b

    def test_configuration_only_applied_on_first_call(self) -> None:
        """Test that error_handler and correlation_id only applied on first call."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        error_handler_calls: list[tuple[Exception, str]] = []

        def custom_error_handler(exc: Exception, topic: str) -> None:
            error_handler_calls.append((exc, topic))

        # First call with custom error handler
        bus1 = PubSubSolo.get_instance(
            scope="test_config",
            error_handler=custom_error_handler,
            correlation_id="custom-id-1",
        )
        assert bus1.correlation_id == "custom-id-1"

        # Second call with different config - should be ignored
        bus2 = PubSubSolo.get_instance(
            scope="test_config",
            error_handler=lambda e, t: None,  # Different handler
            correlation_id="custom-id-2",  # Different correlation_id
        )
        assert bus1 is bus2  # Same instance
        assert bus2.correlation_id == "custom-id-1"  # Original config kept

        # Verify error handler is the original one
        bus1.publish("test.topic", {"data": "test"})

        # Subscribe a callback that raises
        def failing_callback(msg: Message) -> None:
            raise ValueError("Test error")

        bus1.subscribe("test.topic", failing_callback)
        bus1.publish("test.topic", {"data": "test"})
        bus1.drain()

        # Should have called our custom error handler
        assert len(error_handler_calls) > 0


# ============================================================================
# Thread Safety Tests
# ============================================================================


class TestThreadSafety:
    """Tests for thread-safe singleton creation."""

    def test_concurrent_get_instance_same_scope(self) -> None:
        """Test that concurrent get_instance() calls return same instance."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        instances: list[PubSub] = []
        lock = threading.Lock()

        def get_instance() -> None:
            bus = PubSubSolo.get_instance(scope="concurrent_scope")
            with lock:
                instances.append(bus)

        # Create multiple threads
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All instances should be the same
        assert len(instances) == 10
        first_instance = instances[0]
        assert all(inst is first_instance for inst in instances)

    def test_concurrent_get_instance_different_scopes(self) -> None:
        """Test that concurrent get_instance() calls with different scopes work."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        instances: dict[str, PubSub] = {}
        lock = threading.Lock()

        def get_instance(scope: str) -> None:
            bus = PubSubSolo.get_instance(scope=scope)
            with lock:
                instances[scope] = bus

        # Create threads for different scopes
        scopes = [f"scope_{i}" for i in range(10)]
        threads = [threading.Thread(target=get_instance, args=(scope,)) for scope in scopes]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Each scope should have its own instance
        assert len(instances) == 10
        # All instances should be different
        instance_list = list(instances.values())
        assert len(set(id(inst) for inst in instance_list)) == 10


# ============================================================================
# Utility Methods Tests
# ============================================================================


class TestUtilityMethods:
    """Tests for utility methods (is_initialized, get_all_scopes)."""

    def test_is_initialized(self) -> None:
        """Test is_initialized() method."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        assert not PubSubSolo.is_initialized("test_scope")
        PubSubSolo.get_instance(scope="test_scope")
        assert PubSubSolo.is_initialized("test_scope")

    def test_get_all_scopes(self) -> None:
        """Test get_all_scopes() method."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        assert len(PubSubSolo.get_all_scopes()) == 0

        PubSubSolo.get_instance(scope="scope1")
        PubSubSolo.get_instance(scope="scope2")
        PubSubSolo.get_instance(scope="scope3")

        scopes = PubSubSolo.get_all_scopes()
        assert len(scopes) == 3
        assert "scope1" in scopes
        assert "scope2" in scopes
        assert "scope3" in scopes


# ============================================================================
# Delegation Methods Tests
# ============================================================================


class TestDelegationMethods:
    """Tests for delegation methods."""

    def test_subscribe_delegation(self) -> None:
        """Test subscribe() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        sub_id = PubSubSolo.subscribe("test.topic", callback, scope="delegation_test")
        assert isinstance(sub_id, str)

        PubSubSolo.publish("test.topic", {"data": "test"}, scope="delegation_test")
        bus = PubSubSolo.get_instance(scope="delegation_test")
        bus.drain()

        assert len(received) == 1
        assert received[0].data == {"data": "test"}

    def test_publish_delegation(self) -> None:
        """Test publish() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        bus = PubSubSolo.get_instance(scope="publish_test")
        bus.subscribe("test.topic", callback)

        PubSubSolo.publish("test.topic", {"data": "test"}, scope="publish_test")
        bus.drain()

        assert len(received) == 1

    def test_unsubscribe_delegation(self) -> None:
        """Test unsubscribe() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        sub_id = PubSubSolo.subscribe("test.topic", callback, scope="unsubscribe_test")
        PubSubSolo.publish("test.topic", {"data": "test1"}, scope="unsubscribe_test")
        bus = PubSubSolo.get_instance(scope="unsubscribe_test")
        bus.drain()

        assert len(received) == 1

        PubSubSolo.unsubscribe("test.topic", sub_id, scope="unsubscribe_test")
        PubSubSolo.publish("test.topic", {"data": "test2"}, scope="unsubscribe_test")
        bus.drain()

        assert len(received) == 1  # Still 1, unsubscribed

    def test_clear_delegation(self) -> None:
        """Test clear() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        PubSubSolo.subscribe("test.topic", callback, scope="clear_test")
        PubSubSolo.publish("test.topic", {"data": "test1"}, scope="clear_test")
        bus = PubSubSolo.get_instance(scope="clear_test")
        bus.drain()

        assert len(received) == 1

        PubSubSolo.clear(scope="clear_test")
        PubSubSolo.publish("test.topic", {"data": "test2"}, scope="clear_test")
        bus.drain()

        assert len(received) == 1  # Still 1, cleared

    def test_drain_delegation(self) -> None:
        """Test drain() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        received: list[Message] = []

        def callback(msg: Message) -> None:
            received.append(msg)

        PubSubSolo.subscribe("test.topic", callback, scope="drain_test")
        PubSubSolo.publish("test.topic", {"data": "test"}, scope="drain_test")

        result = PubSubSolo.drain(scope="drain_test")
        assert result is True
        assert len(received) == 1

    def test_shutdown_delegation(self) -> None:
        """Test shutdown() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus = PubSubSolo.get_instance(scope="shutdown_test")
        assert not bus.is_shutdown

        PubSubSolo.shutdown(scope="shutdown_test")
        assert bus.is_shutdown
        assert not PubSubSolo.is_initialized("shutdown_test")

    def test_on_delegation(self) -> None:
        """Test on() decorator delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        received: list[Message] = []

        @PubSubSolo.on("test.topic", scope="on_test")
        def callback(msg: Message) -> None:
            received.append(msg)

        PubSubSolo.publish("test.topic", {"data": "test"}, scope="on_test")
        bus = PubSubSolo.get_instance(scope="on_test")
        bus.drain()

        assert len(received) == 1


# ============================================================================
# Property Delegation Tests
# ============================================================================


class TestPropertyDelegation:
    """Tests for property delegation methods."""

    def test_get_correlation_id(self) -> None:
        """Test get_correlation_id() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus = PubSubSolo.get_instance(scope="correlation_test", correlation_id="test-id")
        assert PubSubSolo.get_correlation_id(scope="correlation_test") == "test-id"
        assert PubSubSolo.get_correlation_id(scope="correlation_test") == bus.correlation_id

    def test_get_correlation_ids(self) -> None:
        """Test get_correlation_ids() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus = PubSubSolo.get_instance(scope="correlation_ids_test")
        bus.publish("test.topic", {}, correlation_id="custom-id")
        bus.drain()

        correlation_ids = PubSubSolo.get_correlation_ids(scope="correlation_ids_test")
        assert isinstance(correlation_ids, set)
        assert "custom-id" in correlation_ids

    def test_get_is_shutdown(self) -> None:
        """Test get_is_shutdown() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus = PubSubSolo.get_instance(scope="is_shutdown_test")
        assert PubSubSolo.get_is_shutdown(scope="is_shutdown_test") is False

        bus.shutdown()
        assert PubSubSolo.get_is_shutdown(scope="is_shutdown_test") is True

    def test_get_is_shutdown_uninitialized(self) -> None:
        """Test get_is_shutdown() for uninitialized scope."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        assert PubSubSolo.get_is_shutdown(scope="uninitialized") is True

    def test_get_subscribers(self) -> None:
        """Test get_subscribers() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        def callback(msg: Message) -> None:
            pass

        PubSubSolo.subscribe("test.topic", callback, scope="subscribers_test")
        subscribers = PubSubSolo.get_subscribers(scope="subscribers_test")
        assert isinstance(subscribers, dict)
        assert "test.topic" in subscribers

    def test_get_wildcard_subscribers(self) -> None:
        """Test get_wildcard_subscribers() delegation."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        def callback(msg: Message) -> None:
            pass

        PubSubSolo.subscribe("*", callback, scope="wildcard_test")
        wildcard_subscribers = PubSubSolo.get_wildcard_subscribers(scope="wildcard_test")
        assert isinstance(wildcard_subscribers, list)
        assert len(wildcard_subscribers) == 1


# ============================================================================
# Integration with PubSubAggregator Tests
# ============================================================================


class TestPubSubAggregatorIntegration:
    """Tests for PubSubSolo integration with PubSubAggregator."""

    def test_aggregate_multiple_scopes(self) -> None:
        """Test aggregating PubSubSolo instances from different scopes."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus_a = PubSubSolo.get_instance(scope="package_a")
        bus_b = PubSubSolo.get_instance(scope="package_b")
        bus_c = PubSubSolo.get_instance(scope="package_c")

        # Verify they're different instances
        assert bus_a is not bus_b
        assert bus_a is not bus_c
        assert bus_b is not bus_c

        # Create aggregator
        aggregator = PubSubAggregator(pubsubs=[bus_a, bus_b, bus_c])

        received: list[Message] = []

        def handler(msg: Message) -> None:
            received.append(msg)

        aggregator.subscribe("user.created", handler, correlation_id="*")

        # Publish from different scopes
        bus_a.publish("user.created", {"source": "package_a"})
        bus_b.publish("user.created", {"source": "package_b"})
        bus_c.publish("user.created", {"source": "package_c"})

        # Drain all buses
        bus_a.drain()
        bus_b.drain()
        bus_c.drain()
        aggregator.drain()

        assert len(received) == 3
        sources = [msg.data["source"] for msg in received]
        assert "package_a" in sources
        assert "package_b" in sources
        assert "package_c" in sources

    def test_same_scope_instance_cannot_be_added_twice(self) -> None:
        """Test that same scope instance cannot be added to aggregator twice."""
        # Reset all instances for clean test state
        for scope in PubSubSolo.get_all_scopes():
            PubSubSolo.shutdown(scope=scope)

        bus_a = PubSubSolo.get_instance(scope="package_a")
        bus_a2 = PubSubSolo.get_instance(scope="package_a")  # Same instance

        aggregator = PubSubAggregator(pubsubs=[bus_a])

        # Try to add same instance again
        with pytest.raises(SplurgePubSubRuntimeError, match="already managed"):
            aggregator.add_pubsub(bus_a2)
