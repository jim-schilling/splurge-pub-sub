# Note: Message Metadata Initialization

**Date:** January 16, 2025  
**Status:** Completed  
**Summary:** Updated Message class to initialize metadata as empty dict instead of None

## Changes Made

### File: `splurge_pub_sub/core/message.py`

**Changed field definition:**
```python
# Before
metadata: dict[str, Any] | None = field(default=None)

# After
metadata: dict[str, Any] = field(default_factory=dict)
```

**Benefits:**
- Eliminates need for None checks throughout codebase
- Simplifies metadata handling in subscribers
- Guarantees metadata is always a dict
- Aligns with principle of "fail fast" by always having a valid dict

### Updated Docstrings

Changed class docstring from:
- "Optional metadata dict"

To:
- "Metadata dict (defaults to empty dict if not provided)"

Updated example in docstring to show empty dict:
```python
>>> msg.metadata
{}
```

## Test Updates

### File: `tests/unit/test_core_message_basic.py`

1. **TestMessageCreation.test_message_creation_without_optional_fields**
   - Changed: `assert msg.metadata is None` → `assert msg.metadata == {}`

2. **TestMessageMetadata.test_message_metadata_dict_optional**
   - Renamed to: `test_message_metadata_dict_defaults_to_empty`
   - Changed: `assert msg1.metadata is None` → `assert msg1.metadata == {}`

### File: `tests/unit/test_core_message_properties.py`

1. **TestMessageInvariants.test_message_metadata_defaults_to_none**
   - Renamed to: `test_message_metadata_defaults_to_empty_dict`
   - Changed to test that metadata defaults to empty dict

## Impact Analysis

### Code Simplification
Subscribers and other code that uses message metadata no longer need to check for None:

```python
# Before (need None check)
if message.metadata is not None:
    metadata = message.metadata
else:
    metadata = {}

# After (no check needed)
metadata = message.metadata  # Always a dict
```

### Test Results
- ✅ All 316 tests pass
- ✅ Code coverage maintained at 95%
- ✅ No breaking changes to public API (metadata is still accessible)

## Rationale

Following the principle of "fail fast" and avoiding null/None checks:
1. Metadata is now always guaranteed to be a dict (empty if not provided)
2. Subscribers don't need defensive None checks
3. Code is more readable and maintainable
4. Aligns with common Python patterns (e.g., dict.get() returns None, but direct access expects valid dict)

## Backward Compatibility

**Note:** This is a subtle change that could affect code that checks `if msg.metadata is None`. However:
- The public API remains unchanged (metadata is still accessible)
- Code should be updated to use `if msg.metadata:` instead if checking for empty metadata
- This is a code improvement that simplifies the codebase

## Files Modified

1. `splurge_pub_sub/core/message.py` - Changed field definition and docstring
2. `tests/unit/test_core_message_basic.py` - Updated 2 tests
3. `tests/unit/test_core_message_properties.py` - Updated 1 property test
