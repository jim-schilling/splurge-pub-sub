# Research: Correlation ID Feature for Cross-Library Event Tracking

**Date**: 2025-01-17  
**Version**: 1.0  
**Status**: Research Phase  
**Sequence**: 001

---

## Executive Summary

This research document proposes adding **correlation ID** support to Splurge Pub-Sub to enable cross-library event tracking and coordination. The feature allows multiple PubSub instances (from different Splurge libraries) to coordinate event capture using shared correlation IDs, enabling centralized monitoring and debugging across library boundaries.

**Key Use Case**: When multiple Splurge libraries (splurge-dsv, splurge-tabular, splurge-typer, etc.) each have their own PubSub instances, a high-level process can use a single correlation_id across all instances and monitor events through a single callback.

---

## 1. Problem Statement

### Current Limitations

Currently, Splurge Pub-Sub instances operate independently:
- Each PubSub instance maintains its own subscription registry
- No mechanism to correlate events across multiple PubSub instances
- Difficult to trace events through a multi-library workflow
- No way to filter subscriptions by event correlation

### Use Case: Multi-Library Coordination

In the Splurge ecosystem:
- **splurge-dsv**: CSV/data processing library with its own PubSub instance
- **splurge-tabular**: Table manipulation library with its own PubSub instance  
- **splurge-typer**: Type inference library with its own PubSub instance
- **High-level process**: Orchestrates multiple libraries in a single workflow

**Goal**: Enable a single monitoring callback to capture events from all library PubSub instances when they share the same correlation_id.

### Example Scenario

```python
# High-level process sets correlation_id for entire workflow
correlation_id = "workflow-abc-123"

# splurge-dsv PubSub instance
dsv_bus = PubSub(correlation_id=correlation_id)
dsv_bus.publish("dsv.file.loaded", {"file": "data.csv"})

# splurge-tabular PubSub instance  
tabular_bus = PubSub(correlation_id=correlation_id)
tabular_bus.publish("tabular.table.created", {"rows": 100})

# splurge-typer PubSub instance
typer_bus = PubSub(correlation_id=correlation_id)
typer_bus.publish("typer.command.executed", {"command": "process"})

# Single monitoring callback can subscribe to all with same correlation_id
monitor_bus = PubSub()
monitor_bus.subscribe("*", monitor_all_events, correlation_id=correlation_id)
# This callback receives events from dsv_bus, tabular_bus, AND typer_bus
```

---

## 2. Proposed Solution

### 2.1 Core Design Principles

1. **Instance-Level Correlation ID**: Each PubSub instance has a default `correlation_id`
2. **Per-Message Override**: Publish can override instance correlation_id per message
3. **Subscription Filtering**: Subscribers can filter by correlation_id
4. **Automatic Tracking**: Published correlation_ids are automatically tracked in a thread-safe set
5. **Topic Wildcard Support**: `topic="*"` subscribes to all topics for a given correlation_id

### 2.2 API Changes

#### PubSub Constructor

```python
def __init__(
    self,
    *,
    error_handler: ErrorHandler | None = None,
    correlation_id: str | None = None,
) -> None:
    """Initialize PubSub instance.
    
    Args:
        error_handler: Optional error handler (keyword-only)
        correlation_id: Optional correlation ID. If None or '', auto-generates.
                       Must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]* (1-64 chars)
                       with no consecutive '.', '-', or '_' characters.
                       Must be passed as keyword argument.
    """
```

**Behavior**:
- If `correlation_id` is `None` or `''`, auto-generate: `str(uuid4())`
- Otherwise, validate pattern `[a-zA-Z0-9][a-zA-Z0-9\.-_]*` (1-64 chars) and check for consecutive separators
- Store as `self._correlation_id: str`
- Initialize `self._correlation_ids: set[str] = {self._correlation_id}` (thread-safe)

#### Publish Method

```python
def publish(
    self,
    topic: str,
    data: MessageData | None = None,
    metadata: Metadata | None = None,
    *,
    correlation_id: str | None = None,
) -> None:
    """Publish message with optional correlation_id override.
    
    Args:
        topic: Topic identifier
        data: Message payload
        metadata: Optional metadata
        correlation_id: Optional correlation ID override. If None or '',
                       uses self._correlation_id. If '*', raises error.
                       Otherwise must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]*
                       (1-64 chars) with no consecutive '.', '-', or '_' characters.
                       Must be passed as keyword.
    """
```

