"""
Splurge Pub-Sub: PubSubSolo Usage Examples

This script demonstrates the usage of PubSubSolo, a scoped singleton wrapper
for PubSub instances that enables multiple packages to have their own singleton
instances that can be aggregated via PubSubAggregator.

Run with:
    python examples/api_solo_usage.py
    python -m examples.api_solo_usage
"""

from splurge_pub_sub import (
    Message,
    PubSubAggregator,
    PubSubSolo,
)


def example_1_basic_singleton() -> None:
    """Example 1: Basic Singleton Usage

    Demonstrates that PubSubSolo provides singleton instances per scope.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Singleton Usage")
    print("=" * 70)

    # Reset any existing instances for clean example state
    for scope in PubSubSolo.get_all_scopes():
        PubSubSolo.shutdown(scope=scope)

    print("\n1. Getting singleton instance for 'package_a'")
    bus_a = PubSubSolo.get_instance(scope="package_a")
    print(f"   Instance created: {bus_a}")

    print("\n2. Getting same instance again (same scope)")
    bus_a2 = PubSubSolo.get_instance(scope="package_a")
    print(f"   Same instance: {bus_a is bus_a2}")  # True

    print("\n3. Getting instance for different scope")
    bus_b = PubSubSolo.get_instance(scope="package_b")
    print(f"   Different instance: {bus_a is not bus_b}")  # True


def example_2_multiple_packages() -> None:
    """Example 2: Multiple Packages with Their Own Singletons

    Demonstrates how different packages can each have their own singleton instance.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Multiple Packages with Their Own Singletons")
    print("=" * 70)

    # Reset any existing instances for clean example state
    for scope in PubSubSolo.get_all_scopes():
        PubSubSolo.shutdown(scope=scope)

    print("\n1. Simulating package_a")
    bus_a = PubSubSolo.get_instance(scope="package_a")
    events_a: list[Message] = []

    @bus_a.on("package_a.event")
    def handle_package_a_event(msg: Message) -> None:
        events_a.append(msg)
        print(f"  [Package A] Received: {msg.topic} - {msg.data}")

    print("\n2. Simulating package_b")
    bus_b = PubSubSolo.get_instance(scope="package_b")
    events_b: list[Message] = []

    @bus_b.on("package_b.event")
    def handle_package_b_event(msg: Message) -> None:
        events_b.append(msg)
        print(f"  [Package B] Received: {msg.topic} - {msg.data}")

    print("\n3. Simulating package_c")
    bus_c = PubSubSolo.get_instance(scope="package_c")
    events_c: list[Message] = []

    @bus_c.on("package_c.event")
    def handle_package_c_event(msg: Message) -> None:
        events_c.append(msg)
        print(f"  [Package C] Received: {msg.topic} - {msg.data}")

    print("\n4. Publishing events from each package")
    bus_a.publish("package_a.event", {"data": "from package A"})
    bus_b.publish("package_b.event", {"data": "from package B"})
    bus_c.publish("package_c.event", {"data": "from package C"})

    # Drain all buses
    bus_a.drain()
    bus_b.drain()
    bus_c.drain()

    print(f"\n5. Events received: A={len(events_a)}, B={len(events_b)}, C={len(events_c)}")
    print("   Each package received its own events")


