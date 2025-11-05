# Implementation Plan: Correlation ID Feature for Cross-Library Event Tracking

**Date**: 2025-01-17  
**Version**: 1.0  
**Status**: Planning  
**Author**: Jim Schilling  
**Related Research**: `docs/research/research-correlation-id-2025-01-17-001.md`

---

## Executive Summary

This plan implements **correlation ID** support in Splurge Pub-Sub to enable cross-library event tracking and coordination. The feature allows multiple PubSub instances to coordinate event capture using shared correlation IDs, enabling centralized monitoring across library boundaries.

**Key Changes**:
1. Add `correlation_id` field to Message class
2. Add `correlation_id` parameter to PubSub constructor (keyword-only, auto-generates if None)
3. Add `correlation_id` parameter to publish() method (keyword-only, defaults to instance correlation_id)
4. Add `correlation_id` filter to subscribe() method (keyword-only)
5. Implement thread-safe `_correlation_ids` set tracking
6. Support `topic="*"` wildcard for all-topics subscriptions

**Breaking Changes**: This is a breaking change - no backward compatibility maintained.

---

## Stage 1: Core Infrastructure (Task 1.1 - 1.5)

### Task 1.1: Update Message Class

**Objective**: Add correlation_id field to Message dataclass

**Files**:
- `splurge_pub_sub/message.py` - UPDATE Message class

**Steps**:
- [ ] Add `correlation_id: str | None = None` field to Message dataclass
- [ ] Update `__post_init__` validation (no validation needed for correlation_id)
- [ ] Update `__repr__` to include correlation_id
- [ ] Update docstring to document correlation_id field

**Acceptance Criteria**:
- Message can be created with correlation_id
- Message correlation_id defaults to None
- Message repr includes correlation_id
- All existing Message tests updated to work with new field

---

### Task 1.2: Create Correlation ID Validation Helper

**Objective**: Create validation and normalization helper function

**Files**:
- `splurge_pub_sub/pubsub.py` - ADD helper function

**Steps**:
- [ ] Create `_normalize_correlation_id(value: str | None, instance_correlation_id: str) -> str | None` helper
- [ ] Normalize None/'' to instance_correlation_id
- [ ] Check for '*' first (returns None for wildcard)
- [ ] Validate pattern `[a-zA-Z0-9][a-zA-Z0-9\.-_]*` (1-64 chars)
- [ ] Check for consecutive separators (no `..`, `--`, `__`, or combinations like `.-`, `_.`, `-_`)
- [ ] Raise SplurgePubSubValueError for invalid patterns or consecutive separators
- [ ] Create `_generate_correlation_id() -> str` helper that generates pattern-compliant IDs (can use standard UUID)

**Acceptance Criteria**:
- Validation helper correctly normalizes None/''
- Validation helper correctly handles '*' wildcard
- Pattern validation works correctly
- Length validation works correctly
- Generates pattern-compliant correlation_ids

---

### Task 1.3: Update PubSub Constructor

**Objective**: Add correlation_id parameter to PubSub.__init__

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE PubSub.__init__

**Steps**:
- [ ] Add `correlation_id: str | None = None` keyword-only parameter to `__init__`
- [ ] Normalize None/'' using helper function (use instance correlation_id)
- [ ] Validate provided correlation_id using helper function
- [ ] If None/'', auto-generate pattern-compliant correlation_id
- [ ] Store as `self._correlation_id: str`
- [ ] Initialize `self._correlation_ids: set[str] = {self._correlation_id}` (thread-safe)
- [ ] Update docstring with correlation_id parameter documentation
- [ ] Update class docstring examples

**Acceptance Criteria**:
- Constructor accepts correlation_id keyword parameter
- Auto-generates pattern-compliant correlation_id if None/'' provided
- Validates provided correlation_id against pattern
- Instance correlation_id accessible
- _correlation_ids set initialized correctly
- Thread-safe initialization

---

### Task 1.4: Update _SubscriberEntry Structure

**Objective**: Extend _SubscriberEntry to support correlation_id filtering

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE _SubscriberEntry dataclass

**Steps**:
- [ ] Add `correlation_id_filter: str | None = None` field to _SubscriberEntry
- [ ] Keep existing fields (subscriber_id, callback)
- [ ] Update docstring to document correlation_id_filter

**Acceptance Criteria**:
- _SubscriberEntry supports correlation_id_filter
- Backward compatible structure (new field has default)
- Type hints correct

---

### Task 1.5: Add Wildcard Topic Support Infrastructure

**Objective**: Prepare infrastructure for `topic="*"` wildcard subscriptions

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE PubSub class

