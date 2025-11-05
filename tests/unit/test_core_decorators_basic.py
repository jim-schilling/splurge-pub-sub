"""Tests for decorator-based subscription API.

This module provides comprehensive tests for the @bus.on() decorator
and TopicDecorator functionality.

Test Classes:
    - TestDecoratorBasics: Basic decorator functionality
    - TestDecoratorSubscription: Decorator subscription behavior
    - TestDecoratorMessageDelivery: Message delivery with decorators
    - TestDecoratorMultiple: Multiple decorators and functions
    - TestDecoratorChaining: Decorator chaining patterns
    - TestDecoratorExceptionHandling: Error handling with decorators

DOMAINS: ["testing", "decorators"]
"""

import pytest

from splurge_pub_sub import Message, PubSub

DOMAINS = ["testing", "decorators"]


class TestDecoratorBasics:
    """Tests for basic decorator functionality."""

    def test_on_method_returns_decorator(self) -> None:
        """Test that bus.on() returns a TopicDecorator."""
        bus = PubSub()
        decorator = bus.on("topic")

        # Should have __call__ method
        assert callable(decorator)

    def test_decorator_accepts_callable(self) -> None:
        """Test that decorator accepts a callable."""
        bus = PubSub()
        decorator = bus.on("topic")

        def handler(msg: Message) -> None:
            pass

        # Should not raise
        result = decorator(handler)
        assert callable(result)

    def test_decorator_returns_original_function(self) -> None:
        """Test that decorator returns the original function."""
        bus = PubSub()

        def handler(msg: Message) -> None:
            pass

        decorator = bus.on("topic")
        result = decorator(handler)

        # Should return same function
        assert result is handler

    def test_decorator_with_different_topics(self) -> None:
        """Test decorators with different topics."""
        bus = PubSub()

        def handler_1(msg: Message) -> None:
            pass

        def handler_2(msg: Message) -> None:
            pass

        bus.on("topic1")(handler_1)
        bus.on("topic2")(handler_2)

        # Both should be registered
        assert "topic1" in bus.subscribers
        assert "topic2" in bus.subscribers


class TestDecoratorSubscription:
    """Tests for decorator subscription behavior."""

    def test_decorator_registers_subscriber(self) -> None:
        """Test that decorator actually registers a subscriber."""
        bus = PubSub()

        @bus.on("user.created")
        def handle_user_created(msg: Message) -> None:
            pass

        # Should be registered
        assert "user.created" in bus.subscribers
        assert len(bus.subscribers["user.created"]) == 1

    def test_decorator_multiple_subscribers_same_topic(self) -> None:
        """Test decorating multiple handlers for same topic."""
        bus = PubSub()

        @bus.on("event")
        def handler_1(msg: Message) -> None:
            pass

        @bus.on("event")
        def handler_2(msg: Message) -> None:
            pass

        @bus.on("event")
        def handler_3(msg: Message) -> None:
            pass

        assert len(bus.subscribers["event"]) == 3

    def test_decorator_with_topic_containing_dots(self) -> None:
        """Test decorator with multi-level topics."""
        bus = PubSub()

        @bus.on("user.account.created")
        def handle(msg: Message) -> None:
            pass

        assert "user.account.created" in bus.subscribers

    def test_decorator_generates_unique_subscriber_ids(self) -> None:
        """Test that decorated subscribers get unique IDs."""
        bus = PubSub()

        @bus.on("topic")
        def handler_1(msg: Message) -> None:
            pass

        @bus.on("topic")
        def handler_2(msg: Message) -> None:
            pass

        ids = [entry.subscriber_id for entry in bus.subscribers["topic"]]

        # Should have two unique IDs
        assert len(ids) == 2
        assert len(set(ids)) == 2


