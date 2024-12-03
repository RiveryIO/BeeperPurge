import json
import logging
from beeperpurge.logging import JsonFormatter, setup_logging, log_with_context

def test_json_formatter():
    """Test JSON formatter produces valid JSON with expected fields."""
    formatter = JsonFormatter()

    # Create a log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )

    # Format the record
    formatted = formatter.format(record)

    # Parse the JSON
    log_dict = json.loads(formatted)

    # Check required fields
    assert "timestamp" in log_dict
    assert "level" in log_dict
    assert "message" in log_dict
    assert "logger" in log_dict

    # Check values
    assert log_dict["level"] == "INFO"
    assert log_dict["message"] == "Test message"
    assert log_dict["logger"] == "test_logger"

def test_json_formatter_with_error():
    """Test JSON formatter handles errors correctly."""
    formatter = JsonFormatter()

    try:
        raise ValueError("Test error")
    except ValueError:
        import sys
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=sys.exc_info()
        )

    formatted = formatter.format(record)
    log_dict = json.loads(formatted)

    assert "error" in log_dict
    assert "ValueError: Test error" in log_dict["error"]

def test_setup_logging():
    """Test logger setup with correct configuration."""
    logger = setup_logging("test_logger", "DEBUG")

    assert logger.name == "test_logger"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2

    # Check handler levels
    has_info = False
    has_error = False
    for handler in logger.handlers:
        if handler.level == logging.INFO:
            has_info = True
        if handler.level == logging.ERROR:
            has_error = True

    assert has_info, "Should have INFO level handler"
    assert has_error, "Should have ERROR level handler"

    # Check formatters
    for handler in logger.handlers:
        assert isinstance(handler.formatter, JsonFormatter)

def test_log_with_context(mock_logger):
    """Test logging with context fields."""
    logger, records = mock_logger

    extra = {
        "field1": "value1",
        "field2": 123
    }

    log_with_context(logger, "info", "Test message", extra)

    assert len(records) == 1
    record = records[0]

    assert hasattr(record, "extra_fields")
    assert record.extra_fields == extra
    assert record.message == "Test message"
    assert record.levelname == "INFO"

def test_log_levels(mock_logger):
    """Test different log levels."""
    logger, records = mock_logger

    # We only test levels that are at or above INFO since that's our handler configuration
    levels = ["info", "warning", "error", "critical"]

    for level in levels:
        log_with_context(logger, level, f"Test {level}")

    assert len(records) == len(levels), f"Expected {len(levels)} records, got {len(records)}"
    for record, level in zip(records, levels):
        assert record.levelname == level.upper()