**Steps**:
- [ ] Add `self._wildcard_subscribers: list[_SubscriberEntry] = []` (for topic="*")
- [ ] Thread-safe list management
- [ ] Update clear() and shutdown() to handle wildcard subscribers

**Acceptance Criteria**:
- Wildcard subscriber registry exists
- Thread-safe operations
- Properly cleaned up on shutdown/clear

---

## Stage 2: Publish Enhancement (Task 2.1 - 2.2)

### Task 2.1: Update Publish Method Signature

**Objective**: Add correlation_id parameter to publish() method

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE publish() method

**Steps**:
- [ ] Add `correlation_id: str | None = None` keyword-only parameter to publish()
- [ ] Normalize None/'' to `self._correlation_id` using helper function
- [ ] Validate '*' raises SplurgePubSubValueError (cannot publish with wildcard)
- [ ] Validate provided correlation_id using helper function
- [ ] Update docstring with correlation_id parameter documentation
- [ ] Update examples in docstring

**Acceptance Criteria**:
- publish() accepts correlation_id keyword parameter
- Defaults to instance correlation_id when None/''
- Raises error if '*' provided
- Validates correlation_id pattern
- Parameter is keyword-only

---

### Task 2.2: Implement Correlation ID Tracking and Message Creation

**Objective**: Track correlation_ids and include in Message

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE publish() method implementation

**Steps**:
- [ ] Add correlation_id to `_correlation_ids` set (thread-safe)
- [ ] Create Message with correlation_id field populated
- [ ] Update Message() call to include correlation_id parameter
- [ ] Ensure thread-safe set operations

**Acceptance Criteria**:
- Published correlation_ids added to _correlation_ids set
- Message includes correlation_id
- Thread-safe set operations
- No race conditions

---

## Stage 3: Subscribe Enhancement (Task 3.1 - 3.3)

### Task 3.1: Update Subscribe Method Signature

**Objective**: Add correlation_id filter parameter to subscribe()

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE subscribe() method

**Steps**:
- [ ] Add `correlation_id: str | None = None` keyword-only parameter to subscribe()
- [ ] Normalize None/'' to `self._correlation_id` using helper function
- [ ] Check for '*' first - store as None (matches any correlation_id)
- [ ] Validate provided correlation_id using helper function
- [ ] Store normalized value in _SubscriberEntry.correlation_id_filter
- [ ] Update docstring with correlation_id parameter documentation
- [ ] Update examples to show correlation_id filtering

**Acceptance Criteria**:
- subscribe() accepts correlation_id keyword parameter
- Normalizes None/'' to instance correlation_id
- '*' stored as None (match any)
- Validates correlation_id pattern
- Parameter is keyword-only

---

### Task 3.2: Implement Topic Wildcard Support

**Objective**: Support `topic="*"` for all-topics subscriptions

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE subscribe() method

**Steps**:
- [ ] Detect `topic="*"` in subscribe()
- [ ] Add to `_wildcard_subscribers` list instead of topic registry
- [ ] Still support pattern matching for other topics
- [ ] Update validation to allow "*" as special topic

**Acceptance Criteria**:
- `topic="*"` subscribes to all topics
- Wildcard subscriptions stored separately
- Topic pattern matching still works for non-wildcard topics
- Validation allows "*" as special case

---

### Task 3.3: Update Subscribe Entry Creation

**Objective**: Store correlation_id_filter in _SubscriberEntry

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE subscribe() method

**Steps**:
- [ ] Create _SubscriberEntry with correlation_id_filter set
- [ ] Handle default vs explicit None distinction
- [ ] Update logging to include correlation_id_filter

**Acceptance Criteria**:
- _SubscriberEntry created with correct correlation_id_filter
- Default correlation_id properly handled
- Explicit None properly stored

---

## Stage 4: Matching Logic (Task 4.1 - 4.2)

### Task 4.1: Implement Correlation ID Matching

**Objective**: Filter subscribers by correlation_id during publish

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE publish() method

**Steps**:
- [ ] Create helper method `_matches_correlation_id(message: Message, entry: _SubscriberEntry) -> bool`
- [ ] Logic: if entry.correlation_id_filter is None, match any
- [ ] Logic: if entry.correlation_id_filter is str, match exactly
- [ ] Integrate into publish() matching logic

**Acceptance Criteria**:
- Correlation ID matching works correctly
- None filter matches any correlation_id
- String filter matches exact correlation_id
- Thread-safe matching

---

### Task 4.2: Integrate Topic and Correlation ID Matching

**Objective**: Combine topic and correlation_id matching in publish()

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE publish() method

**Steps**:
- [ ] Update topic-based subscriber iteration to also check correlation_id
- [ ] Check wildcard subscribers (_wildcard_subscribers) with correlation_id filter
- [ ] Execute callbacks only for matching subscribers
- [ ] Maintain snapshot-then-release pattern for thread safety

