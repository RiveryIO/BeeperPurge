import json
import logging
import argparse  # For parsing command-line arguments
from typing import Any, Dict, Optional

class JsonFormatter(logging.Formatter):
    """JSON log formatter for Kubernetes compatibility"""
    def format(self, record: logging.LogRecord) -> str:
        """Format LogRecord into JSON string."""
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # Add error information if present
        if record.exc_info:
            log_obj["error"] = self.formatException(record.exc_info)
            
        # Add extra fields if any
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)
            
        return json.dumps(log_obj)

def setup_logging(logger_name: str = "beeperpurge", level: str = "INFO") -> logging.Logger:
    """Configure JSON logging for Kubernetes compatibility.
    
    Args:
        logger_name: Name of the logger
        level: Logging level (INFO, DEBUG, etc.)
        
    Returns:
        Configured logger instance
    """
    # Remove any existing handlers from root logger
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))  # Set the level dynamically based on the argument
    
    # Create handlers for stdout and stderr
    stdout_handler = logging.StreamHandler()
    stderr_handler = logging.StreamHandler()
    
    # Set log levels for handlers
    stdout_handler.setLevel(logging.DEBUG if level.upper() == "DEBUG" else logging.INFO)
    stderr_handler.setLevel(logging.ERROR)
    
    # Create and set JSON formatter
    json_formatter = JsonFormatter()
    stdout_handler.setFormatter(json_formatter)
    stderr_handler.setFormatter(json_formatter)
    
    # Add handlers to logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    
    return logger

def log_with_context(logger: logging.Logger, 
                     level: str, 
                     message: str, 
                     extra: Optional[Dict[str, Any]] = None) -> None:
    """Log message with additional context fields.
    
    Args:
        logger: Logger instance to use
        level: Log level (info, error, debug, etc.)
        message: Log message
        extra: Additional context fields to include
    """
    if extra is None:
        extra = {}
        
    # Create record with context
    context = {
        "extra_fields": extra
    }
    
    # Log with the appropriate level
    log_method = getattr(logger, level.lower())
    log_method(message, extra=context)

# Example usage with command-line argument
if __name__ == "__main__":
    # Parse the command-line arguments for log level
    parser = argparse.ArgumentParser(description="Run with specified log level")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set the logging level")
    args = parser.parse_args()

    # Setup the logger with the specified log level
    logger = setup_logging(level=args.log_level)

    # Example log usage
    log_with_context(logger, "info", "This is an informational message.")
    log_with_context(logger, "debug", "This is a debug message for detailed tracing.")
    log_with_context(logger, "error", "This is an error message.")
