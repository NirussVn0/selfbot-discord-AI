"""Unit tests for TextStyler message chunking."""
import pytest
from selfbot_discord.utils.formatting import TextStyler


def test_chunk_message_short():
    """Test that short messages are not chunked."""
    msg = "short message"
    result = TextStyler.chunk_message(msg)
    assert len(result) == 1
    assert result[0] == msg


def test_chunk_message_exact_limit():
    """Test message exactly at limit."""
    msg = "a" * 1900
    result = TextStyler.chunk_message(msg)
    assert len(result) == 1


def test_chunk_message_over_limit():
    """Test message over limit gets chunked."""
    msg = "a" * 3000
    result = TextStyler.chunk_message(msg)
    assert len(result) == 2
    assert all(len(chunk) <= 1900 for chunk in result)


def test_chunk_message_with_newlines():
    """Test chunking respects line breaks."""
    lines = ["Line " + str(i) for i in range(100)]
    msg = "\n".join(lines)
    result = TextStyler.chunk_message(msg, max_length=500)
    assert len(result) > 1
    assert all(len(chunk) <= 500 for chunk in result)


def test_chunk_message_empty():
    """Test empty string handling."""
    result = TextStyler.chunk_message("")
    assert len(result) == 1
    assert result[0] == ""


def test_chunk_message_very_long_line():
    """Test single line exceeding limit."""
    msg = "a" * 2500
    result = TextStyler.chunk_message(msg, max_length=1000)
    assert len(result) == 3
    assert all(len(chunk) <= 1000 for chunk in result)
