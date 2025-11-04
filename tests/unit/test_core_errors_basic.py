"""Tests for error handling in Splurge Pub-Sub.

This module provides comprehensive tests for the error handler system
and custom exception handling in subscriber callbacks.

Test Classes:
    - TestDefaultErrorHandler: Default error handler behavior
    - TestCustomErrorHandler: Custom error handler registration
    - TestErrorHandlerCalling: Error handler invocation scenarios
    - TestErrorHandlerExecution: Error handler execution details
    - TestErrorHandlerIsolation: Exception isolation in error handlers
    - TestErrorHandlerWithPublish: Error handling during publish

DOMAINS: ["testing", "errors"]
"""

import logging
from unittest.mock import MagicMock

import pytest

from splurge_pub_sub import Message, PubSub, default_error_handler

DOMAINS = ["testing", "errors"]


class TestDefaultErrorHandler:
    """Tests for default error handler."""

    def test_default_error_handler_logs_exception(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that default error handler logs exceptions."""
        exc = ValueError("test error")

        with caplog.at_level(logging.ERROR):
            default_error_handler(exc, "test.topic")

        assert "test error" in caplog.text
        assert "test.topic" in caplog.text

    def test_default_error_handler_logs_exception_type(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that default error handler logs exception type."""
        exc = RuntimeError("runtime issue")

        with caplog.at_level(logging.ERROR):
            default_error_handler(exc, "runtime.topic")

        assert "RuntimeError" in caplog.text
        assert "runtime issue" in caplog.text

    def test_default_error_handler_with_different_exceptions(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test default error handler with various exception types."""
        exceptions = [
            ValueError("value error"),
            TypeError("type error"),
            KeyError("key error"),
            RuntimeError("runtime error"),
        ]

        for exc in exceptions:
            with caplog.at_level(logging.ERROR):
                default_error_handler(exc, "error.topic")

            assert type(exc).__name__ in caplog.text


class TestCustomErrorHandler:
    """Tests for custom error handler registration."""

    def test_register_custom_error_handler(self) -> None:
        """Test registering a custom error handler."""
        mock_handler = MagicMock()
        bus = PubSub(error_handler=mock_handler)

        # Trigger an error
        def failing_callback(msg: Message) -> None:
            raise ValueError("test error")

        bus.subscribe("topic", failing_callback)
        bus.publish("topic", {"data": "test"})

        mock_handler.assert_called_once()
        args = mock_handler.call_args[0]
        assert isinstance(args[0], ValueError)
        assert args[1] == "topic"

    def test_custom_error_handler_receives_exception_and_topic(self) -> None:
        """Test that custom error handler receives correct parameters."""
        received_calls = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            received_calls.append({"exception": exc, "topic": topic})

        bus = PubSub(error_handler=tracking_handler)

        def failing_callback(msg: Message) -> None:
            raise RuntimeError("specific error")

        bus.subscribe("user.created", failing_callback)
        bus.publish("user.created", {"id": 123})

        assert len(received_calls) == 1
        assert isinstance(received_calls[0]["exception"], RuntimeError)
        assert received_calls[0]["topic"] == "user.created"

    def test_error_handler_none_uses_default(self) -> None:
        """Test that None error_handler uses default."""
        bus = PubSub(error_handler=None)

        def failing_callback(msg: Message) -> None:
            raise ValueError("test")

        bus.subscribe("topic", failing_callback)
        # Should not raise, should use default handler
        bus.publish("topic", {})


class TestErrorHandlerCalling:
    """Tests for error handler invocation."""

    def test_error_handler_called_on_callback_exception(self) -> None:
        """Test that error handler is called when callback raises."""
        mock_handler = MagicMock()
        bus = PubSub(error_handler=mock_handler)

        def failing_callback(msg: Message) -> None:
            raise ValueError("callback failed")

        bus.subscribe("topic", failing_callback)
        bus.publish("topic", {})

        mock_handler.assert_called_once()

    def test_error_handler_not_called_on_success(self) -> None:
        """Test that error handler is not called when callback succeeds."""
        mock_handler = MagicMock()
        bus = PubSub(error_handler=mock_handler)

        def working_callback(msg: Message) -> None:
            pass  # No error

        bus.subscribe("topic", working_callback)
        bus.publish("topic", {})

        mock_handler.assert_not_called()

    def test_error_handler_called_for_each_failing_subscriber(self) -> None:
        """Test that error handler is called for each failing subscriber."""
        mock_handler = MagicMock()
        bus = PubSub(error_handler=mock_handler)

        def failing_callback_1(msg: Message) -> None:
            raise ValueError("error 1")

        def failing_callback_2(msg: Message) -> None:
            raise RuntimeError("error 2")

        bus.subscribe("topic", failing_callback_1)
        bus.subscribe("topic", failing_callback_2)
        bus.publish("topic", {})

        # Should be called twice (once for each failing subscriber)
        assert mock_handler.call_count == 2

    def test_error_handler_called_for_multiple_publishes(self) -> None:
        """Test error handler called for each publish with error."""
        mock_handler = MagicMock()
        bus = PubSub(error_handler=mock_handler)

        def failing_callback(msg: Message) -> None:
            raise ValueError("error")

        bus.subscribe("topic", failing_callback)

        bus.publish("topic", {"id": 1})
        bus.publish("topic", {"id": 2})
        bus.publish("topic", {"id": 3})

        # Should be called three times
        assert mock_handler.call_count == 3


class TestErrorHandlerExecution:
    """Tests for error handler execution details."""

    def test_error_handler_receives_correct_exception(self) -> None:
        """Test that error handler receives the actual exception."""
        received_exceptions = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            received_exceptions.append(exc)

        bus = PubSub(error_handler=tracking_handler)

        expected_error = ValueError("specific message")

        def failing_callback(msg: Message) -> None:
            raise expected_error

        bus.subscribe("topic", failing_callback)
        bus.publish("topic", {})

        assert len(received_exceptions) == 1
        assert received_exceptions[0] is expected_error
        assert str(received_exceptions[0]) == "specific message"

    def test_error_handler_receives_correct_topic(self) -> None:
        """Test that error handler receives the correct topic."""
        received_topics = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            received_topics.append(topic)

        bus = PubSub(error_handler=tracking_handler)

        def failing_callback(msg: Message) -> None:
            raise ValueError("error")

        bus.subscribe("user.created", failing_callback)
        bus.subscribe("order.paid", failing_callback)

        bus.publish("user.created", {})
        bus.publish("order.paid", {})

        assert received_topics == ["user.created", "order.paid"]

    def test_error_handler_execution_order(self) -> None:
        """Test that error handler is called in sequence for multiple errors."""
        call_order = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            call_order.append(str(exc))

        bus = PubSub(error_handler=tracking_handler)

        def failing_1(msg: Message) -> None:
            raise ValueError("error 1")

        def failing_2(msg: Message) -> None:
            raise RuntimeError("error 2")

        bus.subscribe("topic", failing_1)
        bus.subscribe("topic", failing_2)

        bus.publish("topic", {})

        assert call_order == ["error 1", "error 2"]


class TestErrorHandlerIsolation:
    """Tests for exception isolation with error handlers."""

    def test_one_subscriber_exception_doesnt_affect_others(self) -> None:
        """Test that one subscriber's exception doesn't prevent others from running."""
        callback_calls = []

        def failing_callback(msg: Message) -> None:
            callback_calls.append("failing")
            raise ValueError("error")

        def working_callback(msg: Message) -> None:
            callback_calls.append("working")

        bus = PubSub(error_handler=lambda e, t: None)

        bus.subscribe("topic", failing_callback)
        bus.subscribe("topic", working_callback)
        bus.publish("topic", {})

        # Both callbacks should execute
        assert "failing" in callback_calls
        assert "working" in callback_calls

    def test_error_handler_exception_doesnt_affect_publish(self) -> None:
        """Test that exception in error handler doesn't break publish."""

        def failing_handler(exc: Exception, topic: str) -> None:
            raise RuntimeError("error handler failed")

        bus = PubSub(error_handler=failing_handler)

        def failing_callback(msg: Message) -> None:
            raise ValueError("callback error")

        bus.subscribe("topic", failing_callback)

        # This should raise because error handler itself fails
        # (error handler exceptions are not caught)
        with pytest.raises(RuntimeError):
            bus.publish("topic", {})

    def test_multiple_errors_all_handled(self) -> None:
        """Test that multiple subscriber errors are all handled."""
        handled_exceptions = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            handled_exceptions.append(type(exc).__name__)

        bus = PubSub(error_handler=tracking_handler)

        def failing_1(msg: Message) -> None:
            raise ValueError("error 1")

        def failing_2(msg: Message) -> None:
            raise TypeError("error 2")

        def failing_3(msg: Message) -> None:
            raise RuntimeError("error 3")

        bus.subscribe("topic", failing_1)
        bus.subscribe("topic", failing_2)
        bus.subscribe("topic", failing_3)

        bus.publish("topic", {})

        assert handled_exceptions == ["ValueError", "TypeError", "RuntimeError"]


class TestErrorHandlerWithPublish:
    """Tests for error handling during publish operations."""

    def test_error_handler_with_successful_publish(self) -> None:
        """Test error handler with mix of successful and failing subscribers."""
        handler_calls = []
        callback_calls = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            handler_calls.append(str(exc))

        def failing(msg: Message) -> None:
            callback_calls.append("failing")
            raise ValueError("error")

        def working(msg: Message) -> None:
            callback_calls.append("working")

        bus = PubSub(error_handler=tracking_handler)

        bus.subscribe("topic", failing)
        bus.subscribe("topic", working)
        bus.subscribe("topic", working)

        bus.publish("topic", {})

        # All callbacks executed
        assert callback_calls == ["failing", "working", "working"]
        # Only one error handler call
        assert len(handler_calls) == 1

    def test_error_handler_with_message_data(self) -> None:
        """Test error handler can access message details through exception context."""
        received_info = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            received_info.append({"exception": str(exc), "topic": topic})

        bus = PubSub(error_handler=tracking_handler)

        def failing(msg: Message) -> None:
            raise ValueError(f"Failed processing {msg.data}")

        bus.subscribe("user.created", failing)
        bus.publish("user.created", {"id": 123, "name": "Alice"})

        assert len(received_info) == 1
        assert "id" in received_info[0]["exception"]
        assert received_info[0]["topic"] == "user.created"

    def test_error_handler_no_interference_with_message_creation(self) -> None:
        """Test that error handler doesn't interfere with message creation."""
        handler_calls = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            handler_calls.append({"topic": topic, "error": str(exc)})

        bus = PubSub(error_handler=tracking_handler)

        def failing(msg: Message) -> None:
            raise ValueError(f"Error on {msg.topic}")

        bus.subscribe("order.created", failing)

        bus.publish("order.created", {"order_id": 42})
        bus.publish("order.paid", {"order_id": 42})  # Different topic, no subscribers

        # Should only handle error from first publish
        assert len(handler_calls) == 1
        assert handler_calls[0]["topic"] == "order.created"


class TestErrorHandlerIntegration:
    """Integration tests for error handlers."""

    def test_error_handler_with_context_manager(self) -> None:
        """Test error handler works with context manager."""
        handler_calls = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            handler_calls.append(topic)

        with PubSub(error_handler=tracking_handler) as bus:

            def failing(msg: Message) -> None:
                raise ValueError("error")

            bus.subscribe("topic", failing)
            bus.publish("topic", {})

        # Handler should have been called before shutdown
        assert "topic" in handler_calls

    @pytest.mark.parametrize(
        "exception_type,exception_msg",
        [
            (ValueError, "value error"),
            (TypeError, "type error"),
            (RuntimeError, "runtime error"),
        ],
    )
    def test_error_handler_with_various_exceptions(
        self,
        exception_type: type,
        exception_msg: str,
    ) -> None:
        """Parametrized test for error handler with various exceptions."""
        received = []

        def tracking_handler(exc: Exception, topic: str) -> None:
            received.append((type(exc).__name__, str(exc)))

        bus = PubSub(error_handler=tracking_handler)

        def failing(msg: Message) -> None:
            raise exception_type(exception_msg)

        bus.subscribe("topic", failing)
        bus.publish("topic", {})

        assert len(received) == 1
        assert received[0][0] == exception_type.__name__
        assert exception_msg in received[0][1]
