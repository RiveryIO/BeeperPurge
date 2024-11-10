import json
import logging
import pytest
from beeperpurge.logging import JsonFormatter, setup_logging, log_with_context

@pytest.fixture
def mock_logger():
    """Fixture to create a logger with a mock handler for capturing logs."""
    logger = setup_logging("test_logger", "DEBUG")  # Default to DEBUG for capturing all logs
    log_records = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    list_handler = ListHandler()
    list_handler.setFormatter(JsonFormatter())
    logger.addHandler(list_handler)
    
    return logger, log_records

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
    has_debug = False
    has_error = False
    for handler in logger.handlers:
        if handler.level == logging.DEBUG:
            has_debug = True
        if handler.level == logging.ERROR:
            has_error = True
    
    assert has_debug, "Should have DEBUG level handler for stdout"
    assert has_error, "Should have ERROR level handler for stderr"
    
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
    assert record.getMessage() == "Test message"
    assert record.levelname == "INFO"

def test_log_levels(mock_logger):
    """Test different log levels."""
    logger, records = mock_logger
    
    levels = ["debug", "info", "warning", "error", "critical"]
    
    for level in levels:
        log_with_context(logger, level, f"Test {level}")
    
    # All log levels should be captured in DEBUG mode
    assert len(records) == len(levels), f"Expected {len(levels)} records, got {len(records)}"
    for record, level in zip(records, levels):
        assert record.levelname == level.upper()

def test_log_level_info_only():
    """Test that only INFO level and above are logged when log level is set to INFO."""
    logger = setup_logging("test_logger", "INFO")
    log_records = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    list_handler = ListHandler()
    list_handler.setFormatter(JsonFormatter())
    logger.addHandler(list_handler)
    
    # Log messages of all levels
    log_with_context(logger, "debug", "This debug message should not appear.")
    log_with_context(logger, "info", "This info message should appear.")
    log_with_context(logger, "warning", "This warning message should appear.")
    log_with_context(logger, "error", "This error message should appear.")
    
    # Only INFO and higher levels should be recorded
    assert len(log_records) == 3, f"Expected 3 records, got {len(log_records)}"
    assert log_records[0].levelname == "INFO"
    assert log_records[1].levelname == "WARNING"
    assert log_records[2].levelname == "ERROR"