class TestDecoratorMessageDelivery:
    """Tests for message delivery with decorated handlers."""

    def test_decorated_handler_receives_messages(self) -> None:
        """Test that decorated handler receives published messages."""
        received_messages = []
        bus = PubSub()

        @bus.on("user.created")
        def handle_user_created(msg: Message) -> None:
            received_messages.append(msg)

        bus.publish("user.created", {"id": 123, "name": "Alice"})

        assert len(received_messages) == 1
        assert received_messages[0].data == {"id": 123, "name": "Alice"}

    def test_decorated_handler_multiple_messages(self) -> None:
        """Test decorated handler receives multiple messages."""
        received_messages = []
        bus = PubSub()

        @bus.on("event")
        def handle_event(msg: Message) -> None:
            received_messages.append(msg.data)

        bus.publish("event", {"id": 1})
        bus.publish("event", {"id": 2})
        bus.publish("event", {"id": 3})

        assert len(received_messages) == 3
        assert [m["id"] for m in received_messages] == [1, 2, 3]

    def test_decorated_handler_not_called_for_different_topic(self) -> None:
        """Test decorated handler not called for different topics."""
        received = []
        bus = PubSub()

        @bus.on("user.created")
        def handle_user_created(msg: Message) -> None:
            received.append(msg)

        bus.publish("user.updated", {"id": 123})

        assert len(received) == 0

    def test_decorated_handler_access_message_properties(self) -> None:
        """Test that decorated handler can access message properties."""
        captured = []
        bus = PubSub()

        @bus.on("test.topic")
        def handler(msg: Message) -> None:
            captured.append(
                {
                    "topic": msg.topic,
                    "data": msg.data,
                    "timestamp": msg.timestamp,
                }
            )

        bus.publish("test.topic", {"key": "value"})

        assert len(captured) == 1
        assert captured[0]["topic"] == "test.topic"
        assert captured[0]["data"] == {"key": "value"}
        assert captured[0]["timestamp"] is not None

    def test_decorated_handler_with_complex_data(self) -> None:
        """Test decorated handler with complex message data."""
        received_data = []
        bus = PubSub()

        @bus.on("event")
        def handle(msg: Message) -> None:
            received_data.append(msg.data)

        complex_data = {
            "user": {"id": 123, "name": "Alice"},
            "nested": {"level1": {"level2": [1, 2, 3]}},
            "list": [1, "two", None, True],
        }

        bus.publish("event", complex_data)

        assert received_data[0] == complex_data


class TestDecoratorMultiple:
    """Tests for multiple decorators and decorated functions."""

    def test_multiple_decorators_on_different_topics(self) -> None:
        """Test applying decorator to handlers for different topics."""
        received_1 = []
        received_2 = []
        bus = PubSub()

        @bus.on("topic1")
        def handler_1(msg: Message) -> None:
            received_1.append(msg.data)

        @bus.on("topic2")
        def handler_2(msg: Message) -> None:
            received_2.append(msg.data)

        bus.publish("topic1", {"from": "topic1"})
        bus.publish("topic2", {"from": "topic2"})

        assert received_1 == [{"from": "topic1"}]
        assert received_2 == [{"from": "topic2"}]

    def test_decorator_preserves_function_attributes(self) -> None:
        """Test that decorator preserves function name and docstring."""
        bus = PubSub()

        @bus.on("topic")
        def my_handler(msg: Message) -> None:
            """My handler docstring."""
            pass

        # Function should retain its attributes
        assert my_handler.__name__ == "my_handler"
        assert my_handler.__doc__ == "My handler docstring."

    def test_multiple_decorated_handlers_execution_order(self) -> None:
        """Test execution order of multiple decorated handlers."""
        execution_order = []
        bus = PubSub()

        @bus.on("event")
        def handler_1(msg: Message) -> None:
            execution_order.append(1)

        @bus.on("event")
        def handler_2(msg: Message) -> None:
            execution_order.append(2)

        @bus.on("event")
        def handler_3(msg: Message) -> None:
            execution_order.append(3)

        bus.publish("event", {})

        # Should execute in registration order
        assert execution_order == [1, 2, 3]


class TestDecoratorChaining:
    """Tests for decorator chaining patterns."""

    def test_decorator_can_be_chained_with_return(self) -> None:
        """Test that decorator returns function for chaining."""
        bus = PubSub()

        def outer_decorator(func):
            """Outer decorator that doesn't modify function."""
            return func

        @outer_decorator
        @bus.on("topic")
        def handler(msg: Message) -> None:
            pass

        # Should be registered
        assert "topic" in bus.subscribers

    def test_multiple_topic_registrations_not_supported_directly(self) -> None:
        """Test that one decorator registers to one topic only."""
        bus = PubSub()

        @bus.on("topic1")
        def handler(msg: Message) -> None:
            pass

        # Only topic1 should have subscriber
        assert len(bus.subscribers.get("topic1", [])) == 1
        assert len(bus.subscribers.get("topic2", [])) == 0

    def test_function_decoratable_multiple_times_manually(self) -> None:
        """Test that same function can be decorated for multiple topics."""
        bus = PubSub()

        def shared_handler(msg: Message) -> None:
            pass

        # Can apply decorator multiple times
        bus.on("topic1")(shared_handler)
        bus.on("topic2")(shared_handler)

        assert len(bus.subscribers["topic1"]) == 1
        assert len(bus.subscribers["topic2"]) == 1


