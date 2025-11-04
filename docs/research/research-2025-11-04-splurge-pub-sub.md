# Research: Lightweight Thread-Safe Pub-Sub Framework Design

**Date**: 2025-11-04  
**Version**: 2.0  
**Status**: Research Phase  

---

## Executive Summary

This research document proposes an initial design for **Splurge Pub-Sub**, a lightweight, thread-safe publish-subscribe framework for Python 3.10+. The framework implements the **Pub-Sub architectural pattern** to support decoupled, event-driven communication in Python applications while maintaining thread safety for concurrent scenarios.

**Key Clarification**: This document focuses on **Phase 1 (MVP)** which implements a specific pub-sub variant: the **Fan-Out Event Bus**. This is one pattern within the broader pub-sub ecosystem; the framework is designed to extend to other pub-sub variants in future phases.

---

## 1. Problem Statement

### Background: Pub-Sub Pattern

The **Publish-Subscribe (Pub-Sub)** pattern decouples message producers (publishers) from message consumers (subscribers) through a mediator. Multiple pub-sub variants exist, each suited to different use cases:

| Variant | Characteristics | Use Case |
|---------|-----------------|----------|
| **Fan-Out Event Bus** | All subscribers receive all published messages | Event notification, state change broadcasts |
| **Message Queue** | Each message consumed by ONE subscriber (competing consumers) | Task distribution, work queues |
| **Filtered Topics** | Subscribers specify topic patterns; messages routed by topic | Sensor data routing, domain events |
| **Request-Reply** | Pub-Sub with synchronous responses | RPC-style communication |
| **Distributed** | Cross-process or network communication | Microservices, clustered systems |

### Phase 1 Scope: Fan-Out Event Bus

This research focuses on **Phase 1**, implementing a **Fan-Out Event Bus** variant where:
- Multiple subscribers can register for topics
- All registered subscribers receive ALL published messages for their topic
- Synchronous callback execution (no queuing)
- In-process communication only
- Thread-safe for concurrent pub/sub operations

### Current Challenges (Phase 1 Scope)

Many Python applications require in-process event-driven communication where:
- Components need to communicate without tight coupling
- Multiple threads may publish/subscribe simultaneously
- Solutions must be lightweight with minimal dependencies
- Performance must be reasonable for typical use cases
- Thread safety is essential for multi-threaded applications

### Future Phases

Later phases may implement alternative pub-sub variants (message queues, competing consumers, filtering, async, distributed), but are explicitly **out of scope for Phase 1**.

---

## 2. Pub-Sub Pattern Overview & Phase 1 Positioning

### Pub-Sub as an Architectural Pattern

The Publish-Subscribe pattern is a **message-oriented middleware** architecture where:
- **Publishers** send messages without knowing who receives them
- **Subscribers** express interest in message topics without knowing publishers
- A **mediator** (broker/bus) routes messages based on topics/subscriptions
- **Decoupling** occurs in both space (publishers/subscribers unaware of each other) and time (queuing variants)

### Phase 1: Fan-Out Event Bus Variant

The Phase 1 implementation is a **specific variant** of pub-sub optimized for:
- **In-process communication** (single Python process)
- **Synchronous delivery** (callbacks execute immediately)
- **Fan-out semantics** (all subscribers receive all messages)
- **Thread safety** (concurrent pub/sub operations)
- **Zero external dependencies**

**Example Use Case**: A web application where user authentication, logging, email notifications, and analytics all need to react to a "user.created" event without tight coupling.

### Architectural Constraints (Phase 1 Only)

These are **intentional limitations** for Phase 1 MVP, not permanent framework constraints:

| Constraint | Reason | Future Flexibility |
|-----------|--------|-------------------|
| Synchronous callbacks only | Simplicity, no async complexity | Phase 2: Add async variant |
| All subscribers receive all messages | Fan-out semantics | Phase 2: Add topic filtering |
| Single-process only | No network overhead | Phase 3+: Add distributed support |
| No message queuing | In-memory callback execution | Phase 2: Add queue variant |
| No competing consumers | Not applicable to fan-out | Phase 2+: Queue-based variant |

### Framework Extensibility

The architecture is designed to support future variants:
- Core interfaces defined for subscribers/messages
- Plugin points for different mediation strategies
- Clear separation between transport and business logic
- Documented extension points for custom behaviors

---

## 2. Existing Solutions Analysis

### 2.1 Standard Library Approaches

#### `queue.Queue`
- **Pros**: Built-in, thread-safe, FIFO ordering
- **Cons**: Point-to-point only, not pub-sub, designed for producer-consumer
- **Fit**: Could be a foundation, but needs wrapping


### 2.2 Analysis Summary

