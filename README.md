# splurge-pub-sub

[![PyPI version](https://badge.fury.io/py/splurge-pub-sub.svg)](https://pypi.org/project/splurge-pub-sub/)
[![Python versions](https://img.shields.io/pypi/pyversions/splurge-pub-sub.svg)](https://pypi.org/project/splurge-pub-sub/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

[![CI](https://github.com/jim-schilling/splurge-pub-sub/actions/workflows/ci-quick-test.yml/badge.svg)](https://github.com/jim-schilling/splurge-pub-sub/actions/workflows/ci-quick-test.yml)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen.svg)](https://github.com/jim-schilling/splurge-pub-sub)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-black)](https://mypy-lang.org/)

A lightweight, thread-safe publish-subscribe framework for Python applications. Splurge provides simple, Pythonic in-process event communication with full type safety and comprehensive error handling.

## Features

- **Lightweight**: Zero external dependencies, minimal footprint
- **Thread-Safe**: Full concurrency support with reentrant locks
- **Type-Safe**: Complete type annotations with mypy strict mode compliance
- **Simple API**: Subscribe, publish, unsubscribe with intuitive methods
- **Decorator Syntax**: `@bus.on("topic")` for simplified subscriptions
- **Topic Filtering**: Wildcard pattern matching for selective message delivery
- **Correlation IDs**: Cross-library event tracking and coordination
- **Error Handling**: Custom error handlers for failed callbacks
- **Context Manager**: Automatic resource cleanup with `with` statement
- **94% Coverage**: Comprehensive test coverage across all features

## Quick Start

### Installation

```bash
pip install splurge-pub-sub
```

### Basic Usage

```python
from splurge_pub_sub import PubSub, Message

# Create a pub-sub bus
bus = PubSub()

# Subscribe to a topic
def handle_event(msg: Message) -> None:
    print(f"Received: {msg.data}")

sub_id = bus.subscribe("user.created", handle_event)

# Publish a message
bus.publish("user.created", {"id": 123, "name": "Alice"})
# Output: Received: {'id': 123, 'name': 'Alice'}

# Unsubscribe when done
bus.unsubscribe("user.created", sub_id)
```

### Decorator API

```python
@bus.on("user.updated")
def handle_user_updated(msg: Message) -> None:
    print(f"User updated: {msg.data}")

bus.publish("user.updated", {"id": 123, "status": "active"})
```

### Topic Filtering

```python
from splurge_pub_sub import TopicPattern

# Create patterns with wildcards
pattern = TopicPattern("user.*")
pattern.matches("user.created")  # True
pattern.matches("user.updated")  # True
pattern.matches("order.created")  # False

# Patterns with ? for single character
pattern = TopicPattern("user.?.created")
pattern.matches("user.a.created")  # True
pattern.matches("user.ab.created")  # False
```

### Correlation ID for Cross-Library Coordination

```python
# Multiple libraries using same correlation_id
correlation_id = "workflow-123"

dsv_bus = PubSub(correlation_id=correlation_id)
tabular_bus = PubSub(correlation_id=correlation_id)

# Monitor all events with same correlation_id
monitor_bus = PubSub()
monitor_bus.subscribe("*", lambda m: print(f"[{m.correlation_id}] {m.topic}"), 
                      correlation_id=correlation_id)

dsv_bus.publish("dsv.file.loaded", {"file": "data.csv"})
tabular_bus.publish("tabular.table.created", {"rows": 100})
# Both messages received by monitor
```

### Error Handling

```python
def my_error_handler(exc: Exception, topic: str) -> None:
    print(f"Error on topic '{topic}': {exc}")

bus = PubSub(error_handler=my_error_handler)

@bus.on("risky.operation")
def handle_event(msg: Message) -> None:
    raise ValueError("Something went wrong!")

bus.publish("risky.operation", {})  # Error handler called
# Output: Error on topic 'risky.operation': Something went wrong!
```

### Context Manager

```python
with PubSub() as bus:
    bus.subscribe("topic", callback)
    bus.publish("topic", data)
    # Cleanup happens automatically
```

## Documentation

- **[README-DETAILS.md](docs/README-DETAILS.md)** - Comprehensive developer's guide with features, examples, and API overview
- **[API-REFERENCE.md](docs/api/API-REFERENCE.md)** - Complete API reference with all classes, methods, and error types
- **[CLI-REFERENCE.md](docs/cli/CLI-REFERENCE.md)** - Command-line interface documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

## Requirements

- Python 3.10 or later
- No external dependencies

## License

MIT License - see [LICENSE](LICENSE) file for details

## Author

Jim Schilling

## Support

For issues, questions, or contributions, visit the [GitHub repository](https://github.com/jim-schilling/splurge-pub-sub).
