"""Integration tests for realistic PubSub scenarios.

Test real-world use cases and multi-component interactions.
"""

import threading
from typing import Any

from splurge_pub_sub import Message, PubSub


class TestIntegrationScenarios:
    """Integration test scenarios."""

    def test_scenario_user_created_event_multiple_subscribers(self) -> None:
        """Test realistic user creation event with multiple subscribers."""
        bus = PubSub()

        logged_events = []
        notifications_sent = []
        analytics_recorded = []

        def logging_subscriber(msg: Message) -> None:
            logged_events.append({"event": msg.topic, "data": msg.data})

        def notification_subscriber(msg: Message) -> None:
            notifications_sent.append(
                {
                    "email": msg.data.get("email"),
                    "name": msg.data.get("name"),
                }
            )

        def analytics_subscriber(msg: Message) -> None:
            analytics_recorded.append({"event_type": msg.topic, "timestamp": msg.timestamp})

        # Subscribe all handlers
        bus.subscribe("user.created", logging_subscriber)
        bus.subscribe("user.created", notification_subscriber)
        bus.subscribe("user.created", analytics_subscriber)

        # Publish user created event
        user_data = {"id": 123, "name": "Alice", "email": "alice@example.com"}
        bus.publish("user.created", user_data)

        # Verify all subscribers received event
        assert len(logged_events) == 1
        assert len(notifications_sent) == 1
        assert len(analytics_recorded) == 1

        assert logged_events[0]["data"]["name"] == "Alice"
        assert notifications_sent[0]["email"] == "alice@example.com"
        assert analytics_recorded[0]["event_type"] == "user.created"

    def test_scenario_cascading_events_subscribers_publish(self) -> None:
        """Test cascading events where subscribers publish new events."""
        bus = PubSub()

        event_sequence = []

        def user_created_handler(msg: Message) -> None:
            event_sequence.append("user_created")
            # Subscriber publishes new event
            bus.publish("email.welcome.send", {"to": msg.data.get("email")})

        def email_sent_handler(msg: Message) -> None:
            event_sequence.append("email_sent")
            # Another subscriber publishes
            bus.publish("audit.log.created", {"action": "email_sent"})

        def audit_handler(msg: Message) -> None:
            event_sequence.append("audit_logged")

        bus.subscribe("user.created", user_created_handler)
        bus.subscribe("email.welcome.send", email_sent_handler)
        bus.subscribe("audit.log.created", audit_handler)

        bus.publish("user.created", {"email": "user@example.com"})

        # All cascading events should have been delivered
        assert event_sequence == ["user_created", "email_sent", "audit_logged"]

    def test_scenario_multi_threaded_publishers_subscribers(self) -> None:
        """Test real-world concurrent pub/sub operations."""
        bus = PubSub()
        received_count = {"count": 0}
        lock = threading.Lock()

        def subscriber(msg: Message) -> None:
            with lock:
                received_count["count"] += 1

        # Subscribe multiple times
        for _ in range(5):
            bus.subscribe("events", subscriber)

        def publisher_thread(thread_id: int) -> None:
            for i in range(10):
                bus.publish("events", {"thread": thread_id, "seq": i})

        # Publish from multiple threads
        threads = [threading.Thread(target=publisher_thread, args=(i,)) for i in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 3 threads × 10 publishes × 5 subscribers = 150 received
        assert received_count["count"] == 150

    def test_scenario_high_subscriber_load(self) -> None:
        """Test performance with many subscribers."""
        bus = PubSub()
        received = []

        def make_subscriber(idx: int) -> Any:
            def sub(msg: Message) -> None:
                received.append(idx)

            return sub

        # Create 500 subscribers
        for i in range(500):
            bus.subscribe("topic", make_subscriber(i))

        # Publish single message
        bus.publish("topic", {"data": "test"})

        # All should have received
        assert len(received) == 500

    def test_scenario_resource_cleanup_on_shutdown(self) -> None:
        """Test that shutdown properly cleans up resources."""
        bus = PubSub()
        received = []

        def subscriber(msg: Message) -> None:
            received.append(msg)

        bus.subscribe("topic", subscriber)
        bus.publish("topic", {"data": "test1"})
        assert len(received) == 1

        bus.shutdown()

        # After shutdown, messages shouldn't be delivered
        bus.publish("topic", {"data": "test2"})
        assert len(received) == 1

    def test_scenario_exception_isolation(self) -> None:
        """Test that one subscriber's failure doesn't cascade."""
        bus = PubSub()
        results = []

        def failing_subscriber(msg: Message) -> None:
            raise ValueError("This subscriber always fails")

        def good_subscriber_1(msg: Message) -> None:
            results.append("subscriber1")

        def good_subscriber_2(msg: Message) -> None:
            results.append("subscriber2")

        # First failing sub, then good ones
        bus.subscribe("topic", failing_subscriber)
        bus.subscribe("topic", good_subscriber_1)
        bus.subscribe("topic", good_subscriber_2)

        # Publish should not raise despite failing subscriber
        bus.publish("topic", {"data": "test"})

        # Good subscribers should have executed
        assert "subscriber1" in results
        assert "subscriber2" in results

    def test_scenario_context_manager_lifecycle(self) -> None:
        """Test that context manager properly manages lifecycle."""
        received = []

        def subscriber(msg: Message) -> None:
            received.append(msg)

        with PubSub() as bus:
            bus.subscribe("topic", subscriber)
            bus.publish("topic", {"data": "test1"})
            assert len(received) == 1
            # Bus is still active

        # After context exit, should not receive
        # (would need to create another instance to verify)
        assert len(received) == 1
