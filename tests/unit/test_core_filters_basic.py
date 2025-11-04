"""Tests for topic filtering and pattern matching.

This module provides comprehensive tests for the TopicPattern class
and topic filtering functionality.

Test Classes:
    - TestTopicPatternCreation: Pattern validation and creation
    - TestTopicPatternMatching: Pattern matching logic
    - TestTopicPatternExactMatch: Exact match (no wildcards)
    - TestTopicPatternWildcards: Wildcard pattern matching
    - TestTopicPatternEdgeCases: Edge cases and special patterns
    - TestTopicPatternPerformance: Pattern matching performance

DOMAINS: ["testing", "filters"]
"""

import pytest

from splurge_pub_sub import TopicPattern
from splurge_pub_sub.exceptions import SplurgePubSubPatternError

DOMAINS = ["testing", "filters"]


class TestTopicPatternCreation:
    """Tests for TopicPattern creation and validation."""

    def test_create_exact_pattern(self) -> None:
        """Test creating an exact match pattern."""
        pattern = TopicPattern("user.created")
        assert pattern.pattern == "user.created"
        assert pattern.is_exact is True

    def test_create_wildcard_star_pattern(self) -> None:
        """Test creating pattern with * wildcard."""
        pattern = TopicPattern("user.*")
        assert pattern.pattern == "user.*"
        assert pattern.is_exact is False

    def test_create_wildcard_question_pattern(self) -> None:
        """Test creating pattern with ? wildcard."""
        pattern = TopicPattern("order.?.paid")
        assert pattern.pattern == "order.?.paid"
        assert pattern.is_exact is False

    def test_create_pattern_multiple_wildcards(self) -> None:
        """Test creating pattern with multiple wildcards."""
        pattern = TopicPattern("*.*.created")
        assert pattern.pattern == "*.*.created"
        assert pattern.is_exact is False

    def test_empty_pattern_raises_error(self) -> None:
        """Test that empty pattern raises error."""
        with pytest.raises(SplurgePubSubPatternError, match="cannot be empty"):
            TopicPattern("")

    def test_pattern_leading_dot_raises_error(self) -> None:
        """Test that leading dot raises error."""
        with pytest.raises(SplurgePubSubPatternError, match="cannot start or end"):
            TopicPattern(".user.created")

    def test_pattern_trailing_dot_raises_error(self) -> None:
        """Test that trailing dot raises error."""
        with pytest.raises(SplurgePubSubPatternError, match="cannot start or end"):
            TopicPattern("user.created.")

    def test_pattern_consecutive_dots_raises_error(self) -> None:
        """Test that consecutive dots raise error."""
        with pytest.raises(SplurgePubSubPatternError, match="consecutive dots"):
            TopicPattern("user..created")

    def test_pattern_invalid_character_raises_error(self) -> None:
        """Test that invalid characters raise error."""
        with pytest.raises(SplurgePubSubPatternError, match="invalid character"):
            TopicPattern("user@created")

    def test_pattern_repr(self) -> None:
        """Test pattern string representation."""
        exact_pattern = TopicPattern("user.created")
        assert "exact" in repr(exact_pattern)

        wildcard_pattern = TopicPattern("user.*")
        assert "wildcard" in repr(wildcard_pattern)


