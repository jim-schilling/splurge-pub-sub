# Implementation Plan: Splurge Pub-Sub Phase 2 (Filtering, Error Handlers, Decorators)

**Date**: 2025-11-04  
**Version**: 1.0  
**Status**: Planning  
**Author**: Jim Schilling  

---

## Executive Summary

**Phase 2** extends the Phase 1 fan-out event bus with advanced features:
1. **Topic Filtering & Wildcards** - Pattern-based message routing
2. **Error Handlers** - Customizable exception handling per bus
3. **Decorator API** - Simplified subscription syntax

---

## Stage 1: Topic Filtering (Task 1.1 - 1.3)

### Task 1.1: Design Filter System

**Objective**: Implement topic wildcard pattern matching

**Files**:
- `splurge_pub_sub/core/filters.py` - NEW filter logic
- `splurge_pub_sub/core/pubsub.py` - UPDATE PubSub class

**Steps**:
- [ ] Create `TopicPattern` class with wildcard support (* = any segment, ? = any char)
- [ ] Implement pattern matching logic
- [ ] Add filtered subscription tracking to PubSub
- [ ] Update Message class to support hierarchical topics
- [ ] Add `subscribe_filtered()` method to PubSub

**Acceptance Criteria**:
- Pattern matching works: `user.*`, `*.created`, `order.*.paid`
- Subscribers receive only matching messages
- Exact matches still supported
- Performance acceptable for 100+ patterns

---

### Task 1.2: Implement Filter Operations

**Objective**: Add filter support to core PubSub

**Steps**:
- [ ] Implement `TopicPattern.matches(topic: str) -> bool`
- [ ] Add filtered subscriber registry
- [ ] Implement snapshot-then-release pattern for filtered subscribers
- [ ] Thread-safety for filter operations
- [ ] Document filter behavior and limits

**Acceptance Criteria**:
- All patterns match correctly
- Thread-safe concurrent filter operations
- No performance regression on fan-out mode
- Backward compatible with exact-match subscriptions

---

### Task 1.3: Filter Tests

**Objective**: Comprehensive filter testing

**File**: `tests/unit/test_core_filters_basic.py`

**Test Cases**:
- [ ] Pattern matching: wildcards, single char, exact match
- [ ] Subscriber receives only matching messages
- [ ] Multiple patterns for single subscriber
- [ ] Mixed exact/filter subscriptions
- [ ] Performance with many patterns
- [ ] Thread-safety with concurrent patterns

**Acceptance Criteria**:
- 85%+ coverage of filter logic
- All pattern types tested
- Edge cases handled

---

## Stage 2: Error Handlers (Task 2.1 - 2.3)

### Task 2.1: Design Error Handler System

**Objective**: Allow custom exception handling

**Files**:
- `splurge_pub_sub/core/errors.py` - NEW error handling
- `splurge_pub_sub/core/pubsub.py` - UPDATE PubSub class

**Steps**:
- [ ] Create `ErrorHandler` type alias: `Callable[[Exception, str], None]`
- [ ] Add error_handler parameter to PubSub constructor
- [ ] Implement default error handler (logging)
- [ ] Add error handler to Message delivery
- [ ] Support multiple error handlers per bus
- [ ] Document error handler contract

**Acceptance Criteria**:
- Error handlers receive exception and topic info
- Thread-safe error handler execution
- Custom error handlers can implement retries, dead-lettering, etc.
- Default handler logs errors appropriately

---

### Task 2.2: Implement Error Handler Operations

**Objective**: Integrate error handling into publish flow

