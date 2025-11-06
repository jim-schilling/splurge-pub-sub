# Changelog

### [2025.2.0] - 2025-11-06

#### Changed
- **Version Bump**: Updated version to 2025.2.0 for patch release in `pyproject.toml` and `__init__.py`
- Consolidated `correlation_id` generation and validation checks from `pubsub.py` and `message.py` into `utility.py` for shared use
  - New functions:
    - `is_valid_correlation_id(correlation_id: str) -> bool`
    - `validate_correlation_id(correlation_id: str) -> None`
    - `generate_correlation_id() -> str`
    - Updated all relevant code and tests to use new validation functions from `utility.py` instead of duplicating logic
- Changed allowable pattern for `correlation_id` to `[a-zA-Z0-9][a-zA-Z0-9\.-_]*[a-zA-Z0-9]` (to require starting and ending with alphanumeric character)
  - Updated validation logic and tests to reflect new pattern requirement

### [2025.1.0] - 2025-11-05

#### Added
- **Correlation ID Support**: Added comprehensive correlation ID feature for cross-library event tracking and coordination
  - `PubSub.__init__()` now accepts optional `correlation_id` keyword parameter (auto-generates UUID if not provided)
  - `Message` class now includes `correlation_id` field for event tracking
  - `PubSub.publish()` accepts optional `correlation_id` keyword parameter (defaults to instance correlation_id)
  - `PubSub.subscribe()` accepts optional `correlation_id` keyword parameter for filtering (supports wildcard `'*'` to match any)
  - Correlation ID pattern validation: `[a-zA-Z0-9][a-zA-Z0-9\.-_]*` (1-64 characters, no consecutive separators)
  - Thread-safe `_correlation_ids` set tracks all published correlation IDs
  - Support for wildcard topic subscription (`topic="*"`) combined with correlation ID filtering
- **Public Properties**: Added read-only properties for accessing internal state via public API
  - `PubSub.correlation_id` - Get instance correlation ID
  - `PubSub.correlation_ids` - Get set of all published correlation IDs (copy)
  - `PubSub.is_shutdown` - Check shutdown state
  - `PubSub.subscribers` - Get topic-based subscribers dictionary (copy)
  - `PubSub.wildcard_subscribers` - Get wildcard subscribers list (copy)
- **Message Validation**: Added `correlation_id` pattern validation in `Message.__post_init__()`
  - Validates pattern, length, and consecutive separator rules
  - Disallows empty string and wildcard `'*'` (only for filters, not concrete values)
- **Documentation**: Added comprehensive correlation ID examples and usage patterns
  - Updated API reference with correlation ID documentation
  - Added cross-library coordination example in README
  - Added correlation ID filtering example in `examples/api_usage.py`
- **Tests**: Added 43 new tests for correlation ID functionality
  - 30 tests in `test_core_correlation_id_basic.py` for correlation ID features
  - 13 tests in `test_core_message_basic.py` for Message correlation_id validation

#### Updated
- **API Changes**: Made `error_handler` parameter keyword-only in `PubSub.__init__()` for better API clarity
- **Test Suite**: Updated all tests to use public properties instead of private attributes
  - Replaced `bus._correlation_id` with `bus.correlation_id`
  - Replaced `bus._correlation_ids` with `bus.correlation_ids`
  - Replaced `bus._is_shutdown` with `bus.is_shutdown`
  - Replaced `bus._subscribers` with `bus.subscribers`
- **Documentation**: Updated API reference, README, and examples to reflect new correlation ID features
- **Examples**: Enhanced `examples/api_usage.py` to demonstrate correlation ID properties and usage

#### Breaking Changes
- `PubSub.__init__()`: `error_handler` parameter is now keyword-only (previously positional)
- Correlation ID feature introduces new required patterns - invalid correlation IDs will raise `SplurgePubSubValueError`

### [2025.0.0] - 2025-11-04

#### Added
- Added all core functionality for library including PubSub class, Message class, TopicPattern filtering, and exception hierarchy.
- Implemented topic filtering with wildcard support (`*` and `?`) for selective message delivery
- Added decorator API for simplified subscription syntax using `@bus.on("topic")`
- Introduced custom error handling for failed callbacks
- Added context manager support for automatic resource cleanup
- Achieved 95% test coverage across all features with unit and property-based tests
- Comprehensive documentation including API reference, CLI reference, and detailed README
- Established pre-commit hooks for code quality checks using Ruff and mypy
- Added example usage code in `examples/` directory
- Added comprehensive unit and property-based tests for PubSub functionality
  - Implemented unit tests for core PubSub operations including initialization, subscription, publishing, unsubscription, clearing, shutdown, context management, thread safety, and edge cases.
  - Developed property-based tests using Hypothesis to verify subscriber management, message publishing invariants, topic filtering behavior, and message delivery guarantees.
  - Created unit tests for package constants, ensuring proper metadata, public API exports, importable symbols, and overall package integrity.