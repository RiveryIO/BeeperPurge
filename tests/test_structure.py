import os
import time
from pathlib import Path

def print_file_tree(path: Path, indent: str = "") -> None:
    """Print the file tree with file ages."""
    print(f"{indent}{path.name}/")
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
                print(f"{indent}{item.name} (ERROR: {str(e)})")

def test_show_structure(sample_file_tree):
    """Show the actual file structure created by the fixture."""
    print("\nActual file structure created:")
    print("-" * 50)
    print_file_tree(sample_file_tree)
    print("-" * 50)
    print("\nFile details:")

    # Show all files with their full paths and stats
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
                    print(f"  Target stats error: {str(e)}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    # Always pass - this test is just for showing the structure
    assert True
