"""
Splurge Pub-Sub: Basic API Usage Examples

This script demonstrates the fundamental usage of the Splurge Pub-Sub framework,
showcasing all major features and common patterns.

Run with:
    python examples/api_usage.py
    python -m examples.api_usage
"""

from datetime import datetime, timezone

from splurge_pub_sub import (
    Message,
    PubSub,
    SplurgePubSubError,
    SplurgePubSubValueError,
    TopicPattern,
)


def example_1_basic_pubsub() -> None:
    """Example 1: Basic Publish-Subscribe

    Demonstrates the fundamental pub-sub pattern: subscribe to a topic,
    publish messages, and receive them in callbacks.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Publish-Subscribe")
    print("=" * 70)

    # Create a pub-sub bus
    bus = PubSub()

    # Define a callback function
    def on_user_created(msg: Message) -> None:
        """Handle user.created events."""
        print(f"  ✓ Event received: {msg.topic}")
        print(f"    Data: {msg.data}")
        print(f"    Timestamp: {msg.timestamp.isoformat()}")

    # Subscribe to a topic
    print("\n1. Creating PubSub bus")
    print("2. Subscribing to 'user.created' topic")
    subscriber_id = bus.subscribe("user.created", on_user_created)
    print(f"   Subscriber ID: {subscriber_id[:8]}...")

    # Publish a message
    print("\n3. Publishing message to 'user.created'")
    bus.publish("user.created", {"id": 123, "name": "Alice", "email": "alice@example.com"})

    # Unsubscribe
    print("\n4. Unsubscribing from topic")
    bus.unsubscribe("user.created", subscriber_id)
    print("   Unsubscribed successfully")

    # Try to publish again (no subscribers)
    print("\n5. Publishing again (no subscribers receive it)")
    bus.publish("user.created", {"id": 456, "name": "Bob"})
    print("   Message published to empty subscriber list")


def example_2_multiple_subscribers() -> None:
    """Example 2: Multiple Subscribers

    Demonstrates that multiple subscribers can listen to the same topic
    and receive the same message.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Multiple Subscribers")
    print("=" * 70)

    bus = PubSub()

    # Define multiple callbacks
    def log_event(msg: Message) -> None:
        """Log all events."""
        print(f"  [LOG] Topic: {msg.topic}, Data: {msg.data}")

    def store_event(msg: Message) -> None:
        """Store events in memory."""
        print(f"  [STORE] Persisting event for topic: {msg.topic}")

    def notify_event(msg: Message) -> None:
        """Send notifications for events."""
        print(f"  [NOTIFY] Notifying about: {msg.topic}")

    # Subscribe all callbacks to same topic
    print("\n1. Subscribing 3 callbacks to 'order.created'")
    bus.subscribe("order.created", log_event)
    bus.subscribe("order.created", store_event)
    bus.subscribe("order.created", notify_event)

    # Publish a message
    print("\n2. Publishing 'order.created' message")
    bus.publish("order.created", {"order_id": "ORD-001", "total": 99.99})

    print("\n3. All callbacks invoked in order (fan-out pattern)")


