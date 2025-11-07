"""
Splurge Pub-Sub: Advanced API Usage Examples

This script demonstrates advanced usage patterns of the Splurge Pub-Sub framework,
including PubSubAggregator for aggregating messages from multiple PubSub instances.

Run with:
    python examples/api_advanced_usage.py
    python -m examples.api_advanced_usage
"""

from splurge_pub_sub import (
    Message,
    PubSub,
    PubSubAggregator,
)


def example_1_basic_aggregator() -> None:
    """Example 1: Basic PubSubAggregator Usage

    Demonstrates how to aggregate messages from multiple PubSub instances
    into a single unified subscriber interface.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic PubSubAggregator Usage")
    print("=" * 70)

    # Create separate PubSub instances (e.g., from different packages/modules)
    pack_b_bus = PubSub()
    pack_c_bus = PubSub()

    # Create a PubSubAggregator that aggregates messages from both
    aggregator = PubSubAggregator(pubsubs=[pack_b_bus, pack_c_bus])

    # Subscribe to events from any managed PubSub instance
    received_events: list[Message] = []

    def unified_handler(msg: Message) -> None:
        """Handle events from any managed PubSub instance."""
        received_events.append(msg)
        print(f"  ✓ Received from {msg.topic}: {msg.data}")

    # Subscribe with correlation_id="*" to receive all messages regardless of correlation_id
    aggregator.subscribe("user.created", unified_handler, correlation_id="*")

    # Publish from different PubSub instances
    print("\n1. Publishing from pack_b_bus")
    pack_b_bus.publish("user.created", {"id": 1, "source": "pack-b"})

    print("2. Publishing from pack_c_bus")
    pack_c_bus.publish("user.created", {"id": 2, "source": "pack-c"})

    # Drain all buses to ensure messages are forwarded and delivered
    pack_b_bus.drain()
    pack_c_bus.drain()
    aggregator.drain()

    print(f"\n3. Total events received: {len(received_events)}")
    print("   ✓ Messages from both PubSub instances were aggregated")


def example_2_dynamic_add_remove() -> None:
    """Example 2: Dynamically Adding and Removing PubSub Instances

    Demonstrates how to add and remove PubSub instances at runtime.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Dynamically Adding and Removing PubSub Instances")
    print("=" * 70)

    # Start with an empty aggregator
    aggregator = PubSubAggregator()

    # Create PubSub instances
    bus_a = PubSub()
    bus_b = PubSub()

    received: list[Message] = []

    def handler(msg: Message) -> None:
        received.append(msg)
        print(f"  ✓ Received: {msg.topic} - {msg.data}")

    aggregator.subscribe("event.topic", handler, correlation_id="*")

    # Add bus_a
    print("\n1. Adding bus_a to aggregator")
    aggregator.add_pubsub(bus_a)
    bus_a.publish("event.topic", {"source": "bus_a", "step": 1})
    bus_a.drain()
    aggregator.drain()

    # Add bus_b
    print("\n2. Adding bus_b to aggregator")
    aggregator.add_pubsub(bus_b)
    bus_b.publish("event.topic", {"source": "bus_b", "step": 2})
    bus_b.drain()
    aggregator.drain()

    # Remove bus_a
    print("\n3. Removing bus_a from aggregator")
    aggregator.remove_pubsub(bus_a)
    bus_a.publish("event.topic", {"source": "bus_a", "step": 3})  # Won't be received
    bus_a.drain()
    aggregator.drain()

    # bus_b still works
    print("\n4. Publishing from remaining bus_b")
    bus_b.publish("event.topic", {"source": "bus_b", "step": 4})
    bus_b.drain()
    aggregator.drain()

    print(f"\n5. Total events received: {len(received)}")
    print("   ✓ Only messages from active PubSub instances were received")


