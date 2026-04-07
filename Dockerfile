FROM python:3.11-slim

WORKDIR /app

# Install build tools needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY requirements.txt pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt uvicorn[standard]

# Copy source code
COPY . .

# Install the package (no-deps since deps are already installed)
RUN pip install --no-cache-dir -e . --no-deps

# Railway injects PORT automatically; default fallback for local testing
ENV PORT=8000

EXPOSE 8000

# python -m api_tester_mcp calls __main__.py -> server.main()
# main() auto-detects PORT env var and starts streamable-http transport
CMD ["python", "-m", "api_tester_mcp"]