def example_3_decorator_api() -> None:
    """Example 3: Decorator API

    Demonstrates the simplified @bus.on() decorator syntax for subscribing
    to topics.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Decorator API (@bus.on())")
    print("=" * 70)

    bus = PubSub()

    print("\n1. Defining subscriber callbacks with @bus.on() decorator")

    # Use decorator syntax
    @bus.on("user.created")
    def handle_user_created(msg: Message) -> None:
        """Handle user creation."""
        print(f"  ✓ New user created: {msg.data['name']}")

    @bus.on("user.updated")
    def handle_user_updated(msg: Message) -> None:
        """Handle user update."""
        print(f"  ✓ User updated: {msg.data['name']}")

    @bus.on("user.deleted")
    def handle_user_deleted(msg: Message) -> None:
        """Handle user deletion."""
        print(f"  ✓ User deleted: {msg.data['id']}")

    print("   Defined 3 handlers with @bus.on() decorator")

    # Publish messages
    print("\n2. Publishing events")
    bus.publish("user.created", {"id": 1, "name": "Alice"})
    bus.publish("user.updated", {"id": 1, "name": "Alice Smith"})
    bus.publish("user.deleted", {"id": 1})

    print("\n3. All decorated callbacks invoked")


def example_4_message_structure() -> None:
    """Example 4: Message Structure

    Demonstrates the Message dataclass with all its attributes and
    validation rules.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Message Structure")
    print("=" * 70)

    bus = PubSub()

    print("\n1. Creating messages with different attributes")

    # Message with just topic and data
    def show_message(msg: Message) -> None:
        print(f"\n   Topic: {msg.topic}")
        print(f"   Data: {msg.data}")
        print(f"   Timestamp: {msg.timestamp.isoformat()}")
        print(f"   Metadata: {msg.metadata}")

    bus.subscribe("demo", show_message)

    # Simple message
    print("\n   a) Simple message (auto-generated timestamp):")
    bus.publish("demo", {"action": "simple"})

    # Message with custom timestamp
    print("\n   b) Message with custom timestamp:")
    custom_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    Message(topic="demo", data={"action": "custom_time"}, timestamp=custom_time)

    def show_custom_message(m: Message) -> None:
        print(f"      Timestamp: {m.timestamp.isoformat()}")

    bus.subscribe("demo", show_custom_message)
    bus.publish("demo", {"action": "custom_time"})

    # Message with metadata
    print("\n   c) Message with metadata:")
    Message(
        topic="demo",
        data={"action": "with_metadata"},
        metadata={"user_id": 123, "session": "abc-xyz"},
    )

    def show_metadata(m: Message) -> None:
        print(f"      Metadata: {m.metadata}")

    bus.subscribe("demo", show_metadata)
    bus.publish("demo", {"action": "with_metadata"})


def example_5_topic_patterns() -> None:
    """Example 5: Topic Pattern Matching

    Demonstrates wildcard topic patterns for flexible message routing.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Topic Pattern Matching")
    print("=" * 70)

    # Create patterns
    print("\n1. Creating topic patterns")
    exact_pattern = TopicPattern("user.created")
    wildcard_pattern = TopicPattern("user.*")
    single_char_pattern = TopicPattern("order.?.paid")
    complex_pattern = TopicPattern("*.order.*")

    print(f"   Exact pattern: '{exact_pattern.pattern}' (is_exact={exact_pattern.is_exact})")
    print(f"   Wildcard pattern: '{wildcard_pattern.pattern}' (is_exact={wildcard_pattern.is_exact})")
    print(f"   Single char pattern: '{single_char_pattern.pattern}'")
    print(f"   Complex pattern: '{complex_pattern.pattern}'")

    # Test matching
    print("\n2. Testing pattern matching")

    test_topics = [
        "user.created",
        "user.updated",
        "user.deleted",
        "order.created",
        "order.1.paid",
        "order.ab.paid",
        "admin.order.processed",
        "user.order.completed",
    ]

    print("\n   Topic Matching Results:")
    print(f"   {'Topic':<25} | {'exact':<6} | {'user.*':<8} | {'order.?':<8} | {'*.order.*':<10}")
    print("   " + "-" * 65)

    for topic in test_topics:
        e = "✓" if exact_pattern.matches(topic) else "✗"
        w = "✓" if wildcard_pattern.matches(topic) else "✗"
        s = "✓" if single_char_pattern.matches(topic) else "✗"
        c = "✓" if complex_pattern.matches(topic) else "✗"
        print(f"   {topic:<25} | {e:<6} | {w:<8} | {s:<8} | {c:<10}")


def example_7_correlation_id() -> None:
    """Example 7: Correlation ID for Cross-Library Coordination

    Demonstrates using correlation_id to coordinate events across multiple
    PubSub instances, enabling cross-library event tracking.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Correlation ID for Cross-Library Coordination")
    print("=" * 70)

    # Shared correlation_id for workflow
    correlation_id = "workflow-abc-123"

    print("\n1. Creating multiple PubSub instances with same correlation_id")
    dsv_bus = PubSub(correlation_id=correlation_id)
    tabular_bus = PubSub(correlation_id=correlation_id)
    typer_bus = PubSub(correlation_id=correlation_id)

    print(f"   Instance correlation_ids: {dsv_bus.correlation_id}")

    # Monitor bus to capture all events
    monitor_bus = PubSub()
    received_events: list[tuple[str, str]] = []

    def monitor_all(msg: Message) -> None:
        """Monitor all events with matching correlation_id."""
        received_events.append((msg.topic, msg.correlation_id or "None"))
        print(f"  ✓ [{msg.correlation_id}] {msg.topic}: {msg.data}")

    print("\n2. Subscribing to all topics with correlation_id filter")
    monitor_bus.subscribe("*", monitor_all, correlation_id=correlation_id)

    print("\n3. Publishing from different library instances")
    dsv_bus.publish("dsv.file.loaded", {"file": "data.csv"})
    tabular_bus.publish("tabular.table.created", {"rows": 100})
    typer_bus.publish("typer.command.executed", {"command": "process"})

    print(f"\n4. Total events received: {len(received_events)}")
    print("   All events have matching correlation_id")
    print(f"   Tracked correlation_ids: {monitor_bus.correlation_ids}")

    print("\n5. Correlation ID filtering example")
    filter_bus = PubSub(correlation_id="default-id")
    received_a: list[str] = []
    received_b: list[str] = []
    received_any: list[str] = []

    def handler_a(msg: Message) -> None:
        received_a.append(msg.data["id"])

    def handler_b(msg: Message) -> None:
        received_b.append(msg.data["id"])

    def handler_any(msg: Message) -> None:
        received_any.append(msg.data["id"])

    filter_bus.subscribe("test.topic", handler_a, correlation_id="id-a")
    filter_bus.subscribe("test.topic", handler_b, correlation_id="id-b")
    filter_bus.subscribe("test.topic", handler_any, correlation_id="*")

    filter_bus.publish("test.topic", {"id": "1"}, correlation_id="id-a")
    filter_bus.publish("test.topic", {"id": "2"}, correlation_id="id-b")
    filter_bus.publish("test.topic", {"id": "3"}, correlation_id="id-c")

    print(f"   Handler A (id-a): {received_a}")  # ['1']
    print(f"   Handler B (id-b): {received_b}")  # ['2']
    print(f"   Handler Any (*): {received_any}")  # ['1', '2', '3']
    print(f"   Instance correlation_id: {filter_bus.correlation_id}")
    print(f"   All published correlation_ids: {filter_bus.correlation_ids}")


