"""Main PubSub class for the Splurge Pub-Sub framework.

This module implements the core PubSub class, providing a lightweight,
thread-safe publish-subscribe pattern for in-process event communication.

Domains:
    - pubsub
"""

import logging
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from .errors import ErrorHandler
from .exceptions import (
    SplurgePubSubLookupError,
    SplurgePubSubRuntimeError,
    SplurgePubSubTypeError,
    SplurgePubSubValueError,
)
from .message import Message
from .types import Callback, MessageData, Metadata, SubscriberId, Topic

if TYPE_CHECKING:
    from .decorators import TopicDecorator

DOMAINS = ["pubsub"]

__all__ = ["PubSub"]

logger = logging.getLogger(__name__)


@dataclass
class _SubscriberEntry:
    """Internal representation of a subscriber."""

    subscriber_id: SubscriberId
    callback: Callback


class PubSub:
    """Lightweight, thread-safe publish-subscribe framework.

    Implements a fan-out event bus where all subscribers receive all published
    messages for their topic. Provides synchronous callback execution with
    full thread-safety for concurrent operations.

    Thread-Safety:
        All operations are thread-safe using an RLock for synchronization.
        The lock is held only during critical sections (subscription registry
        updates), allowing subscribers to publish during callbacks without
        deadlock.

    Example:
        >>> bus = PubSub()
        >>> def on_event(msg: Message) -> None:
        ...     print(f"Received: {msg.data}")
        >>> sub_id = bus.subscribe("user.created", on_event)
        >>> bus.publish("user.created", {"id": 123, "name": "Alice"})
        Received: {'id': 123, 'name': 'Alice'}
        >>> bus.unsubscribe("user.created", sub_id)

    Context Manager Support:
        The bus can be used as a context manager for automatic cleanup:

        >>> with PubSub() as bus:
        ...     bus.subscribe("topic", callback)
        ...     bus.publish("topic", data)
        ... # Resources cleaned up automatically

    Lifecycle:
        - Create instance: bus = PubSub()
        - Subscribe: sub_id = bus.subscribe(topic, callback)
        - Publish: bus.publish(topic, data)
        - Unsubscribe: bus.unsubscribe(topic, sub_id)
        - Shutdown: bus.shutdown() or use context manager
    """

    def __init__(
        self,
        error_handler: "ErrorHandler | None" = None,
    ) -> None:
        """Initialize a new PubSub instance.

        Creates an empty subscription registry and sets up thread-safety
        mechanisms.

        Args:
            error_handler: Optional custom error handler for subscriber callbacks.
                          Defaults to logging errors.

        Example:
            >>> def my_error_handler(exc: Exception, topic: str) -> None:
            ...     print(f"Error on {topic}: {exc}")
            >>> bus = PubSub(error_handler=my_error_handler)
        """
        from .errors import default_error_handler

        self._lock: threading.RLock = threading.RLock()
        self._subscribers: dict[Topic, list[_SubscriberEntry]] = {}
        self._is_shutdown: bool = False
        self._error_handler: ErrorHandler = error_handler or default_error_handler

    def subscribe(
        self,
        topic: str,
        callback: Callback,
    ) -> SubscriberId:
        """Subscribe to a topic with a callback function.

        The callback will be invoked for each message published to the topic.
        Multiple subscribers can subscribe to the same topic.

        Args:
            topic: Topic identifier (uses dot notation, e.g., "user.created")
            callback: Callable that accepts a Message and returns None

        Returns:
            SubscriberId: Unique identifier for this subscription

        Raises:
            SplurgePubSubValueError: If topic is empty
            SplurgePubSubTypeError: If callback is not callable
            SplurgePubSubRuntimeError: If the bus is shutdown

        Example:
            >>> bus = PubSub()
            >>> def handle_event(msg: Message) -> None:
            ...     print(f"Event: {msg.data}")
            >>> sub_id = bus.subscribe("order.created", handle_event)
            >>> sub_id
            '...'  # UUID string
        """
        # Validate inputs
        if not topic or not isinstance(topic, str):
            raise SplurgePubSubValueError(f"Topic must be a non-empty string, got: {topic!r}")

        if not callable(callback):
            raise SplurgePubSubTypeError(f"Callback must be callable, got: {type(callback).__name__}")

        with self._lock:
            # Check shutdown state
            if self._is_shutdown:
                raise SplurgePubSubRuntimeError("Cannot subscribe: PubSub has been shutdown")

            # Generate unique subscriber ID
            subscriber_id: SubscriberId = str(uuid4())

            # Create entry
            entry = _SubscriberEntry(
                subscriber_id=subscriber_id,
                callback=callback,
            )

            # Add to registry
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(entry)

            logger.debug(f"Subscriber {subscriber_id} subscribed to topic '{topic}'")

        return subscriber_id

    def publish(
        self,
        topic: str,
        data: MessageData | None = None,
        metadata: Metadata | None = None,
    ) -> None:
        """Publish a message to a topic.

        All subscribers for the topic receive the message via their callbacks.
        Callbacks are invoked synchronously in the order subscriptions were made.

        If a callback raises an exception, it is passed to the error handler.
        Exceptions in one callback do not affect other callbacks or the publisher.

        Args:
            topic: Topic identifier (uses dot notation, e.g., "user.created")
            data: Message payload (dict[str, Any] with string keys only). Defaults to empty dict.
            metadata: Optional metadata dictionary for message context. Defaults to empty dict.

        Raises:
            SplurgePubSubValueError: If topic is empty or not a string
            SplurgePubSubTypeError: If data is not a dict[str, Any] or has non-string keys

        Example:
            >>> bus = PubSub()
            >>> bus.subscribe("order.created", lambda m: print(m.data))
            '...'
            >>> bus.publish("order.created", {"order_id": 42, "total": 99.99})
            >>> bus.publish("order.created", {"order_id": 42}, metadata={"source": "api"})
            >>> bus.publish("order.created")  # Empty data and metadata
        """
        # Validate input
        if not topic or not isinstance(topic, str):
            raise SplurgePubSubValueError(f"Topic must be a non-empty string, got: {topic!r}")

        # Initialize data and metadata to empty dicts if None
        message = Message(
            topic=topic,
            data=data if data is not None else {},
            metadata=metadata if metadata is not None else {},
        )

        # Get snapshot of subscribers (release lock before callbacks)
        with self._lock:
            subscribers = list(self._subscribers.get(topic, []))

        # Execute callbacks outside lock to allow re-entrant publishes
        for entry in subscribers:
            try:
                entry.callback(message)
            except Exception as e:
                # Call error handler for subscriber exceptions
                self._error_handler(e, topic)

    def unsubscribe(
        self,
        topic: str,
        subscriber_id: SubscriberId,
    ) -> None:
        """Unsubscribe a subscriber from a topic.

        Args:
            topic: Topic identifier
            subscriber_id: Subscriber ID from subscribe() call

        Raises:
            SplurgePubSubValueError: If topic is empty
            SplurgePubSubLookupError: If subscriber not found for topic

        Example:
            >>> bus = PubSub()
            >>> sub_id = bus.subscribe("topic", callback)
            >>> bus.unsubscribe("topic", sub_id)
        """
        # Validate input
        if not topic or not isinstance(topic, str):
            raise SplurgePubSubValueError(f"Topic must be a non-empty string, got: {topic!r}")

        with self._lock:
            # Find and remove the subscriber
            if topic not in self._subscribers:
                raise SplurgePubSubLookupError(f"No subscribers found for topic '{topic}'")

            subscribers = self._subscribers[topic]
            for i, entry in enumerate(subscribers):
                if entry.subscriber_id == subscriber_id:
                    subscribers.pop(i)
                    logger.debug(f"Subscriber {subscriber_id} unsubscribed from topic '{topic}'")
                    # Clean up empty topic lists
                    if not subscribers:
                        del self._subscribers[topic]
                    return

            raise SplurgePubSubLookupError(f"Subscriber '{subscriber_id}' not found for topic '{topic}'")

    def clear(
        self,
        topic: str | None = None,
    ) -> None:
        """Clear subscribers from topic(s).

        Args:
            topic: Specific topic to clear, or None to clear all subscribers

        Example:
            >>> bus = PubSub()
            >>> bus.subscribe("topic", callback)
            '...'
            >>> bus.clear("topic")  # Clear one topic
            >>> bus.clear()  # Clear all topics
        """
        with self._lock:
            if topic is None:
                # Clear all subscribers
                self._subscribers.clear()
                logger.debug("All subscribers cleared")
            else:
                # Clear specific topic
                if topic in self._subscribers:
                    del self._subscribers[topic]
                    logger.debug(f"Subscribers cleared for topic '{topic}'")

    def shutdown(self) -> None:
        """Shutdown the bus and prevent further operations.

        Clears all subscribers and sets shutdown flag. Subsequent calls to
        subscribe() or publish() will raise SplurgePubSubRuntimeError.

        Safe to call multiple times (idempotent).

        Example:
            >>> bus = PubSub()
            >>> bus.subscribe("topic", callback)
            '...'
            >>> bus.shutdown()
            >>> bus.subscribe("topic", callback)  # Raises SplurgePubSubRuntimeError
        """
        with self._lock:
            self._subscribers.clear()
            self._is_shutdown = True
            logger.debug("PubSub shutdown complete")

    def on(self, topic: Topic) -> "TopicDecorator":
        """Create a decorator for subscribing to a topic.

        Allows using @bus.on() syntax for simplified subscriptions.

        Args:
            topic: Topic to subscribe to

        Returns:
            TopicDecorator instance that acts as a subscription decorator

        Example:
            >>> bus = PubSub()
            >>> @bus.on("user.created")
            ... def handle_user_created(msg: Message) -> None:
            ...     print(f"User created: {msg.data}")
            >>> bus.publish("user.created", {"id": 123})
            User created: {'id': 123}

        See Also:
            subscribe(): Manual subscription method
        """
        from .decorators import TopicDecorator

        return TopicDecorator(pubsub=self, topic=topic)

    def __enter__(self) -> "PubSub":
        """Enter context manager.

        Returns:
            This PubSub instance

        Example:
            >>> with PubSub() as bus:
            ...     bus.subscribe("topic", callback)
            ...     bus.publish("topic", data)
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type if exception occurred, else None
            exc_val: Exception value if exception occurred, else None
            exc_tb: Exception traceback if exception occurred, else None
        """
        self.shutdown()