**Recommendation**: Build lightweight custom framework leveraging:
- `threading.Lock` / `threading.RLock` for thread safety
- Standard `dict` and `list` for subscriber storage
- Callback-based synchronous pattern
- Clear, Pythonic API design

---

## 3. Proposed Architecture (Phase 1: Fan-Out Event Bus)

### 3.1 Core Components

#### 3.1.1 PubSub (Registry)
```
PubSub
├── Manages topic subscriptions
├── Dispatches messages to subscribers
├── Thread-safe via RLock
└── Instantiable (not a singleton)
```

**Module**: `pubsub.py`

**Responsibilities**:
- Register/unregister subscribers for topics
- Dispatch messages to all subscribers
- Handle subscriber callback execution
- Protect internal state with locks

**Extensibility**: Phase 1 provides base `PubSub` class with fan-out semantics. Future phases can create variant subclasses (e.g., `QueuedPubSub`, `FilteredPubSub`) while maintaining common interface.

#### 3.1.2 Subscriber Model
```
Subscriber
├── Callback function
├── Optional context/filter
└── Optional exception handling
```

**Design Choices**:
- Callbacks are synchronous functions
- Optional type hints on callback signature
- Automatic subscription cleanup on exceptions (configurable)

#### 3.1.3 Message Model
```
Message
├── Topic (str)
├── Data (Any)
├── Metadata (dict, optional)
└── Timestamp (auto-generated)
```

**Design Choices**:
- Messages are immutable (or effectively immutable)
- Topic strings use dot notation (e.g., `user.created`, `payment.failed`)
- Optional metadata for context passing

### 3.2 Thread Safety Strategy

#### Lock Granularity
- **RLock (Reentrant Lock)** for the subscription registry
- Locks held only during critical sections:
  - Subscriber registration/unregistration
  - Getting subscriber list snapshot
  - Minimal lock duration during dispatch

#### Pattern: Snapshot + Release
```python
with self._lock:
    subscribers = list(self._subscribers[topic])  # Snapshot
# Unlock before executing callbacks
for subscriber in subscribers:
    subscriber.callback(message)
```

**Benefits**:
- Prevents deadlocks from nested publishes
- Allows subscribers to publish during callbacks
- Minimizes lock contention

#### Race Condition Handling
1. **Subscription during publish**: Subscriber added during iteration won't receive current message (acceptable)
2. **Unsubscription during publish**: Subscriber will receive no more messages (safe)
3. **Multiple publishers**: All writes serialized by lock
4. **Callback exceptions**: Don't propagate to publisher (isolation)

### 3.3 API Design

#### Core Operations

```python
# Create pub-sub instance
bus = PubSub()

# Subscribe with callback
def on_user_created(message: Message) -> None:
    print(f"User created: {message.data}")

subscriber_id = bus.subscribe("user.created", on_user_created)

# Publish message
bus.publish("user.created", {"id": 123, "name": "Alice"})

# Unsubscribe
bus.unsubscribe("user.created", subscriber_id)

# Context manager support
with PubSub() as bus:
    bus.subscribe("event.topic", callback)
    bus.publish("event.topic", data)
```

#### Advanced Features (Phase 2+)

These features are **explicitly out of scope for Phase 1** but represent planned extensibility:

- **Topic wildcards**: `user.*` or `*.created` (Phase 2)
- **Subscriber filters**: Only execute if condition met (Phase 2)
- **Error handlers**: Custom exception handling (Phase 2)
- **Async support**: Optional async callbacks (Phase 3)
- **Decorator API**: `@bus.on("topic")` (Phase 2)
- **Message queuing**: Decouple publisher/subscriber in time (Phase 3+)
- **Competing consumers**: Multiple subscribers compete for single message (Phase 3+)
- **Distributed support**: Cross-process or network pub-sub (Phase 4+)
- **Message persistence**: Historical replay and archiving (Phase 4+)

### 3.4 Exception Handling

#### Strategy
1. **Subscriber callback exceptions** are caught and logged (not propagated)
2. **Publisher exceptions** are propagated (framework-level errors)
3. **Configurable error handler** for subscriber callback failures
4. **Custom exception hierarchy** defined in `exceptions.py`

#### Exception Types

```
SplurgePubSubError (base)
├── SplurgePubSubValueError (invalid input)
├── SplurgePubSubTypeError (type violation)
├── SplurgePubSubLookupError (topic/subscriber not found)
├── SplurgePubSubRuntimeError (execution failures)
└── SplurgePubSubOSError (system errors)
```

### 3.5 Lifecycle and Resource Management

#### Context Manager Support
```python
with EventBus() as bus:
    # Setup
    # Cleanup happens here
```

