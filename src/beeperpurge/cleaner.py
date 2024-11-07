import os
import time
import concurrent.futures
import queue
import threading
from pathlib import Path
import argparse
from typing import Dict
import logging

from .logging import setup_logging, log_with_context

class HighThroughputDirCleaner:
    def __init__(self, root_path: str, max_age_hours: float, max_workers: int = 8, dry_run: bool = True, chunk_size: int = 1000):
        """Initialize the directory cleaner."""
        self.root_path = Path(root_path)
        self.max_workers = max_workers
        self.dry_run = dry_run
        self.max_age_hours = max_age_hours  # Store the max age
        self.cutoff_time = time.time() - (max_age_hours * 3600)
        self.dirs_queue: queue.Queue = queue.Queue()
        self.chunk_size = chunk_size
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_to_purge': 0,
            'files_purged': 0,
            'dirs_processed': 0,
            'symlinks_skipped': 0,
            'errors': 0
        }
        self.stats_lock = threading.Lock()
        
        # Setup logging
        self.logger = setup_logging()

    def update_stats(self, **kwargs: int) -> None:
        """Thread-safe update of statistics."""
        with self.stats_lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] += value

    def process_directory(self, directory: Path) -> None:
        """Process all files in a directory and queue them for chunked processing."""
        try:
            file_paths = []
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            # Update stats for skipped symlink
                            self.update_stats(symlinks_skipped=1)
                        elif entry.is_file(follow_symlinks=False):
                            # Add regular file to file_paths
                            file_paths.append(Path(entry.path))
                        elif entry.is_dir(follow_symlinks=False):
                            # Queue regular directory for further processing
                            self.dirs_queue.put(Path(entry.path))
                    except OSError as e:
                        log_with_context(self.logger, 'error', "Error processing entry", {
                            'path': str(entry.path),
                            'error': str(e)
                        })
                        self.update_stats(errors=1)

            # Process files in chunks
            for i in range(0, len(file_paths), self.chunk_size):
                chunk = file_paths[i:i+self.chunk_size]
                self.process_file_chunk(chunk)

            self.update_stats(dirs_processed=1)
            self.logger.debug(f"Processed directory: {directory}")

        except OSError as e:
            log_with_context(self.logger, 'error', "Error accessing directory", {
                'directory': str(directory),
                'error': str(e)
            })
            self.update_stats(errors=1)

    def process_file_chunk(self, file_paths: list[Path]) -> None:
        """Process a chunk of files and purge if too old using only file metadata."""
        for file_path in file_paths:
            try:
                stat = file_path.stat()
                self.update_stats(files_processed=1)

                age_hours = (time.time() - stat.st_mtime) / 3600
                if stat.st_mtime < self.cutoff_time:
                    self.update_stats(files_to_purge=1)
                    
                    if not self.dry_run:
                        try:
                            file_path.unlink()
                            self.update_stats(files_purged=1)
                            self.logger.debug(f"File purged", extra={
                                'file_path': str(file_path),
                                'age_hours': age_hours
                            })
                        except OSError as e:
                            self.logger.error("Error purging file", extra={
                                'file_path': str(file_path),
                                'error': str(e)
                            })
                            self.update_stats(errors=1)
                    else:
                        self.logger.debug("File marked for purging (dry run)", extra={
                            'file_path': str(file_path),
                            'age_hours': age_hours
                        })

            except OSError as e:
                self.logger.error("Error processing file", extra={
                    'file_path': str(file_path),
                    'error': str(e)
                })
                self.update_stats(errors=1)

    def clean(self) -> None:
        """Main cleaning function using ThreadPoolExecutor."""
        start_time = time.time()
        mode = "DRY RUN" if self.dry_run else "PURGE"
        log_with_context(self.logger, 'info', f"Starting directory cleanup - {mode} MODE", {
            'root_path': str(self.root_path),
            'max_workers': self.max_workers,
            'dry_run': self.dry_run,
            'chunk_size': self.chunk_size
        })
        
        # Start with root directory
        self.dirs_queue.put(self.root_path)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = set()
            
            while True:
                # Start new tasks if we have capacity
                while len(futures) < self.max_workers and not self.dirs_queue.empty():
                    directory = self.dirs_queue.get()
                    self.logger.debug(f"Queuing directory for processing: {directory}")
                    futures.add(executor.submit(self.process_directory, directory))
                
                # Check if we're done
                if not futures and self.dirs_queue.empty():
                    break
                
                # Remove completed futures
                done = {f for f in futures if f.done()}
                futures -= done
                
                # Handle any exceptions from completed futures
                for future in done:
                    try:
                        future.result()
                    except Exception as e:
                        log_with_context(self.logger, 'error', "Task error", {
                            'error': str(e)
                        })
                        self.update_stats(errors=1)

                time.sleep(0.1)  # Prevent tight loop

        duration = time.time() - start_time
        log_with_context(self.logger, 'info', "Cleanup completed", {
            'duration_seconds': round(duration, 2),
            'files_processed': self.stats['files_processed'],
            'files_to_purge': self.stats['files_to_purge'],
            'files_purged': self.stats['files_purged'],
            'dirs_processed': self.stats['dirs_processed'],
            'symlinks_skipped': self.stats['symlinks_skipped'],
            'errors': self.stats['errors'],
            'processing_rate': round(self.stats['files_processed'] / duration, 2) if duration > 0 else 0
        })

def main() -> None:
    """Command line interface for the cleaner."""
    parser = argparse.ArgumentParser(
        description='High-throughput parallel file system cleaner',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('path', help='Root path to clean')
    parser.add_argument('--max-age-hours', type=float, default=36.0,
                      help='Maximum age of files in hours')
    parser.add_argument('--workers', type=int, default=8,
                      help='Number of worker threads')
    parser.add_argument('--dry-run', action='store_true',
                      help='Perform a dry run without purging files')
    parser.add_argument('--chunk-size', type=int, default=1000,
                      help='Number of files to process in each chunk')
    parser.add_argument('--log-level', type=str, default='info',
                      help='Logging level (debug, info, warning, error, critical)')
    args = parser.parse_args()

    # Set the log level
    setup_logging(args.log_level)

    cleaner = HighThroughputDirCleaner(
        root_path=args.path,
        max_age_hours=args.max_age_hours,
        max_workers=args.workers,
        dry_run=args.dry_run,
        chunk_size=args.chunk_size
    )
    cleaner.clean()

if __name__ == '__main__':
    main()