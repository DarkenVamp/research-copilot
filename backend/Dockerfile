FROM python:3.13-slim

WORKDIR /app

# uv for fast, reproducible installs.
RUN pip install --no-cache-dir uv

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
RUN uv pip install --system --no-cache .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
