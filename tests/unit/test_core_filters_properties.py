"""Property-based tests for TopicPattern using Hypothesis.

This module uses Hypothesis to verify TopicPattern invariants and
behavior under various pattern and topic combinations.

Test Classes:
    - TestPatternInvariants: Pattern creation and storage invariants
    - TestPatternMatching: Pattern matching properties
    - TestPatternEdgeCases: Edge case handling in pattern matching

DOMAINS: ["testing", "filters", "properties"]
"""

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from splurge_pub_sub import TopicPattern

DOMAINS = ["testing", "filters", "properties"]


# Custom strategies
@st.composite
def topic_segments(draw: Any) -> str:
    """Strategy for generating valid topic segment."""
    return draw(st.text(alphabet="a-z0-9_", min_size=1, max_size=10))


@st.composite
def valid_topics(draw: Any) -> str:
    """Strategy for generating valid topic strings."""
    segments = draw(st.lists(topic_segments(), min_size=1, max_size=5))
    return ".".join(segments)


@st.composite
def valid_patterns(draw: Any) -> str:
    """Strategy for generating valid pattern strings."""
    max_segments = 5
    num_segments = draw(st.integers(min_value=1, max_value=max_segments))
    segments = []

    for _ in range(num_segments):
        segment = draw(
            st.one_of(
                st.just("*"),
                st.text(alphabet="a-z0-9_", min_size=1, max_size=10),
            )
        )
        segments.append(segment)

    return ".".join(segments)


class TestPatternInvariants:
    """Property-based tests for pattern creation invariants."""

    @given(pattern_str=valid_patterns())
    def test_pattern_creation_always_succeeds(self, pattern_str: str) -> None:
        """Test that TopicPattern creation always succeeds with valid patterns."""
        pattern = TopicPattern(pattern_str)
        assert pattern is not None

    @given(pattern_str=valid_patterns())
    def test_pattern_stores_pattern_unchanged(self, pattern_str: str) -> None:
        """Test that pattern is stored exactly as provided."""
        pattern = TopicPattern(pattern_str)
        assert pattern.pattern == pattern_str

    @given(pattern_str=valid_patterns())
    def test_pattern_is_immutable(self, pattern_str: str) -> None:
        """Test that TopicPattern is immutable (frozen dataclass)."""
        pattern = TopicPattern(pattern_str)

        with pytest.raises((AttributeError, TypeError)):
            pattern.pattern = "new.pattern"


class TestPatternMatching:
    """Property-based tests for pattern matching behavior."""

    @given(topic=valid_topics())
    def test_exact_pattern_matches_itself(self, topic: str) -> None:
        """Test that exact pattern matches the identical topic."""
        pattern = TopicPattern(topic)
        assert pattern.matches(topic)

    @given(topic=valid_topics())
    def test_exact_pattern_only_matches_exact_topic(self, topic: str) -> None:
        """Test that exact pattern doesn't match different topics."""
        pattern = TopicPattern(topic)

        # Create a different topic by modifying the last segment
        segments = topic.split(".")
        segments[-1] = segments[-1] + "_different"
        different_topic = ".".join(segments)

        assert not pattern.matches(different_topic)

    @given(pattern_str=valid_patterns(), topic=valid_topics())
    def test_pattern_matching_is_boolean(self, pattern_str: str, topic: str) -> None:
        """Test that pattern matching always returns boolean."""
        pattern = TopicPattern(pattern_str)
        result = pattern.matches(topic)
        assert isinstance(result, bool)

    @given(pattern_str=valid_patterns())
    def test_single_wildcard_pattern(self, pattern_str: str) -> None:
        """Test that single wildcard matches any single-segment topic."""
        if pattern_str == "*":
            pattern = TopicPattern(pattern_str)
            # Wildcard should match any single segment
            assert pattern.matches("user")
            assert pattern.matches("order")
            assert pattern.matches("a")

    @given(
        segments1=st.lists(st.text(alphabet="a-z0-9", min_size=1), min_size=1, max_size=3),
        segments2=st.lists(st.text(alphabet="a-z0-9", min_size=1), min_size=1, max_size=3),
    )
    def test_segments_length_affects_matching(
        self,
        segments1: list[str],
        segments2: list[str],
    ) -> None:
        """Test that segment count affects pattern matching."""
        topic1 = ".".join(segments1)
        topic2 = ".".join(segments2)
        pattern = TopicPattern(topic1)

        # If segments differ in length, exact pattern won't match
        if len(segments1) != len(segments2):
            # Topic with different segment count should not match exact pattern
            # (unless the pattern uses wildcards, but topic1 doesn't)
            assert not pattern.matches(topic2)


class TestPatternEquality:
    """Property-based tests for pattern equality and comparison."""

    @given(pattern_str=valid_patterns())
    def test_pattern_equals_itself(self, pattern_str: str) -> None:
        """Test that a pattern equals itself."""
        pattern1 = TopicPattern(pattern_str)
        pattern2 = TopicPattern(pattern_str)
        assert pattern1 == pattern2

    @given(
        pattern_str1=valid_patterns(),
        pattern_str2=valid_patterns(),
    )
    def test_different_patterns_not_equal(self, pattern_str1: str, pattern_str2: str) -> None:
        """Test that different patterns are not equal."""
        pattern1 = TopicPattern(pattern_str1)
        pattern2 = TopicPattern(pattern_str2)

        if pattern_str1 != pattern_str2:
            assert pattern1 != pattern2

    @given(pattern_str=valid_patterns())
    def test_pattern_hash_is_consistent(self, pattern_str: str) -> None:
        """Test that pattern hash is consistent."""
        pattern = TopicPattern(pattern_str)
        hash1 = hash(pattern)
        hash2 = hash(pattern)
        assert hash1 == hash2

    @given(pattern_str=valid_patterns())
    def test_equal_patterns_have_same_hash(self, pattern_str: str) -> None:
        """Test that equal patterns have the same hash."""
        pattern1 = TopicPattern(pattern_str)
        pattern2 = TopicPattern(pattern_str)
        assert hash(pattern1) == hash(pattern2)


class TestPatternEdgeCases:
    """Property-based tests for pattern edge cases."""

    @given(pattern_str=valid_patterns())
    def test_pattern_has_valid_string_representation(self, pattern_str: str) -> None:
        """Test that pattern has valid string representation."""
        pattern = TopicPattern(pattern_str)
        str_repr = str(pattern)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    @given(pattern_str=valid_patterns(), topic=valid_topics())
    def test_pattern_matching_result_is_deterministic(
        self,
        pattern_str: str,
        topic: str,
    ) -> None:
        """Test that pattern matching is deterministic."""
        pattern = TopicPattern(pattern_str)
        result1 = pattern.matches(topic)
        result2 = pattern.matches(topic)
        assert result1 == result2

    @given(segments=st.lists(st.text(alphabet="a-z0-9", min_size=1), min_size=1, max_size=10))
    def test_wildcard_in_middle_segment(self, segments: list[str]) -> None:
        """Test wildcards in different segment positions."""
        if len(segments) >= 2:
            # Create pattern with wildcard in middle
            pattern_segments = segments.copy()
            pattern_segments[len(pattern_segments) // 2] = "*"
            pattern_str = ".".join(pattern_segments)

            topic_str = ".".join(segments)

            pattern = TopicPattern(pattern_str)
            # Pattern with wildcard in middle should match the topic
            assert pattern.matches(topic_str)