**Steps**:
- [ ] Update `publish()` to call error_handler on callback exception
- [ ] Maintain exception isolation (one handler failure doesn't cascade)
- [ ] Allow error handler to re-publish or queue messages
- [ ] Thread-safe error handler state
- [ ] Support error handler chaining

**Acceptance Criteria**:
- Error handlers called on subscriber exception
- No deadlocks with re-entrant error handlers
- Errors in error handler itself handled gracefully
- Performance impact minimal

---

### Task 2.3: Error Handler Tests

**Objective**: Comprehensive error handler testing

**File**: `tests/unit/test_core_errors_basic.py`

**Test Cases**:
- [ ] Custom error handler called on exception
- [ ] Error handler receives correct info
- [ ] Multiple error handlers work sequentially
- [ ] Error handler re-publishing works
- [ ] Error handler exceptions don't cascade
- [ ] Default error handler logs appropriately
- [ ] Thread-safety with concurrent errors

**Acceptance Criteria**:
- 85%+ coverage of error handler logic
- All scenarios tested
- Edge cases handled

---

## Stage 3: Decorator API (Task 3.1 - 3.3)

### Task 3.1: Design Decorator API

**Objective**: Implement @bus.on() decorator syntax

**Files**:
- `splurge_pub_sub/core/decorators.py` - NEW decorator logic
- `splurge_pub_sub/core/pubsub.py` - UPDATE PubSub class

**Steps**:
- [ ] Create `on()` method returning decorator
- [ ] Support topic parameter: `@bus.on("user.created")`
- [ ] Support pattern parameter: `@bus.on("user.*")`
- [ ] Decorator registers function as callback
- [ ] Decorator returns original function (chainable)
- [ ] Support multiple decorators on same function

**Acceptance Criteria**:
- `@bus.on("topic")` syntax works
- Decorated functions work as callbacks
- Chaining supported
- Type hints proper

---

### Task 3.2: Implement Decorator Operations

**Objective**: Integrate decorator into PubSub

**Steps**:
- [ ] Implement `PubSub.on(topic)` method returning decorator
- [ ] Decorator automatically subscribes function
- [ ] Support for both async and sync callbacks (Phase 2)
- [ ] Subscriber ID returned from decorator if needed
- [ ] Thread-safe decorator execution

**Acceptance Criteria**:
- Decorated functions work identically to manual subscribe
- No performance overhead
- Proper error handling for decorated callbacks
- Chainable decorators work

---

### Task 3.3: Decorator Tests

**Objective**: Comprehensive decorator testing

**File**: `tests/unit/test_core_decorators_basic.py`

**Test Cases**:
- [ ] Decorator syntax works
- [ ] Decorated function receives messages
- [ ] Multiple decorators on same bus
- [ ] Decorator chaining
- [ ] Decorated function exceptions handled
- [ ] Decorator with filters (Phase 2.5)
- [ ] Dynamic decoration (runtime)

**Acceptance Criteria**:
- 85%+ coverage of decorator logic
- All patterns tested
- Edge cases handled

---

## Stage 4: Integration Tests (Task 4.1 - 4.2)

### Task 4.1: Phase 2 Integration Scenarios

**Objective**: Test Phase 2 features together

**File**: `tests/integration/test_phase2_scenarios.py`

**Scenarios**:
- [ ] Filtering + error handlers + decorators together
- [ ] High-volume filtered messages with error handling
- [ ] Decorator-based cascade with filtering
- [ ] Error handler with decorated callbacks
- [ ] Mixed Phase 1 and Phase 2 features

**Acceptance Criteria**:
- All scenarios work correctly
- No regressions from Phase 1
- Performance acceptable

---

### Task 4.2: Backward Compatibility Testing

**Objective**: Ensure Phase 1 compatibility

**File**: `tests/integration/test_phase1_compatibility.py`

**Tests**:
- [ ] All Phase 1 tests still pass
- [ ] Phase 1 API unchanged
- [ ] No performance regression
- [ ] Phase 1 code works with Phase 2 libraries

**Acceptance Criteria**:
- 100% Phase 1 tests pass
- Performance within 10% of Phase 1
- All Phase 1 features work

---

## Stage 5: Code Quality (Task 5.1 - 5.3)

### Task 5.1: Type Checking and Linting

**Steps**:
- [ ] mypy strict mode: 100% pass
- [ ] ruff: No warnings
- [ ] Coverage: 85%+ for new code
- [ ] All docstrings complete

**Acceptance Criteria**:
- mypy passes strict mode
- ruff passes
- Coverage >= 85% for Phase 2 code

---

### Task 5.2: Documentation

**Steps**:
- [ ] Update API reference with Phase 2
- [ ] Add decorator examples
- [ ] Document filtering patterns
- [ ] Document error handler patterns
- [ ] Migration guide (Phase 1 → Phase 2)

**Acceptance Criteria**:
- All new APIs documented
- Examples provided
- Clear migration path

---

### Task 5.3: Refactoring Review

**Steps**:
- [ ] Review SOLID principles
- [ ] Check for code duplication
- [ ] Optimize hot paths
- [ ] Performance profile

**Acceptance Criteria**:
- Code follows SOLID
- No duplication
- Performance maintained

---

## Summary

**Phase 2 adds**:
✅ Topic filtering with wildcards  
✅ Error handler customization  
✅ Decorator-based subscriptions  
✅ Backward compatible with Phase 1  
✅ 85%+ coverage on all new code  

**Deliverables**:
- 3 new core modules (filters, errors, decorators)
- 3 test modules (filters, errors, decorators)
- 2 integration test modules (Phase 2 scenarios, compatibility)
- Updated documentation

**Success Criteria**:
- All 81 Phase 1 tests pass
- 50+ new Phase 2 tests pass
- 85%+ coverage on new code
- 0 regressions from Phase 1
- mypy strict + ruff clean
- Documentation complete

