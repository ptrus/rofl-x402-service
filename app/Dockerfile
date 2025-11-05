FROM python:3.10-slim

WORKDIR /app

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

# Run the application
CMD ["uv", "run", "python", "main.py"]
