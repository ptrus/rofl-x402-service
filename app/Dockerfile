FROM python:3.10-slim

WORKDIR /app

# Install git (needed for git dependencies) and clean up
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (with ollama group by default)
RUN uv sync --frozen --no-dev --group ollama

# Copy application code
COPY . .

# Expose port
EXPOSE 4021

# Run the application using uv run (which uses the venv)
CMD ["uv", "run", "python", "main.py"]
