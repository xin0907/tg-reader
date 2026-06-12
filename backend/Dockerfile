FROM ghcr.io/astral-sh/uv:python3.11-bookworm

WORKDIR /app

# Install dependencies first (leverages layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and install the project itself
COPY . .
RUN uv sync --frozen --no-dev

RUN mkdir -p /app/static/images

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