def example_6_error_handling() -> None:
    """Example 6: Error Handling

    Demonstrates error handling with custom error handlers and
    exception catching.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Error Handling")
    print("=" * 70)

    # Custom error handler
    def my_error_handler(exc: Exception, topic: str) -> None:
        """Custom error handler."""
        print(f"  [ERROR HANDLER] Exception on '{topic}': {type(exc).__name__}: {exc}")

    bus = PubSub(error_handler=my_error_handler)

    print("\n1. Creating bus with custom error handler")

    # Subscribe to topic with failing callback
    @bus.on("risky.operation")
    def risky_callback(msg: Message) -> None:
        raise ValueError("Something went wrong!")

    @bus.on("risky.operation")
    def safe_callback(msg: Message) -> None:
        print(f"  ✓ Safe callback still executes: {msg.data}")

    print("2. Subscribing callbacks (one will fail)")

    print("\n3. Publishing to topic (error handler manages exceptions)")
    bus.publish("risky.operation", {"task": "risky"})

    print("\n4. Error isolation: safe callback still ran despite exception in risky callback")

    # Test input validation errors
    print("\n5. Testing input validation")

    try:
        print("   Attempting to subscribe to empty topic...")
        bus.subscribe("", lambda m: None)
    except SplurgePubSubValueError as e:
        print(f"   ✓ Caught: {type(e).__name__}: {e}")

    try:
        print("   Attempting to subscribe non-callable callback...")
        bus.subscribe("topic", "not_callable")  # type: ignore
    except Exception as e:
        print(f"   ✓ Caught: {type(e).__name__}")


def example_8_context_manager() -> None:
    """Example 8: Context Manager

    Demonstrates automatic resource cleanup using the context manager
    protocol.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Context Manager")
    print("=" * 70)

    print("\n1. Using PubSub with context manager")
    print("   with PubSub() as bus:")

    with PubSub() as bus:
        print("   ├─ Inside context, bus is active")

        @bus.on("event")
        def handle_event(msg: Message) -> None:
            print(f"   │  ✓ Received: {msg.data}")

        print("   ├─ Publishing message")
        bus.publish("event", {"data": "test"})

        print("   └─ Exiting context...")

    print("\n2. Context manager automatically calls bus.shutdown()")
    print("   (Resources cleaned up, subscriptions cleared)")
    print(f"   Bus shutdown status: {bus.is_shutdown}")

    # Try to use bus after shutdown
    print("\n3. Attempting to use bus after shutdown")
    try:
        bus.subscribe("topic", lambda m: None)
    except SplurgePubSubError as e:
        print(f"   ✓ Operation blocked: {type(e).__name__}")


