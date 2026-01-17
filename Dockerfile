# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set the working directory in the container
WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy only the necessary files for dependency installation first (caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we use the exact versions in uv.lock
# --python system forces usage of the container's python (3.10)
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python

# Copy the rest of the application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# CRITICAL: Copy the local data directory (ChromaDB + NetworkX graph)
# This "bakes" the data into the image for read-only usage
COPY data/ ./data/

# Install the project itself (if needed, though we run via module)
RUN uv sync --frozen --no-dev --python /usr/local/bin/python

# Expose the port used by Cloud Run
EXPOSE 8080

# Run the application
# We use 'uv run' to ensure we use the virtual environment created by uv
CMD ["uv", "run", "uvicorn", "src.serving.api:app", "--host", "0.0.0.0", "--port", "8080"]
