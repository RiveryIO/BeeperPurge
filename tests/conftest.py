import os
import time
from pathlib import Path
import pytest
import logging

@pytest.fixture
def sample_file_tree(tmp_path):
    """Create a sample file tree for testing.
    
    Creates:
    - Files of different ages
    - Nested directory structure
    - Symlinks
    - Files with different permissions
    """
    # Create base test directories
    root = tmp_path / "test_data"
    root.mkdir()
    nested = root / "nested"
    nested.mkdir()
    deep_nested = nested / "deep"
    deep_nested.mkdir()
    
    # Current time for age calculations
    current_time = time.time()
    
    # Create files of different ages
    files = {
        # Regular files
        root / "new.txt": 1,           # 1 hour old
        root / "old.txt": 48,          # 48 hours old
        root / "borderline.txt": 35,   # Just under 36 hours
        
        # Nested files
        nested / "nested_old.txt": 72,
        nested / "nested_new.txt": 12,
        
        # Deep nested files
        deep_nested / "deep_old.txt": 96,
        deep_nested / "deep_new.txt": 2,
    }
    
    # Create and timestamp the files
    for file_path, hours_old in files.items():
        file_path.touch()
        old_time = current_time - (hours_old * 3600)
        os.utime(file_path, (old_time, old_time))
    
    # Create a symlink
    symlink_target = root / "target.txt"
    symlink_target.touch()
    symlink = root / "link.txt"
    symlink.symlink_to(symlink_target)
    
    # Create a read-only file
    readonly = root / "readonly.txt"
    readonly.touch()
    old_time = current_time - (48 * 3600)
    os.utime(readonly, (old_time, old_time))
    readonly.chmod(0o444)
    
    return root

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    
    # Use a list to capture log records
    log_records = []
    
    class ListHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)
    
    handler = ListHandler()
    logger.addHandler(handler)
    
    return logger, log_records