**Acceptance Criteria**:
- Subscribers match on BOTH topic AND correlation_id
- Wildcard topic subscribers checked with correlation_id filter
- Pattern topic subscribers checked with correlation_id filter
- Exact topic subscribers checked with correlation_id filter
- Performance acceptable (no significant regression)

---

## Stage 5: Unsubscribe and Clear Updates (Task 5.1 - 5.2)

### Task 5.1: Update Unsubscribe Method

**Objective**: Handle correlation_id in unsubscribe (if needed)

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE unsubscribe() method

**Steps**:
- [ ] Review unsubscribe() - should work with existing subscriber_id
- [ ] Verify works with wildcard subscribers
- [ ] Update logging if needed

**Acceptance Criteria**:
- unsubscribe() works with correlation_id-filtered subscriptions
- unsubscribe() works with wildcard topic subscriptions
- No breaking changes to unsubscribe API

---

### Task 5.2: Update Clear Method

**Objective**: Clear wildcard subscribers in clear()

**Files**:
- `splurge_pub_sub/pubsub.py` - UPDATE clear() method

**Steps**:
- [ ] Clear `_wildcard_subscribers` when clearing all
- [ ] Clear `_wildcard_subscribers` when clearing specific topic (if applicable)
- [ ] Update `_correlation_ids` set management (decide: clear or keep?)

**Acceptance Criteria**:
- clear() handles wildcard subscribers
- clear() behavior is clear and documented
- Thread-safe clearing operations

---

## Stage 6: Testing (Task 6.1 - 6.5)

### Task 6.1: Update Existing Message Tests

**Objective**: Update all Message tests for correlation_id field

**Files**:
- `tests/unit/test_core_message_basic.py` - UPDATE tests
- `tests/unit/test_core_message_properties.py` - UPDATE tests

**Steps**:
- [ ] Update all Message creation tests to include correlation_id=None
- [ ] Add tests for Message with correlation_id
- [ ] Update property-based tests if needed
- [ ] Ensure all tests pass

**Acceptance Criteria**:
- All existing Message tests pass
- New correlation_id tests added
- 100% Message test coverage maintained

---

### Task 6.2: Constructor and Correlation ID Tests

**Objective**: Test PubSub constructor and correlation_id management

**Files**:
- `tests/unit/test_core_pubsub_basic.py` - UPDATE tests
- `tests/unit/test_core_pubsub_properties.py` - NEW/UPDATE tests

**Steps**:
- [ ] Test auto-generation of pattern-compliant correlation_id
- [ ] Test custom correlation_id in constructor (valid pattern)
- [ ] Test correlation_id validation (invalid patterns raise errors)
- [ ] Test consecutive separator validation (raises errors for `..`, `--`, `__`, etc.)
- [ ] Test None/'' normalization to instance correlation_id
- [ ] Test _correlation_ids set initialization
- [ ] Test thread-safety of _correlation_ids
- [ ] Test correlation_id accessibility

**Acceptance Criteria**:
- Constructor tests cover all correlation_id scenarios
- Thread-safety verified
- All tests pass

---

### Task 6.3: Publish Correlation ID Tests

**Objective**: Test publish() with correlation_id

**Files**:
- `tests/unit/test_core_pubsub_basic.py` - UPDATE tests

**Steps**:
- [ ] Test default correlation_id usage (None/'' normalization)
- [ ] Test correlation_id override in publish() (valid pattern)
- [ ] Test '*' raises error in publish()
- [ ] Test invalid pattern raises error in publish()
- [ ] Test consecutive separators raise error in publish()
- [ ] Test _correlation_ids set updates
- [ ] Test Message includes correlation_id
- [ ] Test thread-safety of publish with correlation_id

**Acceptance Criteria**:
- All publish correlation_id scenarios tested
- Thread-safety verified
- Message correlation_id verified

---

### Task 6.4: Subscribe Correlation ID Tests

**Objective**: Test subscribe() with correlation_id filtering

**Files**:
- `tests/unit/test_core_pubsub_basic.py` - UPDATE tests
- `tests/unit/test_core_pubsub_properties.py` - NEW/UPDATE tests

**Steps**:
- [ ] Test default correlation_id filter (None/'' normalized to instance)
- [ ] Test explicit correlation_id filter (valid pattern)
- [ ] Test correlation_id='*' (match any, stored as None)
- [ ] Test invalid pattern raises error in subscribe()
- [ ] Test consecutive separators raise error in subscribe()
- [ ] Test topic="*" with correlation_id filter
- [ ] Test topic pattern with correlation_id filter
- [ ] Test multiple subscribers with different correlation_id filters
- [ ] Test matching logic (correlation_id + topic)

