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
- **PubSubAggregator**: Aggregate messages from multiple PubSub instances

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
│   ├── pubsub.py               # Main PubSub class
│   ├── pubsub_aggregator.py    # PubSubAggregator class
│   ├── message.py              # Message data structure
│   ├── types.py                # Type aliases
│   ├── constants.py            # Module constants
│   ├── exceptions.py           # Exception hierarchy
│   ├── filters.py              # Topic pattern matching (Phase 2)
│   ├── errors.py               # Error handler system (Phase 2)
│   ├── decorators.py           # Decorator API (Phase 2)
│   └── __init__.py             # Core module exports
├── cli.py                      # Command-line interface
├── __main__.py                 # Module entry point
└── __init__.py                 # Public API exports
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

## PubSubAggregator - Aggregating Multiple PubSub Instances

`PubSubAggregator` enables you to aggregate messages from multiple `PubSub` instances into a single unified subscriber interface. This is particularly useful when you have multiple packages or modules, each with their own `PubSub` instance, and you want a central component to receive events from all of them.

### Basic Usage

```python
from splurge_pub_sub import PubSubAggregator, PubSub, Message

# Create PubSub instances from different packages/modules
pack_b_bus = PubSub()
pack_c_bus = PubSub()

# Create composite to aggregate messages from both
aggregator = PubSubAggregator(pubsubs=[pack_b_bus, pack_c_bus])

# Subscribe once to receive events from any managed PubSub
def unified_handler(msg: Message) -> None:
    print(f"Received from {msg.topic}: {msg.data}")

# Use correlation_id="*" to receive all messages regardless of correlation_id
aggregator.subscribe("user.created", unified_handler, correlation_id="*")

# Publish from different PubSub instances
pack_b_bus.publish("user.created", {"id": 1, "source": "pack-b"})
pack_c_bus.publish("user.created", {"id": 2, "source": "pack-c"})

# Drain all buses to ensure messages are forwarded and delivered
pack_b_bus.drain()
pack_c_bus.drain()
aggregator.drain()
```

### Dynamic Management

You can add and remove `PubSub` instances at runtime:

```python
aggregator = PubSubAggregator()

bus_a = PubSub()
bus_b = PubSub()

# Add instances dynamically
aggregator.add_pubsub(bus_a)
aggregator.add_pubsub(bus_b)

# Later, remove an instance
aggregator.remove_pubsub(bus_a)
```

### One-Way Message Flow

**Important**: `PubSubAggregator` implements one-way message flow. Messages flow FROM managed `PubSub` instances TO aggregator subscribers, but NOT the other way around.

- ✅ Messages published to managed `PubSub` instances are forwarded to aggregator subscribers
- ❌ Messages published to the aggregator are NOT forwarded to managed `PubSub` instances

```python
aggregator = PubSubAggregator(pubsubs=[bus_a, bus_b])

# This message will be received by aggregator subscribers
bus_a.publish("event.topic", {"data": "from_bus_a"})

# This message will NOT be forwarded to bus_a or bus_b subscribers
aggregator.publish("event.topic", {"data": "from_composite"})
```

### Cascade Operations

Both `shutdown()` and `drain()` support optional cascade to managed instances:

```python
aggregator = PubSubAggregator(pubsubs=[bus_a, bus_b])

# Shutdown aggregator only (managed instances remain active)
aggregator.shutdown()

# Shutdown aggregator AND all managed instances
aggregator.shutdown(cascade=True)

# Drain aggregator's internal queue only
aggregator.drain()

# Drain aggregator AND all managed instances
aggregator.drain(cascade=True)
```

### Lifecycle Management

Managed `PubSub` instances are created and managed externally. `PubSubAggregator` only subscribes to them and forwards their messages. When you call `shutdown(cascade=False)` (the default), managed instances remain active and can continue to be used independently.

### Use Cases

- **Multi-Package Event Aggregation**: Aggregate events from multiple packages/modules
- **Central Monitoring**: Central logging or monitoring component receiving events from all sources
- **Event Bus Federation**: Combine multiple independent event buses
- **Plugin Systems**: Aggregate events from multiple plugin buses

### Thread Safety

All `PubSubAggregator` operations are thread-safe, using locks for synchronization. You can safely add/remove `PubSub` instances and subscribe/publish from multiple threads.