def example_9_clear_operations() -> None:
    """Example 9: Clear Operations

    Demonstrates clearing subscribers from specific topics or all topics.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Clear Operations")
    print("=" * 70)

    bus = PubSub()

    def callback(msg: Message) -> None:
        print(f"  Received: {msg.topic}")

    print("\n1. Subscribing callbacks to multiple topics")
    bus.subscribe("topic.a", callback)
    bus.subscribe("topic.b", callback)
    bus.subscribe("topic.c", callback)
    print("   Subscribed to: topic.a, topic.b, topic.c")

    print("\n2. Publishing to all topics (all subscribers called)")
    bus.publish("topic.a", {})
    bus.publish("topic.b", {})
    bus.publish("topic.c", {})

    print("\n3. Clearing topic.b subscribers")
    bus.clear("topic.b")
    print("   topic.b cleared")

    print("\n4. Publishing again (topic.b has no subscribers)")
    bus.publish("topic.a", {"msg": "from a"})
    bus.publish("topic.b", {"msg": "from b"})
    bus.publish("topic.c", {"msg": "from c"})

    print("\n5. Clearing all subscribers")
    bus.clear()
    print("   All topics cleared")

    print("\n6. Publishing again (no subscribers on any topic)")
    bus.publish("topic.a", {})
    print("   (no output - no subscribers)")


def example_10_real_world_scenario() -> None:
    """Example 10: Real-World Scenario

    Demonstrates a practical e-commerce event system combining multiple
    features (decorators, error handling, multiple subscribers).
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 10: Real-World Scenario - E-Commerce Events")
    print("=" * 70)

    # Create event bus with error handling
    def ecommerce_error_handler(exc: Exception, topic: str) -> None:
        print(f"  [!] Event error on '{topic}': {exc}")

    bus = PubSub(error_handler=ecommerce_error_handler)

    # Event handlers
    @bus.on("order.placed")
    def send_confirmation_email(msg: Message) -> None:
        """Send order confirmation."""
        order = msg.data
        print(f"  📧 Sending confirmation email for order {order['id']}")

    @bus.on("order.placed")
    def log_order(msg: Message) -> None:
        """Log order for analytics."""
        order = msg.data
        print(f"  📊 Logging order {order['id']} for analytics")

    @bus.on("order.placed")
    def update_inventory(msg: Message) -> None:
        """Update inventory."""
        order = msg.data
        print(f"  📦 Updating inventory for order {order['id']}")

    @bus.on("payment.failed")
    def notify_payment_failed(msg: Message) -> None:
        """Notify about payment failure."""
        print(f"  ⚠️  Payment failed for order {msg.data['order_id']}")

    @bus.on("payment.failed")
    def retry_payment(msg: Message) -> None:
        """Retry failed payment."""
        print(f"  🔄 Retrying payment for order {msg.data['order_id']}")

    @bus.on("order.shipped")
    def send_tracking(msg: Message) -> None:
        """Send tracking information."""
        print(f"  📬 Sending tracking for order {msg.data['order_id']}")

    print("\n1. E-commerce event system initialized with 6 handlers")

    print("\n2. Customer places order")
    bus.publish(
        "order.placed",
        {
            "id": "ORD-12345",
            "customer": "Alice",
            "items": ["item1", "item2"],
            "total": 99.99,
        },
    )

    print("\n3. Payment fails")
    bus.publish(
        "payment.failed",
        {
            "order_id": "ORD-12345",
            "reason": "Insufficient funds",
        },
    )

    print("\n4. Order ships")
    bus.publish(
        "order.shipped",
        {
            "order_id": "ORD-12345",
            "tracking": "TRACK-2025-12345",
        },
    )


def main() -> None:
    """Run all examples."""
    print("\n" + "#" * 70)
    print("# SPLURGE PUB-SUB: API USAGE EXAMPLES")
    print("#" * 70)

    try:
        example_1_basic_pubsub()
        example_2_multiple_subscribers()
        example_3_decorator_api()
        example_4_message_structure()
        example_5_topic_patterns()
        example_6_error_handling()
        example_7_correlation_id()
        example_8_context_manager()
        example_9_clear_operations()
        example_10_real_world_scenario()

        print("\n" + "#" * 70)
        print("# ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("#" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
