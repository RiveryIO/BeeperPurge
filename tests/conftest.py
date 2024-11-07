import os
import random
import time
from pathlib import Path
import pytest
import logging


def create_sample_file(path: Path, hours_old: int, is_symlink=False, target=None, permissions=0o644) -> None:
    """Creates a file with specified attributes and modification time."""
    path.touch()
    mod_time = time.time() - (hours_old * 3600)
    os.utime(path, (mod_time, mod_time))
    
    if is_symlink and target:
        path.unlink()  # Remove the regular file to create a symlink
        path.symlink_to(target)
    else:
        path.chmod(permissions)

def create_large_file_tree(root_path: Path, num_files: int = 50000) -> None:
    """Create a nested directory structure with files of different ages, types, and permissions."""
    root_path.mkdir(parents=True, exist_ok=True)
    
    # Define the main structure
    num_main_dirs = 5
    num_sub_dirs_per_main = 3
    files_per_sub_dir = num_files // (num_main_dirs * num_sub_dirs_per_main)
    
    for i in range(num_main_dirs):
        main_dir = root_path / f"main_dir_{i}"
        main_dir.mkdir(exist_ok=True)
        
        for j in range(num_sub_dirs_per_main):
            sub_dir = main_dir / f"sub_dir_{j}"
            sub_dir.mkdir(exist_ok=True)
            
            for k in range(files_per_sub_dir):
                file_path = sub_dir / f"file_{k}.txt"
                hours_old = random.choice([0, 10, 30, 50])
                create_sample_file(file_path, hours_old)

    # Add a deeply nested directory structure for complexity
    extra_nested = root_path / "extra" / "nested" / "deep_nested"
    extra_nested.mkdir(parents=True, exist_ok=True)
    deep_file = extra_nested / "deep_file.txt"
    create_sample_file(deep_file, 20)

    # Create a symlink to test symlink handling
    symlink_target = root_path / "target.txt"
    create_sample_file(symlink_target, 0)  # Target file for symlink
    symlink = root_path / "link.txt"
    create_sample_file(symlink, 0, is_symlink=True, target=symlink_target)
    # Create a symlink somewhere deep in the tree
    symlinkdeep = extra_nested / "link.txt"
    create_sample_file(symlinkdeep, 0, is_symlink=True, target=deep_file)


    # Create a read-only file for permission testing
    readonly_file = root_path / "readonly.txt"
    create_sample_file(readonly_file, 48, permissions=0o444)

@pytest.fixture
def sample_file_tree(tmp_path):
    """Fixture to create a large, nested sample file tree for testing."""
    create_large_file_tree(tmp_path)
    return tmp_path

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