**Acceptance Criteria**:
- All subscribe correlation_id scenarios tested
- Matching logic verified
- Edge cases covered

---

### Task 6.5: Integration and Cross-Instance Tests

**Objective**: Test end-to-end correlation_id workflows

**Files**:
- `tests/integration/test_pubsub_scenarios.py` - UPDATE tests
- New integration tests if needed

**Steps**:
- [ ] Test complete workflow: publish with correlation_id, subscribe with filter
- [ ] Test multiple correlation_ids
- [ ] Test wildcard topic with correlation_id
- [ ] Test pattern topic with correlation_id
- [ ] Test unsubscribe with correlation_id-filtered subscriptions
- [ ] Test clear() with correlation_id subscriptions

**Acceptance Criteria**:
- End-to-end workflows work correctly
- Integration tests pass
- Real-world scenarios covered

---

## Stage 7: Documentation (Task 7.1 - 7.4)

### Task 7.1: Update API Reference

**Objective**: Document correlation_id in API reference

**Files**:
- `docs/api/API-REFERENCE.md` - UPDATE documentation

**Steps**:
- [ ] Update PubSub constructor documentation
- [ ] Update publish() method documentation
- [ ] Update subscribe() method documentation
- [ ] Update Message class documentation
- [ ] Add correlation_id examples
- [ ] Document topic="*" wildcard behavior

**Acceptance Criteria**:
- API reference complete and accurate
- All examples updated
- Correlation_id behavior clearly documented

---

### Task 7.2: Update README and Details

**Objective**: Update main documentation files

**Files**:
- `README.md` - UPDATE
- `docs/README-DETAILS.md` - UPDATE

**Steps**:
- [ ] Add correlation_id feature description
- [ ] Add cross-library coordination examples
- [ ] Update usage examples
- [ ] Document breaking changes

**Acceptance Criteria**:
- Main documentation updated
- Examples demonstrate correlation_id usage
- Breaking changes clearly documented

---

### Task 7.3: Update Examples

**Objective**: Update code examples

**Files**:
- `examples/api_usage.py` - UPDATE examples

**Steps**:
- [ ] Add correlation_id examples
- [ ] Add cross-library coordination example
- [ ] Add topic="*" wildcard example
- [ ] Update existing examples if needed

**Acceptance Criteria**:
- Examples demonstrate correlation_id features
- Examples are clear and runnable

---

### Task 7.4: Update Type Hints and Exports

**Objective**: Ensure type hints and exports are correct

**Files**:
- `splurge_pub_sub/types.py` - REVIEW/UPDATE if needed
- `splurge_pub_sub/__init__.py` - REVIEW/UPDATE if needed

**Steps**:
- [ ] Review type hints for correlation_id
- [ ] Add CorrelationId type alias if needed
- [ ] Update __all__ exports if needed
- [ ] Ensure mypy strict compliance

**Acceptance Criteria**:
- Type hints correct and complete
- mypy strict passes
- Exports correct

---

## Implementation Order

1. **Stage 1**: Core Infrastructure (Tasks 1.1-1.4)
2. **Stage 2**: Publish Enhancement (Tasks 2.1-2.2)
3. **Stage 3**: Subscribe Enhancement (Tasks 3.1-3.3)
4. **Stage 4**: Matching Logic (Tasks 4.1-4.2)
5. **Stage 5**: Unsubscribe and Clear (Tasks 5.1-5.2)
6. **Stage 6**: Testing (Tasks 6.1-6.5) - Parallel with implementation
7. **Stage 7**: Documentation (Tasks 7.1-7.4) - Parallel with implementation

---

## Acceptance Criteria (Overall)

- ✅ All tests pass (existing + new)
- ✅ 100% backward compatibility breaking changes are intentional and documented
- ✅ Thread-safety verified
- ✅ Performance acceptable (no significant regression)
- ✅ Documentation complete
- ✅ Type hints correct (mypy strict)
- ✅ Code quality (ruff clean)
- ✅ Correlation ID feature works end-to-end
- ✅ Topic="*" wildcard works
- ✅ Cross-library coordination use case supported

---

## Risk Mitigation

1. **Breaking Changes**: Documented clearly, no backward compatibility maintained
2. **Performance**: Monitor publish() performance with correlation_id filtering
3. **Thread Safety**: Comprehensive thread-safety testing
4. **Complexity**: Keep matching logic clear and well-tested

---

## Success Metrics

- All 316+ existing tests pass (updated)
- 50+ new correlation_id tests added
- 100% code coverage maintained
- Documentation complete
- Zero runtime errors in examples
- Performance within 10% of baseline

---

**Status**: Ready for implementation.

