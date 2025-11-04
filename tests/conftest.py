"""Pytest configuration and shared fixtures for Splurge Pub-Sub tests."""

import logging
from collections.abc import Callable
from typing import Any

import pytest

from splurge_pub_sub import Message, PubSub

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


# ============================================================================
# Fixtures: Test Data
# ============================================================================


@pytest.fixture
def sample_topics() -> dict[str, str]:
    """Sample valid topic names."""
    return {
        "simple": "user.created",
        "nested": "order.payment.completed",
        "deep": "system.process.worker.task.completed",
        "single": "event",
    }


@pytest.fixture
def sample_data() -> dict[str, Any]:
    """Sample message data of various types."""
    return {
        "dict": {"id": 123, "name": "Alice"},
        "list": [1, 2, 3, 4, 5],
        "string": "test event",
        "int": 42,
        "float": 3.14,
        "none": None,
        "nested": {"user": {"id": 1, "prefs": {"theme": "dark"}}},
    }


@pytest.fixture
def sample_callbacks() -> dict[str, Callable[[Message], None]]:
    """Sample callback functions."""
    received: dict[str, list[Message]] = {}

    def make_callback(name: str) -> Callable[[Message], None]:
        """Create a callback that stores received messages."""
        if name not in received:
            received[name] = []

        def callback(msg: Message) -> None:
            received[name].append(msg)

        return callback

    # Create a few sample callbacks
    callbacks = {
        "callback1": make_callback("cb1"),
        "callback2": make_callback("cb2"),
        "callback3": make_callback("cb3"),
    }

    # Store received messages on callbacks for test access
    callbacks["_received"] = received  # type: ignore

    return callbacks


# ============================================================================
# Fixtures: PubSub Instances
# ============================================================================


@pytest.fixture
def pubsub() -> PubSub:
    """Fresh PubSub instance for each test."""
    return PubSub()


@pytest.fixture
def pubsub_with_subscribers(
    pubsub: PubSub,
    sample_callbacks: dict[str, Callable[[Message], None]],
) -> tuple[PubSub, dict[str, str]]:
    """PubSub with pre-subscribed callbacks.

    Returns:
        Tuple of (pubsub instance, dict mapping callback names to subscriber IDs)
    """
    subscriber_ids = {}

    # Subscribe callbacks to different topics
    subscriber_ids["cb1"] = pubsub.subscribe(
        "user.created",
        sample_callbacks["callback1"],
    )
    subscriber_ids["cb2"] = pubsub.subscribe(
        "user.created",
        sample_callbacks["callback2"],
    )
    subscriber_ids["cb3"] = pubsub.subscribe(
        "order.created",
        sample_callbacks["callback3"],
    )

    return pubsub, subscriber_ids


# ============================================================================
# Fixtures: Logging Capture
# ============================================================================


@pytest.fixture
def log_capture(caplog) -> Any:
    """Fixture to capture and inspect log messages."""
    caplog.set_level(logging.DEBUG)
    return caplog
