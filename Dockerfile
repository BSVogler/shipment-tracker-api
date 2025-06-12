FROM python:3.13-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

WORKDIR /app

#dependencies
COPY pyproject.toml uv.lock ./
RUN uv pip compile --generate-hashes pyproject.toml -o requirements.txt && \
    uv pip install --system --no-deps --require-hashes -r requirements.txt

# Copy application files
COPY src/ src/
COPY data/ data/
COPY run.sh run.sh

# Make run script executable
RUN chmod +x run.sh

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["./run.sh"]