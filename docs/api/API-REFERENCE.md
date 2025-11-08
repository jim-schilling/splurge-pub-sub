# Splurge Pub-Sub - API Reference

Complete reference for the Splurge Pub-Sub framework public API.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Type Aliases](#type-aliases)
3. [Exception Classes](#exception-classes)
4. [Functions](#functions)
5. [Examples](#examples)
6. [Related Documentation](#related-documentation)

## Core Classes

### PubSub

Main class for publish-subscribe operations.

#### Constructor

```python
class PubSub:
    def __init__(
        self,
        *,
        error_handler: ErrorHandler | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize a new PubSub instance.

        Args:
            error_handler: Optional custom error handler for subscriber callbacks.
                          Defaults to logging errors. Must be passed as a keyword
                          argument.
            correlation_id: Optional correlation ID. If None or '', auto-generates.
                           Must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9] (2-64 chars)
                           with no consecutive '.', '-', or '_' characters.
                           Must be passed as a keyword argument.

        Example:
            >>> def my_error_handler(exc: Exception, topic: str) -> None:
            ...     print(f"Error on {topic}: {exc}")
            >>> bus = PubSub(error_handler=my_error_handler)
            >>> bus = PubSub(correlation_id="my-correlation-id")
        """
```

#### Methods

##### subscribe

```python
def subscribe(
    self,
    topic: str,
    callback: Callback,
    *,
    correlation_id: str | None = None,
) -> SubscriberId:
    """Subscribe to a topic with a callback function.

    The callback will be invoked for each message published to the topic.
    Multiple subscribers can subscribe to the same topic.

    Args:
        topic: Topic identifier (uses dot notation, e.g., "user.created") or "*" for all topics
        callback: Callable that accepts a Message and returns None
        correlation_id: Optional filter. If None or '', uses instance correlation_id.
                       If '*', matches any correlation_id. Otherwise must match pattern
                       [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9] (2-64 chars) with no consecutive '.', '-', or '_'.
                       Must be passed as a keyword argument.

    Returns:
        SubscriberId: Unique identifier for this subscription (UUID string)

    Raises:
        SplurgePubSubValueError: If topic is empty or not a string, or correlation_id is invalid
        SplurgePubSubTypeError: If callback is not callable
        SplurgePubSubRuntimeError: If the bus is shutdown

    Example:
        >>> bus = PubSub()
        >>> def handle_event(msg: Message) -> None:
        ...     print(f"Event: {msg.data}")
        >>> sub_id = bus.subscribe("order.created", handle_event)
        >>> isinstance(sub_id, str)
        True
    """
```

**Error Messages**:
- `"Topic must be a non-empty string, got: <value>"` - Empty or invalid topic
- `"Callback must be callable, got: <type>"` - Non-callable callback
- `"Cannot subscribe: PubSub has been shutdown"` - Bus is shutdown

##### publish

```python
def publish(
    self,
    topic: str,
    data: MessageData | None = None,
    metadata: Metadata | None = None,
    *,
    correlation_id: str | None = None,
) -> None:
    """Publish a message to a topic.

    Messages are enqueued and dispatched asynchronously by a background worker thread.
    This method returns immediately after enqueueing, ensuring publishers never block
    on subscriber execution.

    All subscribers for the topic receive the message via their callbacks.
    Callbacks are invoked asynchronously in the order subscriptions were made.

    If a callback raises an exception, it is passed to the error handler.
    Exceptions in one callback do not affect other callbacks or the publisher.

    Args:
        topic: Topic identifier (uses dot notation, e.g., "user.created")
        data: Message payload (dict[str, Any] with string keys only). Defaults to empty dict if None.
        metadata: Optional metadata dictionary for message context. Defaults to empty dict if None.
        correlation_id: Optional correlation ID override. If None or '', uses self._correlation_id.
                       If '*', raises error. Otherwise must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9]
                       (2-64 chars) with no consecutive '.', '-', or '_' characters.
                       Must be passed as a keyword argument.

    Raises:
        SplurgePubSubValueError: If topic is empty or not a string, or correlation_id is invalid
        SplurgePubSubTypeError: If data is not a dict[str, Any] or has non-string keys
        SplurgePubSubRuntimeError: If the bus is shutdown

    Example:
        >>> bus = PubSub()
        >>> bus.subscribe("order.created", lambda m: print(m.data))
        '...'
        >>> bus.publish("order.created", {"order_id": 42, "total": 99.99})
        >>> bus.publish("order.created", {"order_id": 42}, metadata={"source": "api"})
        >>> bus.publish("order.created", correlation_id="custom-id")
        >>> bus.publish("order.created")  # Empty data and metadata
        >>> bus.drain()  # Wait for messages to be delivered
    """
```

**Error Messages**:
- `"Topic must be a non-empty string, got: <value>"` - Empty or invalid topic
- `"Message data must be dict[str, Any], got: <type>"` - Payload is not a dict
- `"Message data keys must be strings, got key <key> of type <type>"` - Dict has non-string keys
- `"Cannot publish: PubSub has been shutdown"` - Bus is shutdown

##### drain

```python
def drain(self, timeout: int = 2000) -> bool:
    """Wait for the message queue to be drained (empty).

    Blocks until all queued messages have been processed by the worker thread,
    or until the timeout expires.

    Args:
        timeout: Maximum time to wait in milliseconds. Defaults to 2000ms.

    Returns:
        True if queue was drained within timeout, False if timeout expired.

    Example:
        >>> bus = PubSub()
        >>> bus.subscribe("topic", callback)
        >>> bus.publish("topic", {"data": "test"})
        >>> bus.drain()  # Wait for message to be delivered
        True
        >>> bus.drain(timeout=100)  # Wait up to 100ms
    """
```

**Notes**:
- Use `drain()` when you need to ensure messages have been delivered before proceeding
- Returns `True` immediately if queue is already empty
- Returns `True` if shutdown (queue should be empty)
- Useful in tests or when you need synchronous-like behavior

##### unsubscribe

```python
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
        SplurgePubSubValueError: If topic is empty or not a string
        SplurgePubSubLookupError: If subscriber not found for topic

    Example:
        >>> bus = PubSub()
        >>> sub_id = bus.subscribe("topic", callback)
        >>> bus.unsubscribe("topic", sub_id)
    """
```

**Error Messages**:
- `"Topic must be a non-empty string, got: <value>"` - Empty or invalid topic
- `"No subscribers found for topic '<topic>'"` - Topic not in registry
- `"Subscriber '<id>' not found for topic '<topic>'"` - Subscriber not found for topic

##### clear

```python
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
```

##### shutdown

```python
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
```

##### on

```python
def on(self, topic: Topic) -> TopicDecorator:
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
    """
```

#### Properties

```python
@property
def correlation_id(self) -> str:
    """Get the correlation ID for this PubSub instance.
    
    Returns:
        The instance correlation ID (auto-generated if not provided in constructor)
    
    Example:
        >>> bus = PubSub(correlation_id="my-id")
        >>> bus.correlation_id
        'my-id'
    """

@property
def correlation_ids(self) -> set[str]:
    """Get all correlation IDs that have been published.
    
    Returns:
        A copy of the set of all correlation IDs that have been published.
        Includes the instance correlation_id and any correlation_ids used in publish().
    
    Example:
        >>> bus = PubSub(correlation_id="instance-id")
        >>> bus.publish("topic", {}, correlation_id="custom-1")
        >>> bus.correlation_ids
        {'instance-id', 'custom-1'}
    """

@property
def is_shutdown(self) -> bool:
    """Check if the PubSub instance has been shutdown.
    
    Returns:
        True if shutdown() has been called, False otherwise
    
    Example:
        >>> bus = PubSub()
        >>> bus.is_shutdown
        False
        >>> bus.shutdown()
        >>> bus.is_shutdown
        True
    """

@property
def subscribers(self) -> dict[Topic, list[_SubscriberEntry]]:
    """Get all topic-based subscribers.
    
    Returns:
        A copy of the subscribers dictionary, keyed by topic.
        Note: Returns internal _SubscriberEntry objects for inspection only.
    
    Example:
        >>> bus = PubSub()
        >>> bus.subscribe("topic", callback)
        '...'
        >>> len(bus.subscribers.get("topic", []))
        1
    """

@property
def wildcard_subscribers(self) -> list[_SubscriberEntry]:
    """Get all wildcard topic subscribers (topic="*").
    
    Returns:
        A copy of the list of wildcard subscribers.
        Note: Returns internal _SubscriberEntry objects for inspection only.
    
    Example:
        >>> bus = PubSub()
        >>> bus.subscribe("*", callback)
        '...'
        >>> len(bus.wildcard_subscribers)
        1
    """
```

#### Context Manager

```python
def __enter__(self) -> PubSub:
    """Enter context manager."""

def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: Any,
) -> None:
    """Exit context manager and cleanup resources."""

# Usage
with PubSub() as bus:
    bus.subscribe("topic", callback)
    bus.publish("topic", data)
# bus.shutdown() called automatically
```

### Message

Immutable message published to the pub-sub system. **Payloads are validated to be dictionaries with string keys.**

#### Constructor

```python
@dataclass(frozen=True)
class Message:
    """Immutable message published to the pub-sub system.

    Validates that payloads are dictionaries with string keys. Non-dict payloads
    or dicts with non-string keys will raise SplurgePubSubTypeError during construction.

    Args:
        topic: Topic identifier (uses dot notation, e.g., "user.created")
        data: Message payload as dict[str, Any]. Defaults to empty dict if not provided.
              Must be a dictionary with string keys only.
        correlation_id: Optional correlation ID for cross-library event tracking (defaults to None)
        timestamp: Auto-generated UTC timestamp (optional)
        metadata: Metadata dictionary (defaults to empty dict if not provided)

    Raises:
        SplurgePubSubValueError: If topic is empty, starts/ends with dots, or contains ".."
        SplurgePubSubTypeError: If data is not a dict[str, Any] or has non-string keys

    Example:
        >>> msg = Message(topic="user.created", data={"id": 123, "name": "Alice"})
        >>> msg.topic
        'user.created'
        >>> msg.data
        {'id': 123, 'name': 'Alice'}

        >>> # Signal event with no data (data defaults to {})
        >>> msg_signal = Message(topic="signal.event")
        >>> msg_signal.data
        {}

        >>> # Invalid: non-dict payload raises error
        >>> msg = Message(topic="event", data="string_not_allowed")
        SplurgePubSubTypeError: Message data must be dict[str, Any], got: str

        >>> # Invalid: non-string keys raise error
        >>> msg = Message(topic="event", data={1: "one", 2: "two"})
        SplurgePubSubTypeError: Message data keys must be strings, got key 1 of type int
    """

    topic: Topic
    data: MessageData = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### Attributes

- `topic: str` - Topic identifier for message routing
- `data: dict[str, Any]` - Message payload (dictionary with string keys only, defaults to empty dict if not provided)
- `correlation_id: str | None` - Optional correlation ID for cross-library event tracking (defaults to None)
- `timestamp: datetime` - UTC timestamp of message creation (auto-generated)
- `metadata: dict[str, Any]` - Metadata dictionary (defaults to empty dict if not provided)

#### Methods

```python
def __repr__(self) -> str:
    """Return readable representation."""

def __post_init__(self) -> None:
    """Validate message fields after initialization.

    Raises:
        SplurgePubSubValueError: If topic is invalid
    """
```

#### Validation Rules

- Topic must be non-empty string
- Topic cannot contain consecutive dots (..)
- Topic cannot start or end with dot

**Error Messages**:
- `"Topic must be a non-empty string, got: <value>"` - Empty or invalid topic
- `"Topic cannot contain consecutive dots: <topic>"` - Contains ..
- `"Topic cannot start or end with dot: <topic>"` - Starts or ends with dot

#### Example Usage

```python
from splurge_pub_sub import Message
from datetime import datetime, timezone

# Create message with auto-timestamp and optional data
msg1 = Message(topic="user.created", data={"id": 123})

# Create signal message with no data (data defaults to {})
msg_signal = Message(topic="signal.event")

# Create message with custom timestamp
custom_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
msg2 = Message(
    topic="order.placed",
    data={"order_id": "ABC-123"},
    timestamp=custom_time
)

# Create message with metadata
msg3 = Message(
    topic="event.tracked",
    data={"action": "click"},
    metadata={"user_id": 456, "session_id": "xyz"}
)

# Access message properties
print(msg1.topic)       # "user.created"
print(msg1.data)        # {"id": 123}
print(msg1.timestamp)   # datetime object
print(msg1.metadata)    # {}

# Access signal message properties
print(msg_signal.topic) # "signal.event"
print(msg_signal.data)  # {}
print(msg_signal.metadata)  # {}
```

### TopicPattern

Represents a topic pattern with wildcard support.

#### Constructor

```python
@dataclass(frozen=True)
class TopicPattern:
    """Represents a topic pattern with wildcard support.

    Supports wildcard patterns:
    - '*' matches any segment (between dots)
    - '?' matches any single character within a segment
    - Exact matches for literal topics

    Args:
        pattern: Topic pattern string (e.g., "user.created", "user.*")

    Example:
        >>> p = TopicPattern("user.*")
        >>> p.matches("user.created")
        True
        >>> p.matches("order.created")
        False
    """

    pattern: str
```

#### Methods

##### matches

```python
def matches(self, topic: str) -> bool:
    """Check if topic matches this pattern.

    Args:
        topic: Topic string to check

    Returns:
        True if topic matches pattern, False otherwise

    Example:
        >>> pattern = TopicPattern("user.*")
        >>> pattern.matches("user.created")
        True
        >>> pattern.matches("user.updated")
        True
        >>> pattern.matches("order.created")
        False
    """
```

#### Properties

##### is_exact

```python
@property
def is_exact(self) -> bool:
    """Whether this is an exact match pattern (no wildcards).

    Returns:
        True if pattern contains no wildcards

    Example:
        >>> TopicPattern("user.created").is_exact
        True
        >>> TopicPattern("user.*").is_exact
        False
    """
```

#### Validation Rules

- Pattern cannot be empty
- Pattern cannot start or end with dot
- Pattern cannot contain consecutive dots (..)
- Pattern can only contain: alphanumeric, dots, dashes, *, ?

**Error Messages**:
- `"Pattern cannot be empty"` - Empty pattern
- `"Pattern cannot start or end with dot"` - Starts/ends with dot
- `"Pattern cannot contain consecutive dots"` - Contains ..
- `"Pattern contains invalid character: <char>"` - Invalid character

#### Example Usage

```python
from splurge_pub_sub import TopicPattern

# Exact match
exact = TopicPattern("user.created")
assert exact.matches("user.created") == True
assert exact.matches("user.updated") == False
assert exact.is_exact == True

# Wildcard *
wildcard = TopicPattern("user.*")
assert wildcard.matches("user.created") == True
assert wildcard.matches("user.updated") == True
assert wildcard.matches("user.a.created") == False  # * matches one segment only
assert wildcard.is_exact == False

# Wildcard ?
single_char = TopicPattern("user.?.created")
assert single_char.matches("user.a.created") == True
assert single_char.matches("user.ab.created") == False
assert single_char.is_exact == False

# Complex patterns
complex_pattern = TopicPattern("*.order.*")
assert complex_pattern.matches("user.order.created") == True
assert complex_pattern.matches("admin.order.cancelled") == True
assert complex_pattern.matches("user.created") == False
```

### TopicDecorator

Decorator for registering topic subscriptions.

#### Constructor

```python
class TopicDecorator:
    """Decorator for registering topic subscriptions.

    This is returned by PubSub.on() and is used with @bus.on() syntax
    to register callback functions for topics.

    Args:
        pubsub: The PubSub instance
        topic: The topic to subscribe to
        pattern: Whether to use pattern matching (future feature)
    """

    def __init__(
        self,
        pubsub: PubSub,
        topic: Topic,
        pattern: bool = False,
    ) -> None:
        """Initialize decorator."""
```

#### Methods

##### __call__

```python
def __call__(self, callback: Callback) -> Callback:
    """Register callback as subscriber and return it.

    Args:
        callback: The callback function to register

    Returns:
        The original callback (allowing chaining)

    Example:
        >>> @bus.on("topic")
        ... def handler(msg: Message) -> None:
        ...     pass
    """
```

#### Example Usage

```python
from splurge_pub_sub import PubSub, Message

bus = PubSub()

# Use as decorator
@bus.on("user.created")
def handle_user_created(msg: Message) -> None:
    print(f"User created: {msg.data['name']}")

@bus.on("user.updated")
def handle_user_updated(msg: Message) -> None:
    print(f"User updated: {msg.data['name']}")

# Decorators return the original function
assert callable(handle_user_created)
assert callable(handle_user_updated)

# Publish events
bus.publish("user.created", {"name": "Alice"})
bus.publish("user.updated", {"name": "Alice Smith"})
```

### PubSubAggregator

Composite class for aggregating messages from multiple `PubSub` instances.

#### Constructor

```python
class PubSubAggregator:
    def __init__(
        self,
        *,
        pubsubs: Sequence[PubSub] | None = None,
        error_handler: ErrorHandler | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize a new PubSubAggregator instance.

        Creates an internal PubSub instance for managing subscribers and
        optionally subscribes to the provided PubSub instances.

        Args:
            pubsubs: Optional list of PubSub instances to subscribe to.
                   Defaults to empty list. Must be passed as a keyword argument.
            error_handler: Optional custom error handler for subscriber callbacks.
                          Passed to internal PubSub instance. Must be passed as a keyword argument.
            correlation_id: Optional correlation ID. Passed to internal PubSub instance.
                           Must be passed as a keyword argument.

        Example:
            >>> bus_b = PubSub()
            >>> bus_c = PubSub()
            >>> aggregator = PubSubAggregator(pubsubs=[bus_b, bus_c])
            >>> aggregator = PubSubAggregator()  # Empty, add later with add_pubsub()
        """
```

#### Methods

##### add_pubsub

```python
def add_pubsub(self, pubsub: PubSub) -> None:
    """Add a PubSub instance to the aggregator.

    Subscribes to all topics ("*") on the provided PubSub instance and
    forwards all messages to PubSubAggregator subscribers.

    Args:
        pubsub: PubSub instance to add

    Raises:
        SplurgePubSubValueError: If pubsub is None or not a PubSub instance
        SplurgePubSubRuntimeError: If PubSubAggregator is shutdown
        SplurgePubSubRuntimeError: If pubsub is already managed

    Example:
        >>> aggregator = PubSubAggregator()
        >>> bus_b = PubSub()
        >>> aggregator.add_pubsub(bus_b)
    """
```

##### remove_pubsub

```python
def remove_pubsub(self, pubsub: PubSub) -> None:
    """Remove a PubSub instance from the aggregator.

    Unsubscribes from the provided PubSub instance and stops forwarding
    its messages.

    Args:
        pubsub: PubSub instance to remove

    Raises:
        SplurgePubSubValueError: If pubsub is None
        SplurgePubSubLookupError: If pubsub is not managed by this PubSubAggregator

    Example:
        >>> aggregator = PubSubAggregator(pubsubs=[bus_b])
        >>> aggregator.remove_pubsub(bus_b)
    """
```

##### subscribe

```python
def subscribe(
    self,
    topic: str,
    callback: Callback,
    *,
    correlation_id: str | None = None,
) -> SubscriberId:
    """Subscribe to a topic on the aggregator bus.

    Messages from any managed PubSub instance matching the topic will be
    delivered to the callback.

    Args:
        topic: Topic identifier (uses dot notation, e.g., "user.created") or "*" for all topics
        callback: Callable that accepts a Message and returns None
        correlation_id: Optional filter. If None or '', uses instance correlation_id.
                       If '*', matches any correlation_id. Otherwise must match pattern
                       [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9] (2-64 chars) with no consecutive '.', '-', or '_'.
                       Must be passed as a keyword argument.

    Returns:
        SubscriberId: Unique identifier for this subscription

    Raises:
        SplurgePubSubRuntimeError: If PubSubAggregator is shutdown

    Example:
        >>> aggregator = PubSubAggregator(pubsubs=[bus_b, bus_c])
        >>> def handler(msg: Message) -> None:
        ...     print(f"Received: {msg.topic}")
        >>> sub_id = aggregator.subscribe("user.created", handler, correlation_id="*")
    """
```

**Note**: When subscribing to receive messages from managed PubSub instances, use `correlation_id="*"` to receive all messages regardless of their correlation_id.

##### publish

```python
def publish(
    self,
    topic: str,
    data: MessageData | None = None,
    metadata: Metadata | None = None,
    *,
    correlation_id: str | None = None,
) -> None:
    """Publish a message to the aggregator bus.

    Note: This publishes to the internal bus only. It does NOT publish to
    managed PubSub instances. This is a one-way message flow from managed
    instances to aggregator subscribers.

    Args:
        topic: Topic identifier (uses dot notation, e.g., "user.created")
        data: Message payload (dict[str, Any] with string keys only). Defaults to empty dict if None.
        metadata: Optional metadata dictionary for message context. Defaults to empty dict if None.
        correlation_id: Optional correlation ID override. If None or '', uses self._correlation_id.
                       If '*', raises error. Otherwise must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9]
                       (2-64 chars) with no consecutive '.', '-', or '_' characters.
                       Must be passed as a keyword argument.

    Raises:
        SplurgePubSubRuntimeError: If PubSubAggregator is shutdown

    Example:
        >>> aggregator = PubSubAggregator()
        >>> aggregator.subscribe("topic", callback)
        >>> aggregator.publish("topic", {"data": "test"})
        >>> aggregator.drain()
    """
```

##### drain

```python
def drain(self, timeout: int = 2000, *, cascade: bool = False) -> bool:
    """Wait for the message queue to be drained (empty).

    Blocks until all queued messages have been processed, or until the
    timeout expires. Optionally cascades drain to managed PubSub instances.

    Args:
        timeout: Maximum time to wait in milliseconds. Defaults to 2000ms.
        cascade: If True, also calls drain() on all managed PubSub instances.
                Defaults to False. Must be passed as a keyword argument.

    Returns:
        True if queue was drained within timeout, False if timeout expired.
        If cascade=True, returns True only if all drains succeeded.

    Example:
        >>> aggregator = PubSubAggregator(pubsubs=[bus_b, bus_c])
        >>> aggregator.publish("topic", {"data": "test"})
        >>> aggregator.drain()  # Wait for internal bus only
        True
        >>> aggregator.drain(cascade=True)  # Wait for internal and managed buses
        True
    """
```

##### shutdown

```python
def shutdown(self, *, cascade: bool = False) -> None:
    """Shutdown the aggregator bus and prevent further operations.

    Signals shutdown and optionally cascades shutdown to managed PubSub
    instances. Subsequent calls to subscribe() or publish() will raise
    SplurgePubSubRuntimeError.

    Args:
        cascade: If True, also calls shutdown() on all managed PubSub instances.
                Defaults to False. Must be passed as a keyword argument.

    Safe to call multiple times (idempotent).

    Example:
        >>> aggregator = PubSubAggregator(pubsubs=[bus_b, bus_c])
        >>> aggregator.shutdown()  # Shutdown internal bus only
        >>> aggregator = PubSubAggregator(pubsubs=[bus_b, bus_c])
        >>> aggregator.shutdown(cascade=True)  # Shutdown internal and managed buses
    """
```

#### Properties

```python
@property
def is_shutdown(self) -> bool:
    """Check if the PubSubAggregator instance has been shutdown.

    Returns:
        True if shutdown() has been called, False otherwise

    Example:
        >>> aggregator = PubSubAggregator()
        >>> aggregator.is_shutdown
        False
        >>> aggregator.shutdown()
        >>> aggregator.is_shutdown
        True
    """

@property
def managed_pubsubs(self) -> list[PubSub]:
    """Get list of managed PubSub instances.

    Returns:
        A copy of the list of managed PubSub instances.

    Example:
        >>> aggregator = PubSubAggregator(pubsubs=[bus_b, bus_c])
        >>> len(aggregator.managed_pubsubs)
        2
    """
```

#### Context Manager Support

`PubSubAggregator` supports the context manager protocol:

```python
with PubSubAggregator(pubsubs=[bus_b, bus_c]) as aggregator:
    aggregator.subscribe("topic", callback)
    # Resources cleaned up automatically on exit
```

#### Message Flow

**One-Way Flow**: `PubSubAggregator` implements one-way message flow:
- ✅ Messages published to managed `PubSub` instances → forwarded to aggregator subscribers
- ❌ Messages published to aggregator → NOT forwarded to managed `PubSub` instances

#### Lifecycle Management

Managed `PubSub` instances are created and managed externally. `PubSubAggregator` only subscribes to them and forwards their messages. When `shutdown(cascade=False)` is called (the default), managed instances remain active and can continue to be used independently.

### PubSubSolo

Scoped singleton wrapper for `PubSub` instances. Provides thread-safe singleton instances per scope name, enabling multiple packages/libraries to each have their own singleton that can be aggregated via `PubSubAggregator`.

#### Class Methods

##### get_instance

```python
@classmethod
def get_instance(
    *,
    scope: str,
    error_handler: ErrorHandler | None = None,
    correlation_id: str | None = None,
) -> PubSub:
    """Get or create the singleton PubSub instance for a scope.

    Args:
        scope: Scope name for the singleton (e.g., package name, module name).
              Each scope gets its own singleton instance. Must be passed as a keyword argument.
        error_handler: Optional error handler (only applied on first initialization).
                      Must be passed as a keyword argument.
        correlation_id: Optional correlation ID (only applied on first initialization).
                       Must be passed as a keyword argument.

    Returns:
        The singleton PubSub instance for the specified scope

    Example:
        >>> # Package A
        >>> bus_a = PubSubSolo.get_instance(scope="package_a")

        >>> # Package B
        >>> bus_b = PubSubSolo.get_instance(scope="package_b")

        >>> # bus_a and bus_b are different instances
        >>> bus_a is not bus_b  # True

        >>> # But same scope returns same instance
        >>> bus_a2 = PubSubSolo.get_instance(scope="package_a")
        >>> bus_a is bus_a2  # True
    """
```

**Important**: Configuration parameters (`error_handler`, `correlation_id`) are only applied on the first call for a scope. Subsequent calls with different parameters are ignored.

##### is_initialized

```python
@classmethod
def is_initialized(scope: str) -> bool:
    """Check if the singleton has been initialized for a scope.

    Args:
        scope: Scope name to check

    Returns:
        True if singleton has been created for the scope, False otherwise
    """
```

##### get_all_scopes

```python
@classmethod
def get_all_scopes() -> list[str]:
    """Get list of all initialized scope names.

    Returns:
        List of scope names that have been initialized

    Example:
        >>> PubSubSolo.get_instance(scope="package_a")
        >>> PubSubSolo.get_instance(scope="package_b")
        >>> PubSubSolo.get_all_scopes()
        ['package_a', 'package_b']
    """
```

#### Convenience Methods

`PubSubSolo` provides convenience class methods that delegate to the singleton instance for a specific scope. All methods require a `scope` parameter:

- `subscribe(topic, callback, *, scope, correlation_id=None)` - Subscribe to a topic
- `publish(topic, data=None, metadata=None, *, scope, correlation_id=None)` - Publish a message
- `unsubscribe(topic, subscriber_id, *, scope)` - Unsubscribe from a topic
- `clear(topic=None, *, scope)` - Clear subscribers
- `drain(timeout=2000, *, scope)` - Drain message queue
- `shutdown(*, scope)` - Shutdown the singleton instance
- `on(topic, *, scope)` - Create a decorator for subscribing

#### Property Access Methods

Since properties require an instance, `PubSubSolo` provides class methods to access properties:

- `get_correlation_id(*, scope)` - Get correlation ID
- `get_correlation_ids(*, scope)` - Get all correlation IDs
- `get_is_shutdown(*, scope)` - Check if shutdown
- `get_subscribers(*, scope)` - Get subscribers
- `get_wildcard_subscribers(*, scope)` - Get wildcard subscribers

#### Usage with PubSubAggregator

`PubSubSolo` is designed to work seamlessly with `PubSubAggregator`:

```python
from splurge_pub_sub import PubSubSolo, PubSubAggregator

# Each package gets its own singleton
bus_a = PubSubSolo.get_instance(scope="package_a")
bus_b = PubSubSolo.get_instance(scope="package_b")
bus_c = PubSubSolo.get_instance(scope="package_c")

# Aggregate them - each is a different instance!
aggregator = PubSubAggregator(pubsubs=[bus_a, bus_b, bus_c])

# Subscribe to events from all packages
@aggregator.on("*")
def handle_all_events(msg: Message) -> None:
    print(f"Received from {msg.topic}: {msg.data}")

# Events from both packages will be received
bus_a.publish("package_a.event", {"id": 1})
bus_b.publish("package_b.event", {"id": 2})
bus_c.publish("package_c.event", {"id": 3})
aggregator.drain()
```

#### Thread Safety

Instance creation is thread-safe using per-scope locks with double-check locking pattern. Multiple threads can safely call `get_instance()` with the same scope and will receive the same instance.

#### Direct Instantiation

`PubSubSolo` cannot be instantiated directly. Attempting to do so will raise `RuntimeError`:

```python
>>> PubSubSolo()  # Raises RuntimeError
RuntimeError: PubSubSolo cannot be instantiated directly. Use PubSubSolo.get_instance(scope='...') instead.
```

## Type Aliases

### Callback

```python
Callback = Callable[[Message], None]
```

Type alias for callback functions used in subscriptions.

**Example**:
```python
def my_callback(msg: Message) -> None:
    print(msg.data)

bus.subscribe("topic", my_callback)
```

### ErrorHandler

```python
ErrorHandler = Callable[[Exception, str], None]
```

Type alias for custom error handler functions.

**Parameters**:
- `exception: Exception` - The exception raised by a subscriber callback
- `topic: str` - The topic where the error occurred

**Example**:
```python
def my_error_handler(exc: Exception, topic: str) -> None:
    logger.error(f"Error on {topic}: {exc}")

bus = PubSub(error_handler=my_error_handler)
```

### MessageData

```python
MessageData = dict[str, Any]
```

Type alias for message payload data. **Messages require payloads to be dictionaries with string keys.**

All keys in the payload dictionary must be strings. Values can be any JSON-serializable type
(str, int, float, bool, None, list, dict, etc.).

**Valid Examples**:
```python
# Simple dictionary
{"user_id": 123, "action": "created"}

# Nested dictionaries
{"user": {"id": 123, "name": "Alice"}, "timestamp": "2025-01-01T00:00:00Z"}

# Mixed value types
{"id": 123, "name": "Alice", "active": True, "balance": 99.99, "tags": ["admin", "verified"]}

# Empty dictionary
{}
```

**Invalid Examples** (will raise `SplurgePubSubTypeError`):
```python
"user_created"                    # ✗ String instead of dict
123                               # ✗ Integer instead of dict
["event1", "event2"]              # ✗ List instead of dict
None                              # ✗ None instead of dict
{1: "one", 2: "two"}             # ✗ Non-string keys
{(1, 2): "tuple_key"}            # ✗ Tuple key (not string)
```

**Raises**: `SplurgePubSubTypeError` if payload is not a dict with string keys

### Metadata

```python
Metadata = dict[str, Any]
```

Type alias for message metadata dictionary. **Optional metadata attached to messages for passing additional context.**

Metadata provides a mechanism to attach correlation IDs, source information, request IDs, or other message-related context
that isn't part of the main payload. Defaults to an empty dictionary if not provided.

**Valid Examples**:
```python
# Correlation tracking
{"request_id": "abc-123", "user_id": "user-456"}

# Source information
{"source": "api", "version": "v2"}

# Request-reply pattern
{"request_id": "req-123", "reply_topic": "orders.reply"}

# Empty metadata
{}
```

**Usage**:
```python
# Publish with metadata
bus.publish("topic", {"key": "value"}, metadata={"source": "api"})

# Access metadata in subscriber
@bus.on("topic")
def handler(msg: Message) -> None:
    source = msg.metadata.get("source")  # Safely access metadata
    request_id = msg.metadata.get("request_id")

# Metadata is always a dict (never None)
assert isinstance(msg.metadata, dict)
```

### Topic

```python
Topic = str
```

Type alias for topic identifiers.

### SubscriberId

```python
SubscriberId = str
```

Type alias for subscription identifiers (UUID strings).

## Exception Classes

All exceptions inherit from `SplurgePubSubError`.

### SplurgePubSubError

Base exception for all framework errors.

```python
class SplurgePubSubError(Exception):
    """Base exception for all Splurge Pub-Sub framework errors."""
    pass
```

**Usage**:
```python
from splurge_pub_sub import SplurgePubSubError

try:
    bus.subscribe("topic", callback)
except SplurgePubSubError as e:
    print(f"Pub-Sub error: {e}")
```

### SplurgePubSubValueError

Raised when an invalid value is provided.

Inherits from: `SplurgePubSubError`, `ValueError`

**Common Cases**:
- Topic is empty string
- Topic contains invalid characters
- Required parameter is None
- Pattern validation fails

**Example**:
```python
from splurge_pub_sub import SplurgePubSubValueError

try:
    bus.subscribe("", callback)  # Empty topic
except SplurgePubSubValueError as e:
    print(f"Invalid value: {e}")
```

### SplurgePubSubTypeError

Raised when a parameter has incorrect type.

Inherits from: `SplurgePubSubError`, `TypeError`

**Common Cases**:
- Callback is not callable
- Topic is not a string
- Data type validation fails

**Example**:
```python
from splurge_pub_sub import SplurgePubSubTypeError

try:
    bus.subscribe("topic", "not_a_function")
except SplurgePubSubTypeError as e:
    print(f"Type error: {e}")
```

### SplurgePubSubLookupError

Raised when a resource is not found.

Inherits from: `SplurgePubSubError`, `LookupError`

**Common Cases**:
- Attempting to unsubscribe with invalid subscriber ID
- Attempting to access non-existent topic

**Example**:
```python
from splurge_pub_sub import SplurgePubSubLookupError

try:
    bus.unsubscribe("topic", "invalid-id")
except SplurgePubSubLookupError as e:
    print(f"Not found: {e}")
```

### SplurgePubSubRuntimeError

Raised when a runtime error occurs during operations.

Inherits from: `SplurgePubSubError`, `RuntimeError`

**Common Cases**:
- Attempting to subscribe/publish after shutdown
- Internal state corruption
- Lock acquisition timeout

**Example**:
```python
from splurge_pub_sub import SplurgePubSubRuntimeError

try:
    bus.shutdown()
    bus.subscribe("topic", callback)
except SplurgePubSubRuntimeError as e:
    print(f"Runtime error: {e}")
```

### SplurgePubSubOSError

Raised when an OS-level error occurs.

Inherits from: `SplurgePubSubError`, `OSError`

**Common Cases**:
- Thread creation failures
- Resource allocation failures
- System-level synchronization errors

**Example**:
```python
from splurge_pub_sub import SplurgePubSubOSError

try:
    # Internal framework operations
    pass
except SplurgePubSubOSError as e:
    print(f"OS error: {e}")
```

### SplurgePubSubPatternError

Raised when a topic pattern is invalid.

Inherits from: `SplurgePubSubError`, `ValueError`

**Common Cases**:
- Pattern is empty string
- Pattern starts or ends with dot
- Pattern contains consecutive dots
- Pattern contains invalid characters

**Example**:
```python
from splurge_pub_sub import SplurgePubSubPatternError

try:
    pattern = TopicPattern(".invalid")  # Leading dot
except SplurgePubSubPatternError as e:
    print(f"Invalid pattern: {e}")
```

## Functions

### default_error_handler

```python
def default_error_handler(exc: Exception, topic: str) -> None:
    """Default error handler that logs errors.

    Args:
        exc: The exception that occurred
        topic: The topic where the error occurred

    Example:
        >>> exc = ValueError("test")
        >>> default_error_handler(exc, "user.created")
        # Logs: ERROR:splurge_pub_sub.core.errors:Error in subscriber callback for topic 'user.created': ValueError: test
    """
```

This is the default error handler used if no custom handler is provided. It logs errors at ERROR level with exception info.

**Usage**:
```python
from splurge_pub_sub import default_error_handler

# Explicitly use default handler
bus = PubSub(error_handler=default_error_handler)

# Or rely on it being the default
bus = PubSub()  # Uses default_error_handler automatically
```

### generate_correlation_id

```python
def generate_correlation_id() -> str:
    """Generate a pattern-compliant, unique correlation ID.

    Returns:
        A UUID string that matches the correlation ID pattern.
        Format: [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9] (2-64 chars)

    Example:
        >>> correlation_id = generate_correlation_id()
        >>> len(correlation_id)
        36
        >>> correlation_id.startswith('') or correlation_id.startswith('')  # alphanumeric
        True
    """
```

Generates a unique, pattern-compliant correlation ID for cross-library event tracking and coordination.

**Usage**:
```python
from splurge_pub_sub import generate_correlation_id, PubSub

# Generate unique correlation ID
correlation_id = generate_correlation_id()

# Use with PubSub instance
bus = PubSub(correlation_id=correlation_id)

# Or pass to publish
bus.publish("topic", {"data": "value"}, correlation_id=correlation_id)
```

### validate_correlation_id

```python
def validate_correlation_id(correlation_id: str) -> None:
    """Validate the format of a correlation ID.

    Args:
        correlation_id: The correlation ID to validate.

    Raises:
        SplurgePubSubValueError: If the correlation ID is not pattern-compliant.
            - Empty string raises: "correlation_id cannot be empty string, use None instead"
            - Wildcard '*' raises: "correlation_id cannot be '*' (wildcard), must be a specific value"
            - Invalid length raises: "correlation_id length must be 1-64 chars, got X"
            - Invalid pattern raises: "correlation_id must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9] (2-64 chars), got: ..."
            - Consecutive separators raise: "correlation_id cannot contain consecutive separator characters ('.', '-', '_'), got: ..."

    Pattern Requirements:
        - Format: [a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9] (2-64 chars)
        - Must start with alphanumeric character
        - Must end with alphanumeric character
        - Middle characters can be alphanumeric, dots, hyphens, or underscores
        - Cannot have consecutive separator characters (., -, _)
        - Cannot be empty string or wildcard '*'

    Example:
        >>> from splurge_pub_sub import validate_correlation_id
        >>> validate_correlation_id("workflow-abc-123")  # Valid
        >>> validate_correlation_id("request.id.12345")  # Valid
        >>> validate_correlation_id("-invalid")  # Raises SplurgePubSubValueError
        >>> validate_correlation_id("invalid-")  # Raises SplurgePubSubValueError
    """
```

Validates that a correlation ID matches the required pattern for the framework.

**Valid Examples**:
```python
validate_correlation_id("workflow-abc-123")      # Valid
validate_correlation_id("request.id.12345")      # Valid
validate_correlation_id("a1b2c3")                # Valid (short but valid)
validate_correlation_id("correlation_id_xyz")    # Valid
```

**Invalid Examples**:
```python
validate_correlation_id("")                      # Raises - empty string
validate_correlation_id("*")                     # Raises - wildcard
validate_correlation_id("-invalid")              # Raises - starts with separator
validate_correlation_id("invalid-")              # Raises - ends with separator
validate_correlation_id("invalid..name")         # Raises - consecutive separators
validate_correlation_id("invalid--name")         # Raises - consecutive separators
validate_correlation_id("a")                     # Raises - too short (min 2 chars)
```

### is_valid_correlation_id

```python
def is_valid_correlation_id(correlation_id: str) -> bool:
    """Check if a correlation ID is valid without raising exceptions.

    Args:
        correlation_id: The correlation ID to check.

    Returns:
        True if valid, False otherwise.

    Example:
        >>> from splurge_pub_sub import is_valid_correlation_id
        >>> is_valid_correlation_id("workflow-abc-123")
        True
        >>> is_valid_correlation_id("-invalid")
        False
        >>> is_valid_correlation_id("")
        False
    """
```

Safe validation function that returns a boolean instead of raising exceptions.

**Usage**:
```python
from splurge_pub_sub import is_valid_correlation_id

if is_valid_correlation_id(user_input):
    bus = PubSub(correlation_id=user_input)
else:
    print("Invalid correlation ID format")
```

## Examples

### Basic Pub-Sub

```python
from splurge_pub_sub import PubSub, Message

# Create bus
bus = PubSub()

# Define subscriber
def on_user_created(msg: Message) -> None:
    print(f"User created: {msg.data['name']}")

# Subscribe
sub_id = bus.subscribe("user.created", on_user_created)

# Publish
bus.publish("user.created", {"id": 1, "name": "Alice"})

# Unsubscribe
bus.unsubscribe("user.created", sub_id)
```

### Correlation ID for Cross-Library Coordination

```python
from splurge_pub_sub import PubSub, Message

# Create multiple PubSub instances with same correlation_id
correlation_id = "workflow-abc-123"

# Library A's PubSub instance
dsv_bus = PubSub(correlation_id=correlation_id)

# Library B's PubSub instance
tabular_bus = PubSub(correlation_id=correlation_id)

# Monitor all events with same correlation_id
monitor_bus = PubSub()

def monitor_all(msg: Message) -> None:
    print(f"[{msg.correlation_id}] {msg.topic}: {msg.data}")

# Subscribe to all topics with specific correlation_id
monitor_bus.subscribe("*", monitor_all, correlation_id=correlation_id)

# Publish from different libraries
dsv_bus.publish("dsv.file.loaded", {"file": "data.csv"})
tabular_bus.publish("tabular.table.created", {"rows": 100})

# Both messages received by monitor (same correlation_id)
```

### Correlation ID Filtering

```python
from splurge_pub_sub import PubSub

bus = PubSub(correlation_id="default-id")

# Subscribe with specific correlation_id filter
def handle_id_a(msg: Message) -> None:
    print(f"ID-A: {msg.data}")

def handle_id_b(msg: Message) -> None:
    print(f"ID-B: {msg.data}")

def handle_any(msg: Message) -> None:
    print(f"Any: {msg.data}")

bus.subscribe("test.topic", handle_id_a, correlation_id="id-a")
bus.subscribe("test.topic", handle_id_b, correlation_id="id-b")
bus.subscribe("test.topic", handle_any, correlation_id="*")  # Wildcard matches any

# Publish with different correlation_ids
bus.publish("test.topic", {"data": "1"}, correlation_id="id-a")  # Only handle_id_a and handle_any
bus.publish("test.topic", {"data": "2"}, correlation_id="id-b")  # Only handle_id_b and handle_any
bus.publish("test.topic", {"data": "3"}, correlation_id="id-c")  # Only handle_any
```

### With Decorator

```python
from splurge_pub_sub import PubSub, Message

bus = PubSub()

@bus.on("user.created")
def on_user_created(msg: Message) -> None:
    print(f"User created: {msg.data['name']}")

@bus.on("user.updated")
def on_user_updated(msg: Message) -> None:
    print(f"User updated: {msg.data['name']}")

bus.publish("user.created", {"id": 1, "name": "Alice"})
bus.publish("user.updated", {"id": 1, "name": "Alice Smith"})
```

### With Custom Error Handler

```python
from splurge_pub_sub import PubSub, Message
import logging

logger = logging.getLogger(__name__)

def error_handler(exc: Exception, topic: str) -> None:
    logger.error(f"Error on {topic}: {exc}", exc_info=exc)

bus = PubSub(error_handler=error_handler)

@bus.on("operation")
def risky_operation(msg: Message) -> None:
    raise ValueError("Something went wrong!")

bus.publish("operation", {})  # Error handled gracefully
```

### With Topic Patterns

```python
from splurge_pub_sub import PubSub, TopicPattern

bus = PubSub()

# Create patterns
user_pattern = TopicPattern("user.*")
order_pattern = TopicPattern("order.*")

# Test matching
assert user_pattern.matches("user.created")
assert order_pattern.matches("order.placed")
assert not user_pattern.matches("order.created")
```

### Context Manager

```python
from splurge_pub_sub import PubSub, Message

with PubSub() as bus:
    def callback(msg: Message) -> None:
        print(msg.data)

    bus.subscribe("topic", callback)
    bus.publish("topic", {"key": "value"})
# Cleanup automatic
```

## Related Documentation

- **[README-DETAILS.md](../README-DETAILS.md)** - Comprehensive developer's guide
- **[CLI-REFERENCE.md](../cli/CLI-REFERENCE.md)** - Command-line interface
- **[README.md](../../README.md)** - Project overview
- **[CHANGELOG.md](../../CHANGELOG.md)** - Version history