def example_3_aggregation() -> None:
    """Example 3: Aggregating PubSubSolo Instances

    Demonstrates how to aggregate multiple PubSubSolo instances using PubSubAggregator.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Aggregating PubSubSolo Instances")
    print("=" * 70)

    # Reset any existing instances for clean example state
    for scope in PubSubSolo.get_all_scopes():
        PubSubSolo.shutdown(scope=scope)

    print("\n1. Creating singleton instances for different packages")
    dsv_bus = PubSubSolo.get_instance(scope="splurge_dsv")
    tabular_bus = PubSubSolo.get_instance(scope="splurge_tabular")
    typer_bus = PubSubSolo.get_instance(scope="splurge_typer")

    print("   Created 3 singleton instances (different scopes)")

    print("\n2. Creating central monitoring aggregator")
    monitoring_aggregator = PubSubAggregator(pubsubs=[dsv_bus, tabular_bus, typer_bus])
    print("   Aggregator created with 3 PubSubSolo instances")

    # Central event logger
    all_events: list[dict] = []

    def log_event(msg: Message) -> None:
        """Central logging for all events."""
        event_info = {
            "topic": msg.topic,
            "data": msg.data,
        }
        all_events.append(event_info)
        print(f"  [MONITOR] {msg.topic}: {msg.data}")

    print("\n3. Subscribing to all events via aggregator")
    monitoring_aggregator.subscribe("*", log_event, correlation_id="*")

    print("\n4. Publishing events from different packages")
    dsv_bus.publish("dsv.file.loaded", {"file": "data.csv"})
    tabular_bus.publish("tabular.table.created", {"rows": 100})
    typer_bus.publish("typer.command.executed", {"command": "process"})

    # Drain all buses
    dsv_bus.drain()
    tabular_bus.drain()
    typer_bus.drain()
    monitoring_aggregator.drain()

    print(f"\n5. Total events logged: {len(all_events)}")
    print("   ✓ All events from different packages were aggregated")


def example_4_convenience_methods() -> None:
    """Example 4: Using Convenience Methods

    Demonstrates using PubSubSolo convenience methods that delegate to a scope.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Using Convenience Methods")
    print("=" * 70)

    # Reset any existing instances for clean example state
    for scope in PubSubSolo.get_all_scopes():
        PubSubSolo.shutdown(scope=scope)

    received: list[Message] = []

    def handler(msg: Message) -> None:
        received.append(msg)
        print(f"  Received: {msg.topic} - {msg.data}")

    print("\n1. Using convenience methods with scope parameter")
    PubSubSolo.subscribe("test.topic", handler, scope="convenience_test")
    print("   Subscribed via PubSubSolo.subscribe()")

    print("\n2. Publishing via convenience method")
    PubSubSolo.publish("test.topic", {"data": "test"}, scope="convenience_test")
    print("   Published via PubSubSolo.publish()")

    # Get instance to drain
    bus = PubSubSolo.get_instance(scope="convenience_test")
    bus.drain()

    print(f"\n3. Events received: {len(received)}")
    print("   ✓ Convenience methods work correctly")


def example_5_real_world_scenario() -> None:
    """Example 5: Real-World Multi-Package Scenario

    Demonstrates a realistic scenario where multiple packages publish events
    and a central component aggregates them.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Real-World Multi-Package Scenario")
    print("=" * 70)

    # Reset any existing instances for clean example state
    for scope in PubSubSolo.get_all_scopes():
        PubSubSolo.shutdown(scope=scope)

    # Simulate PubSubSolo instances from different packages
    database_bus = PubSubSolo.get_instance(scope="database_package")
    api_bus = PubSubSolo.get_instance(scope="api_package")
    cache_bus = PubSubSolo.get_instance(scope="cache_package")

    # Central monitoring aggregator
    monitoring_aggregator = PubSubAggregator(pubsubs=[database_bus, api_bus, cache_bus])

    # Central event logger
    all_events: list[dict] = []

    def log_event(msg: Message) -> None:
        """Central logging for all events."""
        event_info = {
            "topic": msg.topic,
            "data": msg.data,
            "timestamp": msg.timestamp.isoformat(),
        }
        all_events.append(event_info)
        print(f"  📝 [{event_info['topic']}] {event_info['data']}")

    # Subscribe to all events
    monitoring_aggregator.subscribe("*", log_event, correlation_id="*")

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
    """Run all PubSubSolo examples."""
    print("\n" + "#" * 70)
    print("# SPLURGE PUB-SUB: PUBSUBSOLO USAGE EXAMPLES")
    print("#" * 70)

    try:
        example_1_basic_singleton()
        example_2_multiple_packages()
        example_3_aggregation()
        example_4_convenience_methods()
        example_5_real_world_scenario()

        print("\n" + "#" * 70)
        print("# ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("#" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