class TestDecoratorExceptionHandling:
    """Tests for error handling with decorated handlers."""

    def test_decorated_handler_exception_caught_by_error_handler(self) -> None:
        """Test that exceptions in decorated handlers are caught."""
        errors = []

        def error_handler(exc: Exception, topic: str) -> None:
            errors.append((type(exc).__name__, str(exc)))

        bus = PubSub(error_handler=error_handler)

        @bus.on("topic")
        def failing_handler(msg: Message) -> None:
            raise ValueError("handler failed")

        bus.publish("topic", {})

        assert len(errors) == 1
        assert errors[0][0] == "ValueError"
        assert errors[0][1] == "handler failed"

    def test_decorated_handler_exception_isolation(self) -> None:
        """Test that exception in one decorated handler doesn't affect others."""
        results = []
        bus = PubSub(error_handler=lambda e, t: None)

        @bus.on("topic")
        def handler_1(msg: Message) -> None:
            raise ValueError("error")

        @bus.on("topic")
        def handler_2(msg: Message) -> None:
            results.append("executed")

        bus.publish("topic", {})

        # Second handler should still execute
        assert "executed" in results

    def test_decorated_handler_with_custom_error_handler(self) -> None:
        """Test decorated handler with custom error handling."""
        log = []

        def custom_handler(exc: Exception, topic: str) -> None:
            log.append(f"Error on {topic}: {exc}")

        bus = PubSub(error_handler=custom_handler)

        @bus.on("critical.operation")
        def critical_handler(msg: Message) -> None:
            raise RuntimeError("operation failed")

        bus.publish("critical.operation", {})

        assert len(log) == 1
        assert "critical.operation" in log[0]
        assert "operation failed" in log[0]


class TestDecoratorWithShutdown:
    """Tests for decorated handlers with bus shutdown."""

    def test_decorated_handler_with_context_manager(self) -> None:
        """Test decorated handler with context manager."""
        received = []

        with PubSub() as bus:

            @bus.on("topic")
            def handler(msg: Message) -> None:
                received.append(msg.data)

            bus.publish("topic", {"id": 1})

        # Handler should have received message before shutdown
        assert received == [{"id": 1}]

    def test_decorated_handler_after_shutdown(self) -> None:
        """Test that decorated handlers can't be added after shutdown."""
        bus = PubSub()
        bus.shutdown()

        # Should raise error when trying to subscribe
        from splurge_pub_sub import SplurgePubSubRuntimeError

        with pytest.raises(SplurgePubSubRuntimeError):

            @bus.on("topic")
            def handler(msg: Message) -> None:
                pass


class TestDecoratorIntegration:
    """Integration tests for decorator API."""

    def test_decorator_equivalence_with_manual_subscribe(self) -> None:
        """Test that decorator produces same result as manual subscribe."""
        received_1 = []
        received_2 = []

        bus_1 = PubSub()
        bus_2 = PubSub()

        # Manual subscription
        bus_1.subscribe("topic", lambda m: received_1.append(m.data))

        # Decorated subscription
        @bus_2.on("topic")
        def handler(msg: Message) -> None:
            received_2.append(msg.data)

        # Publish same data to both
        test_data = {"id": 123}
        bus_1.publish("topic", test_data)
        bus_2.publish("topic", test_data)

        # Results should be same
        assert received_1 == received_2 == [test_data]

    def test_mixed_decorated_and_manual_subscriptions(self) -> None:
        """Test mixing decorated and manually subscribed handlers."""
        results = []
        bus = PubSub()

        # Manual subscription
        bus.subscribe("event", lambda m: results.append("manual"))

        # Decorated subscription
        @bus.on("event")
        def decorated_handler(msg: Message) -> None:
            results.append("decorated")

        bus.publish("event", {})

        # Both should execute (manual first as it was registered first)
        assert results == ["manual", "decorated"]

    def test_decorator_with_complex_application(self) -> None:
        """Test decorator in realistic application scenario."""
        events = []
        bus = PubSub()

        @bus.on("user.created")
        def on_user_created(msg: Message) -> None:
            events.append(f"User created: {msg.data['name']}")

        @bus.on("user.updated")
        def on_user_updated(msg: Message) -> None:
            events.append(f"User updated: {msg.data['name']}")

        @bus.on("user.deleted")
        def on_user_deleted(msg: Message) -> None:
            events.append(f"User deleted: {msg.data['name']}")

        # Simulate application events
        bus.publish("user.created", {"id": 1, "name": "Alice"})
        bus.publish("user.updated", {"id": 1, "name": "Alice Smith"})
        bus.publish("user.deleted", {"id": 1, "name": "Alice Smith"})

        assert len(events) == 3
        assert events[0] == "User created: Alice"
        assert events[1] == "User updated: Alice Smith"
        assert events[2] == "User deleted: Alice Smith"