#### Explicit Cleanup
```python
bus.clear()  # Remove all subscribers
bus.shutdown()  # Full cleanup
```

---

## 4. Design Decisions & Rationale (Phase 1)

| Decision | Choice | Rationale | Future Flexibility |
|----------|--------|-----------|-------------------|
| **Concurrency Model** | Synchronous callbacks + RLock | Simple, no callback overhead, suitable for in-process | Phase 3: Add async variant |
| **Lock Type** | RLock | Allows re-entrant publishes within callbacks | Can be replaced with lock-free structures |
| **Callback Exceptions** | Caught and logged | Prevent one subscriber failure from affecting others | Phase 2: Add error handlers |
| **Topic Structure** | String-based (dot notation) | Simple, flexible, language-agnostic | Phase 2: Add wildcard patterns |
| **Message Format** | Custom Message class | Type-safe, extensible, consistent | Extensible for headers, metadata |
| **Subscription ID** | UUID or integer | Uniqueness guarantee, good for cleanup | Standard approach, proven |
| **Single Instance** | Allow multiple instances | Flexibility, not forced as singleton | Each instance isolated |
| **Dependencies** | Zero external | Lightweight, minimal installation size | Maintained for core framework |
| **Delivery Model** | Fan-out (all subscribers) | Matches event notification patterns | Phase 3+: Add queue/competing consumer |
| **In-process Only** | No network/IPC | Simplicity, performance | Phase 4+: Add distributed variant |

---

## 5. Implementation Roadmap

### Phase 1: Core Fan-Out Event Bus (MVP)
- [ ] `PubSub` class with fan-out pub/sub in `pubsub.py`
- [ ] `Message` class with topic and data
- [ ] Thread-safe subscription registry (RLock-based)
- [ ] Exception hierarchy
- [ ] Unit tests (85%+ coverage)
- [ ] Basic documentation
- **Semantics**: All subscribers receive all messages synchronously

### Phase 2: Filtering & Advanced Features
- [ ] Topic wildcards and pattern matching
- [ ] Subscriber filters (conditional delivery)
- [ ] Error handlers (custom exception handling)
- [ ] Decorator API (`@bus.on("topic")`)
- [ ] Async callback support (requires async event loop integration)
- **New Capability**: Selective message delivery

### Phase 3: Queuing & Message Semantics
- [ ] `QueuedPubSub` variant (async, buffered)
- [ ] Competing consumers (queue-based load distribution)
- [ ] Message ordering guarantees
- [ ] Performance monitoring and metrics
- **New Capability**: Time-decoupled pub-sub

### Phase 4: Advanced Capabilities & Production Hardening
- [ ] Distributed pub-sub (cross-process/network)
- [ ] Message persistence and replay
- [ ] Event sourcing support
- [ ] Dead-letter queues
- [ ] Stress testing and optimization
- **New Capability**: Multi-process and distributed scenarios

---

## 6. Performance Considerations (Phase 1)

### Expected Performance Characteristics (Fan-Out Event Bus)
- **Subscribe**: O(1) - Simple list append
- **Unsubscribe**: O(n) - Linear search and removal
- **Publish**: O(n) - Iterate all subscribers
- **Memory**: O(n) - Where n = total subscribers across all topics

### Optimization Opportunities (Future Phases)
- **Phase 2**: Subscriber removal via weak references or indexed lookup
- **Phase 3**: Topic index optimization for wildcard patterns
- **Phase 3+**: Batch publishing for bulk operations
- **Phase 4+**: Lock-free data structures for extreme concurrency scenarios

### Phase 1 Limitations & Trade-offs
- **Synchronous execution**: Blocking publisher until all callbacks complete (acceptable for in-process)
- **No buffering**: Fast publishers may overwhelm slow subscribers
- **Linear unsubscribe**: O(n) cost; mitigated by typical small subscriber counts
- **All-or-nothing delivery**: No selective delivery per subscriber

**These limitations are intentional for Phase 1 MVP simplicity; future phases address them.**

### Not In Scope for Phase 1
- Distributed pub-sub (cross-network latency)
- Message persistence and storage
- Complex filtering and routing
- Ordered subscription/delivery guarantees
- Throughput optimization beyond simple implementations

---

## 7. Testing Strategy (Phase 1)

### Unit Tests (Fan-Out Event Bus)
- Subscription and unsubscription operations
- Publishing and message delivery to multiple subscribers
- Thread safety with concurrent subscriptions/publishes
- Exception handling in subscriber callbacks
- Message immutability or defensive copying
- Context manager lifecycle behavior
- Subscription ID uniqueness and cleanup