**Behavior**:
- If `correlation_id` is `None` or `''`, use `self._correlation_id`
- If `correlation_id` is `'*'`, raise `SplurgePubSubValueError` (cannot publish with wildcard)
- Otherwise, validate pattern `[a-zA-Z0-9][a-zA-Z0-9\.-_]*` (1-64 chars) and check for consecutive separators
- Add `correlation_id` to `self._correlation_ids` set (thread-safe)
- Include `correlation_id` in Message object
- Match subscribers based on topic AND correlation_id filter

#### Subscribe Method

```python
def subscribe(
    self,
    topic: str,
    callback: Callback,
    *,
    correlation_id: str | None = None,
) -> SubscriberId:
    """Subscribe with optional correlation_id filter.
    
    Args:
        topic: Topic identifier or "*" for all topics
        callback: Callback function
        correlation_id: Optional filter. If None or '', uses instance 
                       correlation_id. If '*', matches any correlation_id.
                       Otherwise must match pattern [a-zA-Z0-9][a-zA-Z0-9\.-_]*
                       (1-64 chars) with no consecutive '.', '-', or '_' characters.
                       Must be passed as keyword.
    """
```

**Behavior**:
- If `correlation_id` is `None` or `''`, use `self._correlation_id` (filter to instance)
- If `correlation_id` is `'*'`, match ANY correlation_id (no filter)
- Otherwise, validate pattern `[a-zA-Z0-9][a-zA-Z0-9\.-_]*` (1-64 chars) and check for consecutive separators and use as filter
- Store `correlation_id_filter` in `_SubscriberEntry` (None = match any, str = filter to that value)
- Support `topic="*"` to match all topics

#### Message Class

```python
@dataclass(frozen=True)
class Message:
    topic: Topic
    data: MessageData
    correlation_id: str | None = None  # NEW FIELD
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 2.3 Subscription Matching Logic

**Matching Rules**:

1. **Topic Matching**:
   - `topic="*"`: Matches any topic
   - Exact match: `topic == message.topic`
   - Pattern match: Use `TopicPattern` if topic contains wildcards

2. **Correlation ID Matching**:
   - If subscriber has `correlation_id_filter=None`: Match ANY correlation_id (wildcard '*')
   - If subscriber has `correlation_id_filter=str`: Match only that exact correlation_id
   - Normalize None/'' to instance correlation_id before storing filter

3. **Combined Matching**:
   - Message matches subscriber if BOTH topic AND correlation_id match

**Pseudo-code**:
```python
def matches_subscriber(message: Message, entry: _SubscriberEntry) -> bool:
    # Topic matching
    topic_match = (
        entry.topic_exact == "*" or  # Wildcard = match any topic
        entry.topic_exact == message.topic or  # Exact match
        (entry.topic_pattern and entry.topic_pattern.matches(message.topic))  # Pattern match
    )
    
    # Correlation ID matching
    if entry.correlation_id_filter is None:  # None = wildcard '*' = match any
        correlation_match = True
    else:
        correlation_match = entry.correlation_id_filter == message.correlation_id
    
    return topic_match and correlation_match
```

**Validation Logic**:
```python
def normalize_correlation_id(value: str | None, instance_correlation_id: str) -> str | None:
    """Normalize correlation_id value.
    
    Args:
        value: Correlation ID value (None, '', '*', or string)
        instance_correlation_id: Instance default correlation_id
    
    Returns:
        None if wildcard (match any), str if specific filter
    """
    if value is None or value == '':
        return instance_correlation_id  # Use instance default
    if value == '*':
        return None  # Wildcard = match any
    # Validate pattern: [a-zA-Z0-9][a-zA-Z0-9\.-_]* (1-64 chars)
    if not (1 <= len(value) <= 64):
        raise SplurgePubSubValueError(f"correlation_id length must be 1-64 chars, got {len(value)}")
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\.\-_]*$', value):
        raise SplurgePubSubValueError(
            f"correlation_id must match pattern [a-zA-Z0-9][a-zA-Z0-9\\.-_]* (1-64 chars), got: {value!r}"
        )
    # Check for consecutive separators (., -, _) - same or different
    separators = '.-_'
    for i in range(len(value) - 1):
        if value[i] in separators and value[i + 1] in separators:
            raise SplurgePubSubValueError(
                f"correlation_id cannot contain consecutive separator characters ('.', '-', '_'), got: {value!r}"
            )
    return value
