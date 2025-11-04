# Changelog

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