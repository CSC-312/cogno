<<<<<<< HEAD
# Use Python 3.12 slim as base image
=======
>>>>>>> main
FROM python:3.12-slim-bookworm

# Install Node.js (required for Prisma) and other utilities
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy Python dependency files first (better caching)
COPY pyproject.toml uv.lock ./
<<<<<<< HEAD
RUN uv sync --locked
=======
RUN uv sync --no-dev --locked
>>>>>>> main

# Copy Node.js dependency files first (better caching)
COPY package*.json ./
RUN npm install

# Copy Prisma schema
COPY prisma/ ./prisma/

# Set a DEFAULT DATABASE_URL for Prisma Client generation during build
# This URL is a DUMMY URL only for generating the client. The real one is used at runtime.
ENV DATABASE_URL="postgresql://dummy:dummy@dummy:5432/dummy"

# Generate client
RUN npx prisma generate

# Create non-root user and set ownership FIRST
RUN useradd -m -d /home/app -s /bin/bash app
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Copy the rest of the app code
COPY --chown=app:app . .

# Set environment variables for container Python and app
ENV PYTHONPATH=/app

# Expose the port for the frontend
EXPOSE 8000

# Run Chainlit app
<<<<<<< HEAD
CMD ["uv", "run", "chainlit", "run", "frontend/main.py", "--host", "0.0.0.0", "--port", "8000"]
=======
CMD ["uv", "run", "chainlit", "run", "frontend/main.py", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> main
