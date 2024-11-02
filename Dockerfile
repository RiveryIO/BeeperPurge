FROM python:3.9-slim

WORKDIR /app

# Install package and dependencies
COPY pyproject.toml setup.py ./
COPY src ./src

RUN pip install --no-cache-dir . && \
    rm -rf ~/.cache/pip/*

# Create non-root user
RUN useradd -r -u 1000 -m purger
USER purger

ENTRYPOINT ["beeperpurge"]
# Default arguments (can be overridden)
CMD ["--help"]