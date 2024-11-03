# BeeperPurge 🧹

[![Python Tests on Release branch (main)](https://github.com/RiveryIO/BeeperPurge/actions/workflows/python-ci-main.yaml/badge.svg?branch=main)](https://github.com/RiveryIO/BeeperPurge/actions/workflows/python-ci-main.yaml)
[![codecov](https://codecov.io/gh/RiveryIO/BeeperPurge/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/RiveryIO/BeeperPurge)

High-throughput parallel file system cleaner designed for efficiently eliminating millions of old files as close to simultaneously as possible.

## Features

- 🚀 Parallel processing with multi-threading
- 🎯 Precision targeting of files by age
- 🔍 Dry-run mode for operation verification
- 📝 Kubernetes-friendly JSON logging
- 🔒 Safe handling of sensitive file systems
- ⚙️ Configurable age thresholds
- 🐳 Production-ready container with security best practices

## Installation and Running

### Running as a Kubernetes Cron Job (Recommended)
To automate regular cleanups using beeper-purge in Kubernetes, you can configure a Kubernetes CronJob that runs at a specified interval. This example mounts an existing PersistentVolumeClaim (PVC) to the cron job container.

Create a CronJob Manifest: Replace /data with your target path in the volume and adjust schedule and other parameters as needed.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: beeper-purge-cron
spec:
  schedule: "0 0 * * *"  # Run daily at midnight
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: beeper-purge
              image: ghcr.io/RiveryIO/beeper-purge:latest
              args: 
                - "/data"
                - "--max-age-hours"
                - "36"
              volumeMounts:
                - name: data-volume
                  mountPath: /data
          restartPolicy: OnFailure
          volumes:
            - name: data-volume
              persistentVolumeClaim:
                claimName: your-existing-pvc-name  # Replace with your PVC name

```

### Using Docker

```bash
docker pull ghcr.io/RiveryIO/beeper-purge:latest

# Always verify targets first with dry run
docker run -v /path/to/clean:/data ghcr.io/RiveryIO/beeper-purge:latest \
    /data --dry-run --max-age-hours 36

# Execute purge operation
docker run -v /path/to/clean:/data ghcr.io/RiveryIO/beeper-purge:latest \
    /data --max-age-hours 36
```

### Using pip

```bash
pip install beeper-purge
```

## Usage

```bash
# Show help
beeperpurge --help

# Reconnaissance (dry run)
beeperpurge /path/to/clean --dry-run --max-age-hours 36

# Execute purge
beeperpurge /path/to/clean --max-age-hours 36 --workers 16

# Show version
beeperpurge --version
```

## Operational Metrics

```bash
$ beeperpurge /data --dry-run
{
    "timestamp": "2024-11-02T10:15:30,123",
    "level": "INFO",
    "message": "Starting purge operation",
    "extra_fields": {
        "root_path": "/data",
        "dry_run": true,
        "max_workers": 16
    }
}
...
{
    "timestamp": "2024-11-02T10:15:35,456",
    "level": "INFO",
    "message": "Operation completed",
    "extra_fields": {
        "files_processed": 1000000,
        "files_targeted": 150000,
        "duration_seconds": 5.33,
        "elimination_rate": 187617
    }
}
```

## Safety Protocols

- 🛡️ Dry-run mode for target verification
- 🔗 No symlink following
- 🚨 Comprehensive error handling
- 👤 Non-root container execution
- ✅ Extensive test coverage

## Performance Specifications

### Scalability
- Efficiently handles millions of files
- Memory usage scales linearly with worker count
- I/O optimized operations

### Recommended Configurations
- Standard systems: 8-16 workers
- High-performance systems: 16-32 workers
- Adjust based on:
  - Available CPU cores
  - I/O capabilities
  - File system response times

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/RiveryIO/BeeperPurge.git
cd beeperpurge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Full test suite
pytest

# Coverage analysis
pytest --cov=beeper_purge

# Specific test execution
pytest tests/test_cleaner.py
```

### Container Build

```bash
docker build -t beeper-purge .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/enhancement`)
3. Commit your changes (`git commit -m 'Add enhancement'`)
4. Push to the branch (`git push origin feature/enhancement`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