class TestTopicPatternMatching:
    """Tests for topic pattern matching."""

    def test_exact_match_success(self) -> None:
        """Test exact match that succeeds."""
        pattern = TopicPattern("user.created")
        assert pattern.matches("user.created") is True

    def test_exact_match_failure(self) -> None:
        """Test exact match that fails."""
        pattern = TopicPattern("user.created")
        assert pattern.matches("user.updated") is False

    def test_exact_match_partial_fails(self) -> None:
        """Test that partial matches fail for exact patterns."""
        pattern = TopicPattern("user")
        assert pattern.matches("user.created") is False
        assert pattern.matches("user") is True

    def test_star_wildcard_single_segment(self) -> None:
        """Test * wildcard matches any single segment."""
        pattern = TopicPattern("user.*")
        assert pattern.matches("user.created") is True
        assert pattern.matches("user.updated") is True
        assert pattern.matches("user.deleted") is True

    def test_star_wildcard_no_cross_segment(self) -> None:
        """Test that * doesn't cross segment boundaries (no dots)."""
        pattern = TopicPattern("user.*")
        assert pattern.matches("user.created.v1") is False

    def test_star_wildcard_multiple_segments(self) -> None:
        """Test * wildcard in multiple positions."""
        pattern = TopicPattern("*.created")
        assert pattern.matches("user.created") is True
        assert pattern.matches("order.created") is True
        assert pattern.matches("product.created") is True
        assert pattern.matches("user.updated") is False

    def test_question_wildcard_single_char(self) -> None:
        """Test ? wildcard matches single character."""
        pattern = TopicPattern("order.?.paid")
        assert pattern.matches("order.1.paid") is True
        assert pattern.matches("order.a.paid") is True
        assert pattern.matches("order.x.paid") is True

    def test_question_wildcard_multi_char_fails(self) -> None:
        """Test ? wildcard fails with multiple characters."""
        pattern = TopicPattern("order.?.paid")
        assert pattern.matches("order.12.paid") is False
        assert pattern.matches("order.abc.paid") is False

    def test_question_wildcard_no_char_fails(self) -> None:
        """Test ? wildcard fails with empty segment."""
        pattern = TopicPattern("order.?.paid")
        assert pattern.matches("order..paid") is False

    def test_complex_pattern_mixed_wildcards(self) -> None:
        """Test complex patterns with mixed wildcards."""
        pattern = TopicPattern("*.order.?.status.*")
        assert pattern.matches("user.order.1.status.pending") is True
        assert pattern.matches("api.order.2.status.confirmed.email") is False  # Too many segments
        assert pattern.matches("system.order.x.status.complete") is True


class TestTopicPatternExactMatch:
    """Tests for exact match patterns (no wildcards)."""

    def test_exact_is_exact_property(self) -> None:
        """Test is_exact property for exact patterns."""
        assert TopicPattern("user.created").is_exact is True
        assert TopicPattern("order.paid").is_exact is True
        assert TopicPattern("a.b.c.d.e").is_exact is True

    def test_exact_with_alphanumeric(self) -> None:
        """Test exact patterns with alphanumeric characters."""
        pattern = TopicPattern("user.account.created.v2")
        assert pattern.matches("user.account.created.v2") is True
        assert pattern.matches("user.account.created.v3") is False

    def test_exact_with_hyphens_underscores(self) -> None:
        """Test exact patterns with allowed special characters."""
        pattern = TopicPattern("user-account.created_v1")
        assert pattern.matches("user-account.created_v1") is True
        assert pattern.matches("user_account.created-v1") is False


class TestTopicPatternWildcards:
    """Tests for wildcard pattern matching."""

    def test_all_star_pattern(self) -> None:
        """Test pattern that is all wildcards."""
        pattern = TopicPattern("*")
        assert pattern.matches("user") is True
        assert pattern.matches("order") is True
        assert pattern.matches("anything") is True
        assert pattern.matches("user.created") is False  # Contains dot

    def test_double_star_pattern(self) -> None:
        """Test pattern with two consecutive *."""
        pattern = TopicPattern("*.*")
        assert pattern.matches("user.created") is True
        assert pattern.matches("order.paid") is True
        assert pattern.matches("user.created.v1") is False
        assert pattern.matches("user") is False

    def test_triple_star_pattern(self) -> None:
        """Test pattern with three segments."""
        pattern = TopicPattern("*.*.*")
        assert pattern.matches("user.account.created") is True
        assert pattern.matches("order.payment.confirmed") is True
        assert pattern.matches("a.b") is False
        assert pattern.matches("a.b.c.d") is False

    def test_star_at_beginning(self) -> None:
        """Test * at beginning of pattern."""
        pattern = TopicPattern("*.created")
        assert pattern.matches("user.created") is True
        assert pattern.matches("order.created") is True
        assert pattern.matches("system.created") is True

    def test_star_at_end(self) -> None:
        """Test * at end of pattern."""
        pattern = TopicPattern("user.*")
        assert pattern.matches("user.created") is True
        assert pattern.matches("user.updated") is True
        assert pattern.matches("user.deleted") is True

    def test_star_in_middle(self) -> None:
        """Test * in middle of pattern."""
        pattern = TopicPattern("user.*.email")
        assert pattern.matches("user.account.email") is True
        assert pattern.matches("user.profile.email") is True
        assert pattern.matches("user.created.email") is True

    def test_multiple_question_marks(self) -> None:
        """Test pattern with multiple ? wildcards."""
        pattern = TopicPattern("order.??")
        assert pattern.matches("order.id") is True
        assert pattern.matches("order.ab") is True
        assert pattern.matches("order.123") is False  # Too long

    def test_mixed_star_and_question(self) -> None:
        """Test pattern mixing * and ? wildcards."""
        pattern = TopicPattern("user.*.email.?")
        assert pattern.matches("user.account.email.v") is True
        assert pattern.matches("user.profile.email.1") is True
        assert pattern.matches("user.account.email.v1") is False  # Too long


class TestTopicPatternEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_topic_no_match(self) -> None:
        """Test that empty topic never matches."""
        pattern = TopicPattern("*")
        assert pattern.matches("") is False

    def test_single_char_topic(self) -> None:
        """Test single character topics."""
        pattern = TopicPattern("a")
        assert pattern.matches("a") is True
        assert pattern.matches("b") is False
        assert pattern.matches("ab") is False

    def test_numeric_topic(self) -> None:
        """Test numeric topics."""
        pattern = TopicPattern("123.456")
        assert pattern.matches("123.456") is True
        assert pattern.matches("123.457") is False

    def test_alphanumeric_with_dash(self) -> None:
        """Test topics with dashes."""
        pattern = TopicPattern("user-account.created-event")
        assert pattern.matches("user-account.created-event") is True
        assert pattern.matches("user_account.created-event") is False

    def test_case_sensitive_matching(self) -> None:
        """Test that matching is case-sensitive."""
        pattern = TopicPattern("User.Created")
        assert pattern.matches("User.Created") is True
        assert pattern.matches("user.created") is False
        assert pattern.matches("USER.CREATED") is False

    def test_very_long_topic(self) -> None:
        """Test very long topic names."""
        long_topic = ".".join(["segment"] * 50)
        pattern = TopicPattern(long_topic)
        assert pattern.matches(long_topic) is True
        assert pattern.matches(".".join(["segment"] * 49)) is False

    def test_special_allowed_characters(self) -> None:
        """Test allowed special characters in patterns."""
        pattern = TopicPattern("order-123.payment_v2-beta")
        assert pattern.matches("order-123.payment_v2-beta") is True


class TestTopicPatternPerformance:
    """Tests for pattern matching performance characteristics."""

    def test_exact_match_performance(self) -> None:
        """Test that exact matches are efficient (don't use regex overhead if possible)."""
        # This is more of a conceptual test - in real scenarios would benchmark
        pattern = TopicPattern("user.created")
        for _ in range(1000):
            pattern.matches("user.created")
            pattern.matches("user.updated")

    def test_wildcard_pattern_performance(self) -> None:
        """Test that wildcard patterns compile efficiently."""
        patterns = [
            TopicPattern("user.*"),
            TopicPattern("*.created"),
            TopicPattern("order.?.paid"),
            TopicPattern("*.*.*.event"),
        ]

        topics = [
            "user.created",
            "user.updated",
            "order.1.paid",
            "system.user.profile.event",
        ]

        for pattern in patterns:
            for topic in topics:
                pattern.matches(topic)

    def test_pattern_reuse_efficiency(self) -> None:
        """Test that pattern objects can be reused efficiently."""
        pattern = TopicPattern("user.*")

        # Simulate reusing same pattern for many matches
        for i in range(100):
            pattern.matches(f"user.event_{i}")


class TestTopicPatternIntegration:
    """Integration tests for topic pattern matching."""

    @pytest.mark.parametrize(
        "pattern_str,topic,should_match",
        [
            # Basic exact matches
            ("user.created", "user.created", True),
            ("user.created", "user.updated", False),
            # Star wildcards
            ("user.*", "user.created", True),
            ("user.*", "user.updated", True),
            ("user.*", "order.created", False),
            ("*.created", "user.created", True),
            ("*.created", "order.created", True),
            ("*.*", "user.created", True),
            ("*.*", "user", False),
            # Question mark wildcards
            ("order.?.paid", "order.1.paid", True),
            ("order.?.paid", "order.a.paid", True),
            ("order.?.paid", "order.12.paid", False),
            # Complex patterns
            ("*.user.*", "api.user.created", True),
            ("*.user.*", "system.user.profile", True),
            ("*.user.*", "user.created", False),
        ],
    )
    def test_pattern_matching_parametrized(
        self,
        pattern_str: str,
        topic: str,
        should_match: bool,
    ) -> None:
        """Parametrized test for various pattern matching scenarios."""
        pattern = TopicPattern(pattern_str)
        assert pattern.matches(topic) is should_match
