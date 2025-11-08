"""Tests for logging configuration."""

import json
import logging
import sys

from image_api.config.logging_config import JSONFormatter, setup_logging


def test_json_formatter() -> None:
    """Test JSON formatter creates valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    formatted = formatter.format(record)
    
    # Should be valid JSON
    data = json.loads(formatted)
    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["logger"] == "test"
    assert "timestamp" in data
    assert "module" in data
    assert "function" in data
    assert "line" in data


def test_json_formatter_with_exception() -> None:
    """Test JSON formatter with exception info."""
    formatter = JSONFormatter()
    
    try:
        raise ValueError("Test error")
    except ValueError:
        exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test error",
            args=(),
            exc_info=exc_info,
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]


def test_setup_logging() -> None:
    """Test logging setup doesn't raise errors."""
    # This should not raise any exceptions
    setup_logging()
    
    # Verify root logger is configured
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0

