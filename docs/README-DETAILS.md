# Splurge Pub-Sub - Comprehensive Developer's Guide

A lightweight, thread-safe publish-subscribe framework for Python applications. This guide provides detailed information about features, architecture, usage patterns, and error handling.

## Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [Installation & Setup](#installation--setup)
4. [Architecture](#architecture)
5. [Phase 1: Core Pub-Sub](#phase-1-core-pub-sub)
6. [Phase 2: Advanced Features](#phase-2-advanced-features)
7. [Error Handling](#error-handling)
8. [Common Patterns](#common-patterns)
9. [Thread Safety](#thread-safety)
10. [Performance Considerations](#performance-considerations)
11. [Related Documentation](#related-documentation)

## Overview

Splurge Pub-Sub is a simple, Pythonic framework for implementing the publish-subscribe pattern in Python applications. It enables decoupled, event-driven communication between components within a single Python process.

### Key Characteristics

- **Zero Dependencies**: No external library requirements
- **Thread-Safe**: Full support for concurrent operations
- **Type-Safe**: Complete type annotations for IDE support and type checking
- **Lightweight**: Minimal overhead, fast operation
- **Production-Ready**: 100% test coverage, comprehensive error handling
- **Extensible**: Custom error handlers and future filtering capabilities

### Use Cases

- Event-driven architecture patterns
- Decoupling application components
- Building plugin systems
- Implementing pub-sub within monolithic applications
- Testing event-driven code
- Message broadcasting within a process

## Core Features

### Phase 1: Core Pub-Sub (Implemented)

- **Subscribe**: Register callbacks for topics
- **Publish**: Send messages to subscribers (asynchronous, non-blocking)
- **Drain**: Wait for queued messages to be processed
- **Unsubscribe**: Remove subscriptions
- **Clear**: Remove all subscribers from topics
- **Shutdown**: Gracefully shutdown the bus
- **Context Manager**: Resource cleanup support

### Phase 2: Advanced Features (Implemented)

- **Decorator API**: Simplified `@bus.on()` syntax
- **Error Handling**: Custom error handler callbacks
- **Topic Filtering**: Wildcard pattern matching for topics

## Installation & Setup

### Installation

```bash
pip install splurge-pub-sub
```

### Import Styles

#### Import Everything at Once

```python
from splurge_pub_sub import (
    PubSub,
    Message,
    TopicPattern,
    ErrorHandler,
    default_error_handler,
)
```

#### Import Selectively

```python
from splurge_pub_sub import PubSub, Message
```

#### Import from Core Directly

```python
from splurge_pub_sub.core import PubSub, Message
from splurge_pub_sub.core.filters import TopicPattern
from splurge_pub_sub.core.errors import ErrorHandler, default_error_handler
```

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────┐
│         Application Code                    │
├─────────────────────────────────────────────┤
│  Subscribers  │  Publishers  │  Decorators  │
├─────────────────────────────────────────────┤
│              PubSub Bus                     │
│  • Subscription Registry (thread-safe)      │
│  • Message Routing                          │
│  • Error Handling                           │
├─────────────────────────────────────────────┤
│  Core Components                            │
│  • Message (data structure)                 │
│  • TopicPattern (filtering)                 │
│  • ErrorHandler (error management)          │
│  • Exceptions (error types)                 │
└─────────────────────────────────────────────┘
```

### Module Organization

```
splurge_pub_sub/
├── core/
│   ├── pubsub.py          # Main PubSub class
│   ├── message.py         # Message data structure
│   ├── types.py           # Type aliases
│   ├── constants.py       # Module constants
│   ├── exceptions.py      # Exception hierarchy
│   ├── filters.py         # Topic pattern matching (Phase 2)
│   ├── errors.py          # Error handler system (Phase 2)
│   ├── decorators.py      # Decorator API (Phase 2)
│   └── __init__.py        # Core module exports
├── cli.py                 # Command-line interface
├── __main__.py            # Module entry point
└── __init__.py            # Public API exports
```

## Phase 1: Core Pub-Sub

The foundation for all pub-sub functionality. Provides basic subscribe, publish, unsubscribe operations with full thread safety.

### Creating a Bus

```python
from splurge_pub_sub import PubSub

# Create a new pub-sub bus
bus = PubSub()
```

With custom error handler:

```python
def my_error_handler(exc: Exception, topic: str) -> None:
    logger.error(f"Error on {topic}: {exc}", exc_info=exc)

bus = PubSub(error_handler=my_error_handler)
```

### Basic Subscription

```python
from splurge_pub_sub import Message

def on_user_created(msg: Message) -> None:
    """Handle user.created events."""
    user_data = msg.data
    print(f"User created: {user_data}")

# Subscribe to a topic
subscriber_id = bus.subscribe("user.created", on_user_created)
```

### Publishing Messages

```python
# Publish a message (non-blocking, returns immediately)
bus.publish("user.created", {
    "id": 123,
    "name": "Alice",
    "email": "alice@example.com"
})

# Wait for messages to be delivered (optional)
bus.drain()  # Waits up to 2000ms by default
bus.drain(timeout=5000)  # Wait up to 5000ms
```

**Note**: `publish()` returns immediately after enqueueing the message. Messages are dispatched asynchronously by a background worker thread. Use `drain()` if you need to wait for delivery.

### Unsubscribing

```python
# Unsubscribe from a topic
bus.unsubscribe("user.created", subscriber_id)

# Clear all subscribers from a specific topic
bus.clear("user.created")

# Clear all subscribers from all topics
bus.clear()
```

### Shutdown

```python
# Shutdown the bus (idempotent, safe to call multiple times)
bus.shutdown()

# After shutdown, subscribe/publish will raise SplurgePubSubRuntimeError
```

### Context Manager

```python
# Automatic cleanup
with PubSub() as bus:
    bus.subscribe("topic", callback)
    bus.publish("topic", data)
# bus.shutdown() called automatically
```

### Message Structure

Messages are immutable frozen dataclasses with the following attributes:

```python
msg.topic        # str - Topic identifier
msg.data         # dict[str, Any] - Message payload (defaults to empty dict if not provided)
msg.timestamp    # datetime - UTC timestamp (auto-generated)
msg.metadata     # dict[str, Any] - Metadata dictionary (defaults to empty dict)
```

**Important**: Message payloads must be dictionaries with string keys. Non-dict payloads or dicts with non-string keys will raise `SplurgePubSubTypeError`.

Example:

```python
def handle_event(msg: Message) -> None:
    print(f"Topic: {msg.topic}")
    print(f"Data: {msg.data}")
    print(f"Timestamp: {msg.timestamp}")
    print(f"Metadata: {msg.metadata}")

bus.subscribe("order.created", handle_event)

# Valid: dict with string keys
bus.publish("order.created", {
    "order_id": "ORD-001",
    "total": 99.99,
    "items": ["item1", "item2"],
    "customer": {"name": "Alice", "email": "alice@example.com"}
})

# Invalid examples (all raise SplurgePubSubTypeError):
bus.publish("event", "string")              # ✗ String instead of dict
bus.publish("event", 123)                   # ✗ Integer instead of dict
bus.publish("event", ["a", "b"])            # ✗ List instead of dict
bus.publish("event", {1: "one", 2: "two"}) # ✗ Non-string keys

# Valid examples with optional data and metadata:
bus.publish("event")                        # ✓ Empty data and metadata (both default to {})
bus.publish("event", metadata={"source": "api"})  # ✓ Only metadata, data defaults to {}
bus.publish("event", {"key": "value"})      # ✓ Only data, metadata defaults to {}

# Create message directly with optional data:
msg1 = Message(topic="signal.event")        # data defaults to {}
msg2 = Message(topic="data.event", data={"id": 123})
msg3 = Message(topic="tracked.event", data={"id": 456}, metadata={"request_id": "req-789"})
```

### Multiple Subscribers

Multiple callbacks can subscribe to the same topic:

```python
def log_event(msg: Message) -> None:
    print(f"Event: {msg}")

def store_event(msg: Message) -> None:
    database.save(msg)

bus.subscribe("order.created", log_event)
bus.subscribe("order.created", store_event)

# Both callbacks invoked for each message
bus.publish("order.created", order_data)
```

### Topic Naming Conventions

Topics use dot notation for hierarchical organization:

```python
# Good topic names
"user.created"
"user.updated"
"order.placed"
"order.payment.failed"
"notification.email.sent"

# Invalid topic names
""                  # Empty - raises SplurgePubSubValueError
".invalid"          # Starts with dot - raises SplurgePubSubValueError
"invalid."          # Ends with dot - raises SplurgePubSubValueError
"invalid..name"     # Consecutive dots - raises SplurgePubSubValueError
```

## Phase 2: Advanced Features

### Decorator API

Simplified subscription syntax using decorators:

```python
bus = PubSub()

# Use @bus.on() to subscribe
@bus.on("user.created")
def handle_user_created(msg: Message) -> None:
    print(f"New user: {msg.data['name']}")

@bus.on("user.updated")
def handle_user_updated(msg: Message) -> None:
    print(f"User updated: {msg.data['name']}")

# Publish events
bus.publish("user.created", {"id": 1, "name": "Alice"})
bus.publish("user.updated", {"id": 1, "name": "Alice Smith"})
```

**Benefits**:
- More readable and Pythonic syntax
- Declaration-time subscription
- Better IDE support and autocompletion

**Limitations**:
- Cannot capture subscriber_id directly (use manual subscribe() if needed)
- Decorator returns original function (useful for chaining)

### Error Handling

Custom error handlers allow centralized error management:

```python
def critical_error_handler(exc: Exception, topic: str) -> None:
    """Handle errors with custom logic."""
    logger.critical(f"Critical error on {topic}: {exc}", exc_info=exc)
    # Could also send alerts, write to database, etc.

bus = PubSub(error_handler=critical_error_handler)

@bus.on("payment.process")
def process_payment(msg: Message) -> None:
    # If this raises an exception...
    charge_credit_card(msg.data)

# Exception is caught and passed to critical_error_handler
bus.publish("payment.process", payment_data)
```

**Default Error Handler**:

If no custom handler is provided, errors are logged:

```python
import logging

# This is the default behavior
logger.error(
    f"Error in subscriber callback for topic '{topic}': {type(exc).__name__}: {exc}",
    exc_info=exc
)
```

**Error Isolation**:

Errors in one subscriber callback do not affect others:

```python
def failing_callback(msg: Message) -> None:
    raise ValueError("This callback fails")

def working_callback(msg: Message) -> None:
    print(f"This still executes: {msg.data}")

bus.subscribe("topic", failing_callback)
bus.subscribe("topic", working_callback)

bus.publish("topic", data)
# Output: Error logged for failing_callback
#         "This still executes: ..." printed
```

### Topic Filtering

Use wildcard patterns to match multiple related topics:

```python
from splurge_pub_sub import TopicPattern

# Create a pattern
pattern = TopicPattern("user.*")

# Test matching
pattern.matches("user.created")      # True
pattern.matches("user.updated")      # True
pattern.matches("user.deleted")      # True
pattern.matches("order.created")     # False
```

**Wildcard Syntax**:

- `*` - Matches any characters except dot (one segment)
- `?` - Matches any single character except dot
- Exact match - Literal topic name

**Examples**:

```python
# Exact match (no wildcards)
TopicPattern("user.created").is_exact  # True
TopicPattern("user.created").matches("user.created")  # True
TopicPattern("user.created").matches("user.updated")  # False

# Match any segment
TopicPattern("user.*").matches("user.created")     # True
TopicPattern("user.*").matches("user.updated")     # True
TopicPattern("user.*").matches("user.a.created")   # False (doesn't match > 1 segment)
TopicPattern("*.created").matches("user.created")  # True
TopicPattern("*.created").matches("order.created") # True

# Match single character within segment
TopicPattern("user.?.created").matches("user.a.created")  # True
TopicPattern("user.?.created").matches("user.ab.created") # False
TopicPattern("order.?.paid").matches("order.1.paid")      # True

# Complex patterns
TopicPattern("*.*.created").matches("entity.action.created")      # True
TopicPattern("*.*.created").matches("entity.created")              # False
TopicPattern("payment.*.*").matches("payment.order.processed")    # True
```

**Pattern Validation**:

Patterns must follow the same rules as topics:

```python
# Valid patterns
TopicPattern("user.*")
TopicPattern("*.created")
TopicPattern("order.?.paid")

# Invalid patterns
TopicPattern("")                    # SplurgePubSubPatternError
TopicPattern(".invalid")            # SplurgePubSubPatternError
TopicPattern("invalid.")            # SplurgePubSubPatternError
TopicPattern("invalid..name")       # SplurgePubSubPatternError
TopicPattern("invalid@name")        # SplurgePubSubPatternError
```

## Error Handling

### Exception Hierarchy

All framework exceptions inherit from `SplurgePubSubError`:

```
SplurgePubSubError (base)
├── SplurgePubSubValueError (ValueError)
├── SplurgePubSubTypeError (TypeError)
├── SplurgePubSubLookupError (LookupError)
├── SplurgePubSubRuntimeError (RuntimeError)
├── SplurgePubSubOSError (OSError)
└── SplurgePubSubPatternError (ValueError)
```

### Error Types and When They're Raised

#### SplurgePubSubValueError

Raised when an invalid value is provided:

```python
# Empty topic
bus.subscribe("", callback)  # SplurgePubSubValueError

# Message with invalid topic
Message(topic="", data={})   # SplurgePubSubValueError

# Invalid pattern
TopicPattern("")             # SplurgePubSubPatternError (subclass)
```

#### SplurgePubSubTypeError

Raised when a parameter has incorrect type:

```python
# Non-callable callback
bus.subscribe("topic", "not_callable")  # SplurgePubSubTypeError

# Non-dict message payload
bus.publish("topic", "string_data")     # SplurgePubSubTypeError

# Dict with non-string keys
bus.publish("topic", {1: "one", 2: "two"})  # SplurgePubSubTypeError
```

**Common Cases**:
- Callback is not callable
- Message payload is not dict[str, Any]
- Message dict has non-string keys
- Parameter type is incorrect

#### SplurgePubSubLookupError

Raised when a resource is not found:

```python
# Unsubscribe with invalid subscriber ID
bus.unsubscribe("topic", "invalid-id")  # SplurgePubSubLookupError

# Unsubscribe from topic with no subscribers
bus.unsubscribe("topic", "any-id")      # SplurgePubSubLookupError
```

#### SplurgePubSubRuntimeError

Raised when operation cannot proceed:

```python
bus.shutdown()
bus.subscribe("topic", callback)  # SplurgePubSubRuntimeError
```

#### SplurgePubSubPatternError

Raised for invalid topic patterns:

```python
TopicPattern(".invalid")        # SplurgePubSubPatternError
TopicPattern("invalid.")        # SplurgePubSubPatternError
TopicPattern("invalid..name")   # SplurgePubSubPatternError
```

### Catching Exceptions

Catch framework-specific errors:

```python
from splurge_pub_sub import SplurgePubSubError, SplurgePubSubValueError

# Catch all framework errors
try:
    bus.subscribe(topic, callback)
except SplurgePubSubError as e:
    logger.error(f"Pub-Sub error: {e}")

# Catch specific errors
try:
    bus.subscribe(topic, callback)
except SplurgePubSubValueError:
    logger.error("Invalid topic")
except SplurgePubSubTypeError:
    logger.error("Invalid callback type")
```

## Common Patterns

### Event Aggregation

Combine multiple event streams:

```python
bus = PubSub()

events = []

@bus.on("user.created")
def track_user_created(msg: Message) -> None:
    events.append(("user_created", msg.data))

@bus.on("user.updated")
def track_user_updated(msg: Message) -> None:
    events.append(("user_updated", msg.data))

@bus.on("user.deleted")
def track_user_deleted(msg: Message) -> None:
    events.append(("user_deleted", msg.data))

# All events tracked in single list
bus.publish("user.created", {"id": 1})
bus.publish("user.updated", {"id": 1})
bus.publish("user.deleted", {"id": 1})

print(events)  # [("user_created", {...}), ("user_updated", {...}), ("user_deleted", {...})]
```

### Event Routing

Route events to different handlers:

```python
bus = PubSub()

@bus.on("order.placed")
def on_order_placed(msg: Message) -> None:
    # Send confirmation email
    email_service.send_confirmation(msg.data)

@bus.on("order.payment.failed")
def on_payment_failed(msg: Message) -> None:
    # Notify customer of payment issue
    notification_service.alert_payment_failure(msg.data)

@bus.on("order.shipped")
def on_order_shipped(msg: Message) -> None:
    # Update tracking
    tracking_service.update(msg.data)
```

### Event Logging

Log all events:

```python
def log_all_events(msg: Message) -> None:
    """Log all events for audit trail."""
    logger.info(
        f"Event: {msg.topic} | Data: {msg.data} | Time: {msg.timestamp}"
    )

# Subscribe to specific topics or use a message middleware
bus.subscribe("order.placed", log_all_events)
bus.subscribe("order.payment.failed", log_all_events)
```

### Dead Letter Queue

Handle failed events:

```python
dead_letter_queue = []

def dead_letter_handler(exc: Exception, topic: str) -> None:
    """Capture failed events for later processing."""
    dead_letter_queue.append({
        "topic": topic,
        "error": str(exc),
        "timestamp": datetime.now()
    })

bus = PubSub(error_handler=dead_letter_handler)

@bus.on("critical.operation")
def process_critical_operation(msg: Message) -> None:
    # May fail
    process_payment(msg.data)
    # Failed events captured in dead_letter_queue
```

### Request-Reply Pattern

Simulate request-reply over pub-sub:

```python
import time
from uuid import uuid4

class RequestReply:
    def __init__(self, bus: PubSub):
        self.bus = bus
        self.responses = {}
        self.bus.subscribe("*.reply", self._handle_reply)

    def _handle_reply(self, msg: Message) -> None:
        # Metadata is always a dict (never None)
        request_id = msg.metadata.get("request_id")
        if request_id:
            self.responses[request_id] = msg.data

    def request(self, topic: str, data: Any, timeout: float = 5.0) -> Any:
        request_id = str(uuid4())
        reply_topic = f"{topic}.reply"
        
        self.responses[request_id] = None
        # Publish with metadata for request tracking
        self.bus.publish(
            topic,
            data,
            metadata={"request_id": request_id, "reply_topic": reply_topic}
        )
        
        # Wait for response
        start = time.time()
        while time.time() - start < timeout:
            if request_id in self.responses and self.responses[request_id] is not None:
                return self.responses.pop(request_id)
            time.sleep(0.01)
        
        raise TimeoutError(f"No response to {topic} request")

# Usage
rr = RequestReply(bus)

@bus.on("calculate")
def handle_calculate(msg: Message) -> None:
    a = msg.data["a"]
    b = msg.data["b"]
    result = a + b
    # Metadata is always a dict, no None checks needed
    reply_topic = msg.metadata.get("reply_topic")
    request_id = msg.metadata.get("request_id")
    
    if reply_topic and request_id:
        bus.publish(reply_topic, {"result": result}, metadata={"request_id": request_id})

# Make request
result = rr.request("calculate", {"a": 5, "b": 3}, timeout=2.0)
print(result)  # {"result": 8}
```

## Thread Safety

### Thread-Safe Operations

All PubSub operations are thread-safe using an RLock:

- `subscribe()` - Thread-safe subscription
- `publish()` - Thread-safe message publishing (non-blocking, enqueues to thread-safe queue)
- `drain()` - Thread-safe waiting for queue to empty
- `unsubscribe()` - Thread-safe subscription removal
- `clear()` - Thread-safe subscriber clearing
- `shutdown()` - Thread-safe shutdown

### Concurrent Publishing

Multiple threads can publish simultaneously:

```python
import threading

bus = PubSub()

def publisher_thread(topic_prefix, count):
    for i in range(count):
        bus.publish(f"{topic_prefix}.event", {"number": i})

# Multiple publishers
t1 = threading.Thread(target=publisher_thread, args=("thread1", 100))
t2 = threading.Thread(target=publisher_thread, args=("thread2", 100))

t1.start()
t2.start()
t1.join()
t2.join()
```

### Reentrant Callbacks

Callbacks can reenter the bus (publish/subscribe within callbacks):

```python
bus = PubSub()

@bus.on("event.primary")
def handle_primary(msg: Message) -> None:
    # Safe to publish from within callback
    bus.publish("event.secondary", msg.data)

@bus.on("event.secondary")
def handle_secondary(msg: Message) -> None:
    print(f"Secondary: {msg.data}")

bus.publish("event.primary", data)  # Chains through secondary
```

### Callback Execution

- Callbacks execute asynchronously in subscription order (via background worker thread)
- Publishers never block on subscriber execution
- Lock is released before callbacks execute (prevents deadlocks)
- If one callback raises an exception, others still execute
- Exceptions passed to error_handler, not re-raised
- Use `drain()` to wait for message delivery when needed

## Performance Considerations

### Message Publishing

Publishing is O(1) for enqueueing (non-blocking), with O(n) dispatch where n is the number of subscribers:

```python
bus = PubSub()

# Subscribe 1000 callbacks to same topic
for i in range(1000):
    bus.subscribe("topic", lambda msg: None)

# Publish enqueues immediately (non-blocking)
bus.publish("topic", data)  # Returns immediately

# Background worker dispatches to all 1000 callbacks asynchronously
bus.drain()  # Wait for delivery if needed
```

### Memory Usage

- Subscriptions stored in dictionary keyed by topic
- Each subscription entry stores callback and subscriber_id
- Frozen dataclasses minimize memory overhead
- Message objects are immutable (safe to share between threads)

### Lock Contention

- Lock held only during subscription registry updates
- Callbacks execute without lock (lock-free execution)
- Allows reentrant publishes without deadlock

### Optimization Tips

1. **Batch Operations**: Group related subscriptions
   ```python
   # Good
   bus.subscribe("user.created", callback1)
   bus.subscribe("user.updated", callback2)
   # Not great
   for topic in large_list:
       bus.subscribe(topic, callback)
   ```

2. **Early Unsubscribe**: Remove unused subscriptions
   ```python
   sub_id = bus.subscribe("topic", callback)
   # Later...
   bus.unsubscribe("topic", sub_id)
   ```

3. **Error Handler Performance**: Keep error handlers fast
   ```python
   # Good: Fast logging
   def error_handler(exc, topic):
       logger.error(f"Error on {topic}", exc_info=exc)
   
   # Bad: Slow database operations
   def error_handler(exc, topic):
       db.save_error(exc, topic)  # Blocks all error handling
   ```

## Related Documentation

- **[API-REFERENCE.md](api/API-REFERENCE.md)** - Complete API reference with all classes and methods
- **[CLI-REFERENCE.md](cli/CLI-REFERENCE.md)** - Command-line interface documentation
- **[CHANGELOG.md](../../CHANGELOG.md)** - Version history and changes
- **[README.md](../../README.md)** - Project overview and quick start
