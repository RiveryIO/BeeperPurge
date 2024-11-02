import os
import time
from pathlib import Path
import pytest
from beeperpurge.cleaner import HighThroughputDirCleaner

def test_dry_run_preserves_files(sample_file_tree):
    """Test that dry run mode doesn't delete any files."""
    print("\nDebug file listing:")
    total_files = 0
    old_files = 0
    current_time = time.time()
    for file_path in sample_file_tree.rglob("*.txt"):
        total_files += 1
        mtime = file_path.stat().st_mtime
        age_hours = (current_time - mtime) / 3600
        is_old = age_hours > 36
        old_files += 1 if is_old else 0
        print(f"File: {file_path.name}")
        print(f"  Age: {age_hours:.1f} hours")
        print(f"  Is Old: {is_old}")

    print(f"\nSummary:")
    print(f"Total files found: {total_files}")
    print(f"Old files found: {old_files}")
    cleaner = HighThroughputDirCleaner(
        root_path=str(sample_file_tree),
        max_age_hours=36,
        dry_run=True
    )
    
    # Count files before
    initial_files = list(sample_file_tree.rglob("*.txt"))
    initial_count = len(initial_files)
    print(f"\nInitial file count: {initial_count}")
    print(f"Cutoff time: {cleaner.cutoff_time}")
    print(f"Current time: {time.time()}")
    
    # Run cleaner
    cleaner.clean()
    
    # Print stats after cleaning
    print("\nCleaner stats:", cleaner.stats)
    
    # Count files after
    final_files = list(sample_file_tree.rglob("*.txt"))
    final_count = len(final_files)
    
    assert initial_count == final_count, "Dry run should not delete any files"
    assert cleaner.stats['files_to_purge'] > 0, "Should identify files to purge"