## PubSubSolo - Scoped Singleton PubSub Instances

`PubSubSolo` provides scoped singleton instances of `PubSub`, where each scope (e.g., package/library name) gets its own singleton instance. This enables multiple packages/libraries to each have their own singleton that can be aggregated via `PubSubAggregator`.

### Why PubSubSolo?

When multiple packages need their own singleton `PubSub` instance, a true singleton (one instance per process) won't work because all packages would share the same instance. `PubSubSolo` solves this by providing **scoped singletons** - one singleton per scope name.

### Basic Usage

```python
from splurge_pub_sub import PubSubSolo

# Each package gets its own singleton instance
bus_a = PubSubSolo.get_instance(scope="package_a")
bus_b = PubSubSolo.get_instance(scope="package_b")

# Same scope returns same instance
bus_a2 = PubSubSolo.get_instance(scope="package_a")
assert bus_a is bus_a2  # True

# Different scopes return different instances
assert bus_a is not bus_b  # True
```

### Usage with PubSubAggregator

`PubSubSolo` is designed to work seamlessly with `PubSubAggregator`:

```python
from splurge_pub_sub import PubSubSolo, PubSubAggregator

# Each package gets its own singleton
dsv_bus = PubSubSolo.get_instance(scope="splurge_dsv")
tabular_bus = PubSubSolo.get_instance(scope="splurge_tabular")
typer_bus = PubSubSolo.get_instance(scope="splurge_typer")

# Aggregate them - each is a different instance!
monitoring_aggregator = PubSubAggregator(pubsubs=[dsv_bus, tabular_bus, typer_bus])

# Subscribe to all events
@monitoring_aggregator.on("*")
def log_all_events(msg: Message) -> None:
    print(f"[{msg.topic}] {msg.data}")

# Publish from different packages
dsv_bus.publish("dsv.file.loaded", {"file": "data.csv"})
tabular_bus.publish("tabular.table.created", {"rows": 100})
typer_bus.publish("typer.command.executed", {"command": "process"})

# Drain all buses
dsv_bus.drain()
tabular_bus.drain()
typer_bus.drain()
monitoring_aggregator.drain()
```

### Configuration

Configuration parameters (`error_handler`, `correlation_id`) are only applied on the first call for a scope:

```python
# First call - configuration applied
bus = PubSubSolo.get_instance(
    scope="my_package",
    error_handler=custom_handler,
    correlation_id="my-id"
)

# Second call with different config - ignored, returns same instance
bus2 = PubSubSolo.get_instance(
    scope="my_package",
    error_handler=different_handler,  # Ignored
    correlation_id="different-id"  # Ignored
)

assert bus is bus2  # Same instance
assert bus.correlation_id == "my-id"  # Original config kept
```

### Convenience Methods

`PubSubSolo` provides convenience class methods that delegate to the singleton instance:

```python
# Using convenience methods
PubSubSolo.subscribe("topic", callback, scope="my_package")
PubSubSolo.publish("topic", {"data": "test"}, scope="my_package")

# Or get instance and use directly
bus = PubSubSolo.get_instance(scope="my_package")
bus.subscribe("topic", callback)
bus.publish("topic", {"data": "test"})
```

### Utility Methods

`PubSubSolo` provides utility methods for monitoring and management:

```python
# Check if a scope is initialized
if PubSubSolo.is_initialized("my_scope"):
    print("Scope is initialized")

# Get all initialized scopes
scopes = PubSubSolo.get_all_scopes()
print(f"Active scopes: {scopes}")

# Shutdown a specific scope
PubSubSolo.shutdown(scope="my_scope")

# Shutdown all scopes
for scope in PubSubSolo.get_all_scopes():
    PubSubSolo.shutdown(scope=scope)
```

### Thread Safety

Instance creation is thread-safe using per-scope locks with double-check locking pattern. Multiple threads can safely call `get_instance()` with the same scope and will receive the same instance.

### Use Cases

- **Multi-Package Applications**: Each package/library has its own singleton instance
- **Plugin Systems**: Each plugin gets its own singleton event bus
- **Microservices**: Each service component has its own singleton
- **Testing**: Easy to reset singleton state between tests

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
