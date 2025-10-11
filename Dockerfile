FROM python:3.13-slim-bookworm

ENV BUN_INSTALL="/usr/local"
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && curl -fsSL https://bun.com/install | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-group dev --locked

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production

COPY prisma/ ./prisma/

# Set a DEFAULT DATABASE_URL for Prisma Client generation during build
# This URL is a DUMMY URL only for generating the client. The real one is used at runtime.
ENV DATABASE_URL="postgresql://dummy:dummy@dummy:5432/dummy"

# Generate client
RUN bunx prisma generate

# Create non-root user and set ownership FIRST
RUN useradd -m -d /home/app -s /bin/bash app
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Copy the rest of the app code
COPY --chown=app:app . .

ENV PYTHONPATH=/app

EXPOSE 8000

# Run Chainlit app
CMD ["uv", "run", "chainlit", "run", "frontend/main.py", "-h", "--host", "0.0.0.0", "--port", "8000"]