def example_3_cascade_shutdown() -> None:
    """Example 3: Cascade Shutdown

    Demonstrates how to cascade shutdown to managed PubSub instances.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Cascade Shutdown")
    print("=" * 70)

    # Create PubSub instances
    bus_a = PubSub()
    bus_b = PubSub()

    # Create aggregator
    aggregator = PubSubAggregator(pubsubs=[bus_a, bus_b])

    print("\n1. Initial state:")
    print(f"   aggregator.is_shutdown: {aggregator.is_shutdown}")
    print(f"   bus_a.is_shutdown: {bus_a.is_shutdown}")
    print(f"   bus_b.is_shutdown: {bus_b.is_shutdown}")

    # Shutdown without cascade (default)
    print("\n2. Shutting down aggregator (no cascade):")
    aggregator.shutdown()
    print(f"   aggregator.is_shutdown: {aggregator.is_shutdown}")
    print(f"   bus_a.is_shutdown: {bus_a.is_shutdown}")  # Still active
    print(f"   bus_b.is_shutdown: {bus_b.is_shutdown}")  # Still active

    # Create new aggregator with cascade
    bus_c = PubSub()
    bus_d = PubSub()
    aggregator2 = PubSubAggregator(pubsubs=[bus_c, bus_d])

    print("\n3. Shutting down aggregator2 (with cascade=True):")
    aggregator2.shutdown(cascade=True)
    print(f"   aggregator2.is_shutdown: {aggregator2.is_shutdown}")
    print(f"   bus_c.is_shutdown: {bus_c.is_shutdown}")  # Shutdown
    print(f"   bus_d.is_shutdown: {bus_d.is_shutdown}")  # Shutdown
    print("   ✓ Cascade shutdown also shut down managed instances")


def example_4_cascade_drain() -> None:
    """Example 4: Cascade Drain

    Demonstrates how to cascade drain to managed PubSub instances.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Cascade Drain")
    print("=" * 70)

    # Create PubSub instances
    bus_a = PubSub()
    bus_b = PubSub()

    # Create aggregator
    aggregator = PubSubAggregator(pubsubs=[bus_a, bus_b])

    received_aggregator: list[Message] = []
    received_bus_a: list[Message] = []
    received_bus_b: list[Message] = []

    def handler_aggregator(msg: Message) -> None:
        received_aggregator.append(msg)

    def handler_bus_a(msg: Message) -> None:
        received_bus_a.append(msg)

    def handler_bus_b(msg: Message) -> None:
        received_bus_b.append(msg)

    aggregator.subscribe("test.topic", handler_aggregator, correlation_id="*")
    bus_a.subscribe("test.topic", handler_bus_a)
    bus_b.subscribe("test.topic", handler_bus_b)

    # Publish messages
    print("\n1. Publishing messages:")
    aggregator.publish("test.topic", {"source": "aggregator"})
    bus_a.publish("test.topic", {"source": "bus_a"})
    bus_b.publish("test.topic", {"source": "bus_b"})

    # Drain without cascade (only drains aggregator's internal bus)
    print("\n2. Draining aggregator (no cascade):")
    aggregator.drain()
    print(f"   aggregator received: {len(received_aggregator)}")
    print(f"   bus_a received: {len(received_bus_a)}")
    print(f"   bus_b received: {len(received_bus_b)}")

    # Now drain individual buses
    bus_a.drain()
    bus_b.drain()
    print("\n   After individual drains:")
    print(f"   bus_a received: {len(received_bus_a)}")
    print(f"   bus_b received: {len(received_bus_b)}")

    # Reset and try with cascade
    received_aggregator.clear()
    received_bus_a.clear()
    received_bus_b.clear()

    aggregator.publish("test.topic", {"source": "aggregator2"})
    bus_a.publish("test.topic", {"source": "bus_a2"})
    bus_b.publish("test.topic", {"source": "bus_b2"})

    print("\n3. Draining aggregator (with cascade=True):")
    result = aggregator.drain(cascade=True)
    print(f"   Drain result: {result}")
    print(f"   aggregator received: {len(received_aggregator)}")
    print(f"   bus_a received: {len(received_bus_a)}")
    print(f"   bus_b received: {len(received_bus_b)}")
    print("   ✓ Cascade drain also drained managed instances")