### Integration Tests
- Multi-threaded scenarios with competing publishers/subscribers
- Nested publishes (subscriber publishing during callback)
- Subscriber callback exceptions don't affect other subscribers
- Proper resource cleanup on bus shutdown
- Fan-out semantics (verify all subscribers receive message)

### Performance & Stress Tests (Phase 1+)
- Throughput with many subscribers (1000+)
- Latency of publish operations under load
- Lock contention measurement with concurrent operations
- Memory usage with large subscriber sets
- Callback latency distribution

### Property-Based Testing (Hypothesis)
- Randomized subscriber/publisher sequences maintain invariants
- All subscribers notified for published message (delivery invariant)
- Unsubscribed subscribers receive no further messages
- Thread-safety invariants under concurrent stress

### Excluded from Phase 1 Testing
- Distributed scenarios
- Message persistence
- Async callback execution
- Complex filtering patterns

---

## 8. API Documentation Requirements (Phase 1)

### Public API (Module: `pubsub.py`)
- `PubSub`: Main class for pub-sub operations (fan-out variant)
- `Message`: Data structure for published messages
- `Subscriber`: Type hint for callback functions
- Custom exception types (exception hierarchy)

### Future API Extensibility
- `QueuedPubSub`: Message queue variant (Phase 3)
- `FilteredPubSub`: Topic filtering variant (Phase 2+)
- Additional variants as needed

### Documentation Should Include
- Quick start guide with fan-out examples
- API reference for core `PubSub` operations
- Thread-safety guarantees and limitations
- Exception handling guide
- Common patterns (event propagation, cascade operations)
- Performance guidelines for typical use cases
- Roadmap for future pub-sub variants
- Extension points for custom variant implementations

---

## 9. Compatibility & Standards (Phase 1)

### Python Version
- **Target**: Python 3.10+
- **Type Checking**: Full mypy support (strict mode)
- **Linting**: Ruff checks (style, security, performance)

### Coding Standards
- PEP 8 compliance (Ruff enforcement)
- Type annotations on all functions/methods
- Google-style docstrings for public API
- Module-level `__all__` exports
- Domain tracking (DOMAINS list)

### Quality Gates
- 85%+ unit test coverage
- 95%+ combined (unit + integration) coverage
- Type checking with mypy (strict mode)
- Linting with Ruff (no warnings)
- No security issues identified
- Project README with feature overview

---

## 10. Conclusion

The proposed **Splurge Pub-Sub** framework begins with a **Phase 1 Fan-Out Event Bus** implementation that provides:

✅ **Lightweight & Focused**: MVP targeting specific pub-sub variant (fan-out events)  
✅ **Thread-Safe**: RLock-based synchronization for concurrent operations  
✅ **Simple, Pythonic API**: Familiar patterns following Python conventions  
✅ **Type-Safe**: Full type annotations with mypy strict mode  
✅ **Extensible Foundation**: Generic `PubSub` class designed for variant subclasses  
✅ **Zero Dependencies**: Standalone implementation (except internal Splurge exceptions)  

### Key Design Decisions
- **Foundational Class**: `PubSub` (not variant-specific name like `EventBus`)
- **Module**: `pubsub.py` for core implementation
- **Extensibility**: Phase 1 implements base `PubSub` with fan-out semantics
- **Future Variants**: `QueuedPubSub`, `FilteredPubSub`, etc. as subclasses/variants

### Key Clarifications
- **Not a complete pub-sub framework yet**: Phase 1 implements fan-out variant only
- **Intentional constraints**: Synchronous, in-process, all-subscribers-receive-all-messages
- **Planned extensibility**: Roadmap includes queues, filtering, async, distribution
- **Proven pattern**: Follows established Observer/Pub-Sub patterns with extensible design

### Next Steps
1. Implement Phase 1 `PubSub` class with core operations
2. Validate with comprehensive test suite
3. Gather feedback from real usage
4. Plan Phase 2 (filtering, error handlers, async)
5. Extend to additional pub-sub variants based on demand

---

## 11. References & Resources

### Pub-Sub Pattern Resources
- [Enterprise Integration Patterns: Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/PublishSubscribeChannel.html)
- [Observer Pattern (Gang of Four)](https://refactoring.guru/design-patterns/observer)
- [Event-Driven Architecture](https://en.wikipedia.org/wiki/Event-driven_architecture)

### Python Documentation
- [threading — Thread-based parallelism](https://docs.python.org/3/library/threading.html)
- [queue — A synchronized queue class](https://docs.python.org/3/library/queue.html)
- [contextlib — Context managers](https://docs.python.org/3/library/contextlib.html)

### Design Patterns & Best Practices
- SOLID Principles for extensibility
- Event Bus pattern for decoupling
- Message-oriented middleware concepts
- Thread safety patterns

---