```

### 2.4 Data Structure Changes

#### Enhanced _SubscriberEntry

```python
@dataclass
class _SubscriberEntry:
    subscriber_id: SubscriberId
    callback: Callback
    correlation_id_filter: str | None = None  # None = match any
    topic_pattern: TopicPattern | None = None  # For pattern matching
    topic_exact: str | None = None  # For exact match or "*"
```

**Registry Structure**:
- Keep current `dict[Topic, list[_SubscriberEntry]]` structure
- During publish, iterate through ALL topic entries and filter by correlation_id
- For `topic="*"` subscriptions, maintain separate registry or check all topics

**Alternative**: Use a unified registry structure:
```python
_subscribers: list[_SubscriberEntry]  # Flat list, filter during publish
```

**Recommendation**: Keep topic-based registry for performance, add correlation_id filtering during iteration.

---

## 3. Implementation Considerations

### 3.1 Thread Safety

- `_correlation_ids: set[str]` must be thread-safe
- Use `threading.RLock` (already in use) for set operations
- Consider `set` operations: `add()`, `__contains__()`, iteration

### 3.2 Performance

- Current design: O(topics) iteration for exact matches
- With correlation_id: Same iteration, but filter by correlation_id
- Wildcard topic (`*`): May require checking all topics
- Pattern topics: Already handled efficiently

**Optimization**: Could maintain separate registry for `topic="*"` subscriptions to avoid checking all topics.

### 3.3 Backward Compatibility

**Decision**: No backward compatibility required. This is a breaking change.

- Existing code will need to update Message construction
- Existing subscriptions will need explicit `correlation_id=None` to match any
- All tests will need updates

### 3.4 Validation

**Correlation ID Validation Rules**:
- Pattern: `[a-zA-Z0-9][a-zA-Z0-9\.-_]*` (first char can be letter or digit, rest alphanumeric/dot/dash/underscore)
- Length: 1-64 characters
- No consecutive separators: Cannot have consecutive `.`, `-`, or `_` characters
- Normalization:
  - `None` or `''` → use instance `correlation_id`
  - `'*'` → wildcard (match any) - check for this FIRST before pattern validation
  - Valid string → use as filter value
- Validation order: Check for `'*'` first, then validate pattern and consecutive separators
- Auto-generated correlation_ids: Can use standard UUID format (e.g., `str(uuid4())`)

**Example Valid Correlation IDs**:
- `"abc123"` ✓
- `"request-456"` ✓
- `"session.abc_123"` ✓
- `"A1-b.2_c"` ✓
- `"550e8400-e29b-41d4-a716-446655440000"` ✓ (UUID format)
- `"123abc"` ✓ (can start with digit)
- `"abc.def-ghi"` ✓

**Example Invalid Correlation IDs**:
- `""` ✗ (empty, but normalized to instance correlation_id)
- `"*"` ✗ (wildcard, but normalized to None for matching)
- `"a" * 65` ✗ (too long)
- `"abc..def"` ✗ (consecutive dots)
- `"abc--def"` ✗ (consecutive dashes)
- `"abc__def"` ✗ (consecutive underscores)
- `"abc.-def"` ✗ (consecutive separators: dot then dash)
- `"abc_.def"` ✗ (consecutive separators: underscore then dot)

---

## 4. Design Alternatives Considered

### Alternative 1: Correlation ID in Metadata Only

**Rejected**: Correlation ID should be first-class for filtering/subscription performance.

### Alternative 2: UUID-Only Correlation IDs

**Rejected**: Users may want custom string identifiers (e.g., "request-123", "session-abc").

### Alternative 3: Separate Correlation Registry

**Rejected**: Adds complexity. Simpler to filter during publish iteration.

### Alternative 4: Correlation ID Required (No None)

**Rejected**: Breaks too much existing code. Allow None for flexibility.

---

## 5. Testing Strategy

### Test Categories

1. **Constructor Tests**:
   - Auto-generation of correlation_id when None
   - Custom correlation_id provided
   - Instance correlation_id accessible

2. **Publish Tests**:
   - Default correlation_id used when not provided
   - Override correlation_id per publish
   - Correlation_id added to _correlation_ids set
   - Message includes correlation_id

3. **Subscribe Tests**:
   - Default correlation_id filter (instance correlation_id)
   - Explicit correlation_id filter
   - correlation_id=None matches any
   - Topic="*" with correlation_id filter

4. **Matching Tests**:
   - Topic match + correlation_id match = delivery
   - Topic match + correlation_id mismatch = no delivery
   - Topic="*" + correlation_id match = delivery
   - Multiple subscribers with different correlation_id filters

5. **Cross-Instance Tests**:
   - Multiple PubSub instances with same correlation_id
   - Subscription to correlation_id across instances (if applicable)

6. **Thread Safety Tests**:
   - Concurrent publish with correlation_ids
   - Concurrent subscription with correlation_ids
   - _correlation_ids set thread-safety

---

## 6. Open Questions

1. **Cross-Instance Subscription**: If Library A and Library B have separate PubSub instances, can a subscriber on Instance C subscribe to correlation_id events from A and B? 
   - **Answer**: No - subscriptions are per-instance. Each library's PubSub maintains its own registry. The correlation_id allows filtering within an instance.
   - **Note**: For cross-library coordination, libraries would need to forward/re-publish events to a central monitoring PubSub instance, or use a shared singleton PubSub instance. This correlation_id feature enables filtering within any single instance.

2. **Wildcard Topic Performance**: How to efficiently handle `topic="*"` subscriptions?
   - **Proposal**: Maintain separate list/set of wildcard subscribers, check separately during publish

3. **Correlation ID Validation**: What pattern should correlation_id follow?
   - **Answer**: Pattern `[a-zA-Z][a-zA-Z0-9\.-_]*` with length 1-64 characters. First char must be letter, rest can be alphanumeric, dot, dash, or underscore.

4. **Empty String and None**: How to handle empty string?
   - **Answer**: Treat `None` and `''` as same - both mean "use instance correlation_id". Wildcard `'*'` means "match any".

---

## 7. Implementation Phases

### Phase 1: Core Infrastructure
- Add `correlation_id` to Message class
- Add `correlation_id` parameter to PubSub.__init__
- Add `_correlation_ids` set management
- Update `_SubscriberEntry` structure

### Phase 2: Publish Enhancement
- Add `correlation_id` parameter to publish()
- Automatic tracking in `_correlation_ids`
- Include correlation_id in Message creation

### Phase 3: Subscribe Enhancement
- Add `correlation_id` parameter to subscribe()
- Implement correlation_id filtering logic
- Support `topic="*"` wildcard

### Phase 4: Testing & Documentation
- Update all existing tests
- Add comprehensive correlation_id tests
- Update API documentation
- Update examples

---

## 8. Success Criteria

- ✅ PubSub instances can be initialized with correlation_id
- ✅ Publish can override correlation_id per message
- ✅ Subscriptions can filter by correlation_id
- ✅ Topic="*" subscribes to all topics for correlation_id
- ✅ Thread-safe correlation_id tracking
- ✅ All tests pass
- ✅ Documentation updated
- ✅ Performance acceptable (no significant regression)

---

## 9. Related Documentation

- `docs/research/research-2025-11-04-splurge-pub-sub.md` - Original framework design
- `docs/plans/plan-implementation-phase2-2025-11-04.md` - Phase 2 implementation plan
- `docs/api/API-REFERENCE.md` - Current API reference

---

## 10. Next Steps

1. Review and approve research document
2. Create detailed implementation plan
3. Begin Phase 1 implementation
4. Iterate through testing phases
5. Update documentation

---

**Status**: Ready for review and implementation planning.

