"""
Unit tests for string utilities.

This module contains comprehensive tests for the string_utils module,
following TDD principles with 100% code coverage.
"""

import pytest
from libs.string_utils import reverse_string


class TestReverseString:
    """Test cases for reverse_string function."""

    def test_reverse_string_basic(self):
        """Test basic string reversal."""
        assert reverse_string("hello") == "olleh"
        assert reverse_string("world") == "dlrow"
        assert reverse_string("abc") == "cba"

    def test_reverse_string_single_character(self):
        """Test single character string."""
        assert reverse_string("a") == "a"
        assert reverse_string("1") == "1"

    def test_reverse_string_empty(self):
        """Test empty string returns empty string."""
        assert reverse_string("") == ""

    def test_reverse_string_palindrome(self):
        """Test palindromic strings."""
        assert reverse_string("racecar") == "racecar"
        assert reverse_string("noon") == "noon"

    def test_reverse_string_with_spaces(self):
        """Test strings with spaces."""
        assert reverse_string("hello world") == "dlrow olleh"
        assert reverse_string("a b c") == "c b a"

    def test_reverse_string_with_special_characters(self):
        """Test strings with special characters."""
        assert reverse_string("hello!") == "!olleh"
        assert reverse_string("123@456") == "654@321"
        assert reverse_string("a-b-c") == "c-b-a"

    def test_reverse_string_unicode(self):
        """Test unicode strings."""
        assert reverse_string("こんにちは") == "はちにんこ"
        assert reverse_string("café") == "éfac"

    def test_reverse_string_none_input(self):
        """Test None input raises ValueError."""
        with pytest.raises(ValueError, match="Input cannot be None"):
            reverse_string(None)

    def test_reverse_string_non_string_types(self):
        """Test non-string types raise TypeError."""
        with pytest.raises(TypeError, match="Input must be a string"):
            reverse_string(123)
        
        with pytest.raises(TypeError, match="Input must be a string"):
            reverse_string([1, 2, 3])
        
        with pytest.raises(TypeError, match="Input must be a string"):
            reverse_string({"key": "value"})
        
        with pytest.raises(TypeError, match="Input must be a string"):
            reverse_string(True)

    def test_reverse_string_whitespace_only(self):
        """Test strings with only whitespace."""
        assert reverse_string("   ") == "   "
        assert reverse_string("\t") == "\t"
        assert reverse_string("\n") == "\n"

    def test_reverse_string_mixed_whitespace(self):
        """Test strings with mixed whitespace."""
        assert reverse_string("a\tb\nc") == "c\nb\ta"
        assert reverse_string(" hello ") == " olleh "