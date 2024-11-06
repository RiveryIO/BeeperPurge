import os
import time
import random
import logging
from pathlib import Path
import pytest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def create_large_file_tree(root_path: Path, num_files: int = 10000) -> None:
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

    # Create a read-only file for permission testing
    readonly_file = root_path / "readonly.txt"
    create_sample_file(readonly_file, 48, permissions=0o444)

def print_file_tree(path: Path, indent: str = "") -> None:
    """Recursively prints the directory tree structure with details on each file."""
    try:
        print(f"{indent}{path.name}/")
    except Exception as e:
        logger.error(f"Could not print directory {path.name}: {e}")
    indent += "  "
    
    for item in sorted(path.iterdir()):
        if item.is_dir():
            print_file_tree(item, indent)
        else:
            try:
                # Get stats for the file
                stats = item.lstat() if item.is_symlink() else item.stat()
                age_hours = (time.time() - stats.st_mtime) / 3600
                size = stats.st_size
                mode = oct(stats.st_mode)[-3:]  # file permissions
                symlink = "-> " + os.readlink(item) if item.is_symlink() else ""
                print(f"{indent}{item.name} ({age_hours:.1f} hours old, {size}b, mode:{mode}) {symlink}")
            except Exception as e:
                logger.error(f"Error processing file {item}: {e}")

@pytest.fixture
def sample_file_tree(tmp_path):
    """Fixture to create a large, nested sample file tree for testing."""
    create_large_file_tree(tmp_path)
    return tmp_path

def test_show_structure(sample_file_tree):
    """Test function to display the actual file structure."""
    print("\nActual file structure created:")
    print("-" * 50)
    print_file_tree(sample_file_tree)
    print("-" * 50)
    print("\nFile details:")
    
    for file_path in sorted(sample_file_tree.rglob("*.txt")):
        try:
            # Get file stats
            stats = file_path.lstat() if file_path.is_symlink() else file_path.stat()
            relative_path = file_path.relative_to(sample_file_tree)
            
            print(f"\nFile: {relative_path}")
            print(f"  Absolute path: {file_path}")
            print(f"  Age (hours): {(time.time() - stats.st_mtime) / 3600:.1f}")
            print(f"  Size: {stats.st_size} bytes")
            print(f"  Mode: {oct(stats.st_mode)}")
            print(f"  Is symlink: {file_path.is_symlink()}")
            
            if file_path.is_symlink():
                target_path = file_path.resolve()
                print(f"  Symlink target: {target_path}")
                try:
                    target_stats = target_path.stat()
                    print(f"  Target age (hours): {(time.time() - target_stats.st_mtime) / 3600:.1f}")
                except Exception as e:
                    logger.error(f"Error retrieving target stats for {target_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Always pass - this test is just for showing the structure
    assert True

def test_symlink(sample_file_tree):
    """Test to ensure that symlinks are processed and resolve correctly."""
    symlink = sample_file_tree / "link.txt"
    assert symlink.is_symlink(), "Expected a symlink, but found a regular file."
    target = symlink.resolve()
    assert target.exists(), "Symlink target does not exist."
    logger.info(f"Symlink {symlink} points to {target}.")

def test_read_only_file(sample_file_tree):
    """Test to ensure that read-only files are detected and handled properly."""
    readonly_file = sample_file_tree / "readonly.txt"
    assert readonly_file.exists(), "Read-only file does not exist."
    assert not os.access(readonly_file, os.W_OK), "Read-only file is writable, which is unexpected."
    logger.info(f"Read-only file {readonly_file} has correct permissions.")

def test_deeply_nested_structure(sample_file_tree):
    """Test to ensure deeply nested files are processed correctly."""
    deep_file = sample_file_tree / "extra" / "nested" / "deep_nested" / "deep_file.txt"
    assert deep_file.exists(), "Deeply nested file does not exist."
    logger.info(f"Deeply nested file {deep_file} found successfully.")