def example_5_one_way_message_flow() -> None:
    """Example 5: One-Way Message Flow

    Demonstrates that PubSubAggregator only forwards messages FROM managed
    PubSub instances TO aggregator subscribers, not the other way around.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: One-Way Message Flow")
    print("=" * 70)

    # Create PubSub instances
    pack_b_bus = PubSub()
    pack_c_bus = PubSub()

    # Create aggregator
    aggregator = PubSubAggregator(pubsubs=[pack_b_bus, pack_c_bus])

    received_aggregator: list[Message] = []
    received_pack_b: list[Message] = []
    received_pack_c: list[Message] = []

    def handler_aggregator(msg: Message) -> None:
        received_aggregator.append(msg)
        print(f"  Aggregator received: {msg.topic} - {msg.data}")

    def handler_pack_b(msg: Message) -> None:
        received_pack_b.append(msg)
        print(f"  Pack-B received: {msg.topic} - {msg.data}")

    def handler_pack_c(msg: Message) -> None:
        received_pack_c.append(msg)
        print(f"  Pack-C received: {msg.topic} - {msg.data}")

    aggregator.subscribe("event.topic", handler_aggregator, correlation_id="*")
    pack_b_bus.subscribe("event.topic", handler_pack_b)
    pack_c_bus.subscribe("event.topic", handler_pack_c)

    # Publish from managed PubSub instances (forwarded to aggregator)
    print("\n1. Publishing from pack_b_bus:")
    pack_b_bus.publish("event.topic", {"source": "pack-b"})
    pack_b_bus.drain()
    aggregator.drain()

    print("\n2. Publishing from pack_c_bus:")
    pack_c_bus.publish("event.topic", {"source": "pack-c"})
    pack_c_bus.drain()
    aggregator.drain()

    # Publish from aggregator (NOT forwarded to managed instances)
    print("\n3. Publishing from aggregator:")
    aggregator.publish("event.topic", {"source": "aggregator"})
    aggregator.drain()
    pack_b_bus.drain()
    pack_c_bus.drain()

    print("\n4. Summary:")
    print(f"   Aggregator received: {len(received_aggregator)} messages")
    print(f"   Pack-B received: {len(received_pack_b)} messages")
    print(f"   Pack-C received: {len(received_pack_c)} messages")
    print("   ✓ Aggregator receives from managed instances")
    print("   ✓ Managed instances do NOT receive from aggregator")


def example_6_real_world_scenario() -> None:
    """Example 6: Real-World Scenario - Multi-Package Event Aggregation

    Demonstrates a realistic scenario where multiple packages/modules
    publish events, and a central component aggregates them.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Real-World Scenario - Multi-Package Event Aggregation")
    print("=" * 70)

    # Simulate PubSub instances from different packages
    database_bus = PubSub()
    api_bus = PubSub()
    cache_bus = PubSub()

    # Central monitoring aggregator
    monitoring_aggregator = PubSubAggregator(pubsubs=[database_bus, api_bus, cache_bus])

    # Central event logger
    all_events: list[dict] = []

    def log_event(msg: Message) -> None:
        """Central logging for all events."""
        event_info = {
            "topic": msg.topic,
            "data": msg.data,
            "correlation_id": msg.correlation_id,
            "timestamp": msg.timestamp.isoformat(),
        }
        all_events.append(event_info)
        print(f"  📝 [{event_info['topic']}] {event_info['data']}")

    # Subscribe to all events
    monitoring_aggregator.subscribe("*", log_event, correlation_id="*")

    # Simulate events from different packages
    print("\n1. Simulating database events:")
    database_bus.publish("db.connection.opened", {"pool_size": 10})
    database_bus.publish("db.query.executed", {"query": "SELECT * FROM users", "duration_ms": 45})
    database_bus.drain()

    print("\n2. Simulating API events:")
    api_bus.publish("api.request.received", {"method": "GET", "path": "/users"})
    api_bus.publish("api.response.sent", {"status_code": 200, "duration_ms": 120})
    api_bus.drain()

    print("\n3. Simulating cache events:")
    cache_bus.publish("cache.hit", {"key": "user:123", "ttl": 3600})
    cache_bus.publish("cache.miss", {"key": "user:456"})
    cache_bus.drain()

    # Drain aggregator to ensure all forwarded messages are processed
    monitoring_aggregator.drain()

    print(f"\n4. Total events logged: {len(all_events)}")
    print("   ✓ All events from different packages were aggregated")
    print("   ✓ Central monitoring received events from all sources")

    # Cleanup
    monitoring_aggregator.shutdown()


def main() -> None:
    """Run all advanced usage examples."""
    print("=" * 70)
    print("SPLURGE PUB-SUB: ADVANCED API USAGE EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates PubSubAggregator usage patterns.")
    print("PubSubAggregator aggregates messages from multiple PubSub instances.")

    try:
        example_1_basic_aggregator()
        example_2_dynamic_add_remove()
        example_3_cascade_shutdown()
        example_4_cascade_drain()
        example_5_one_way_message_flow()
        example_6_real_world_scenario()

        print("\n" + "=" * 70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
