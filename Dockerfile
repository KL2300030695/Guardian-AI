# ==============================================================================
# Guardian AI — Production Multi-Stage Dockerfile
# ==============================================================================

# ── STAGE 1: Build React Frontend ──────────────────────────────────────────────
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

COPY GuardianAI/frontend/package*.json ./
RUN npm ci

COPY GuardianAI/frontend ./
RUN npm run build

# ── STAGE 2: Python Computer Vision & Server Environment ───────────────────────
FROM python:3.10-slim AS runner

# Prevent interactive prompts & python buffering
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install C++ compiler tools & OpenCV / dlib system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement definitions & install Python packages
COPY GuardianAI/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY GuardianAI /app/GuardianAI

# Copy built frontend from Stage 1 into backend static directory
COPY --from=frontend-builder /app/frontend/dist /app/GuardianAI/frontend/dist

# Create storage directories
RUN mkdir -p /app/GuardianAI/database \
             /app/GuardianAI/recordings \
             /app/GuardianAI/screenshots \
             /app/GuardianAI/faces

# Expose FastAPI HTTP server port
EXPOSE 8000

# Set working directory to GuardianAI root
WORKDIR /app/GuardianAI

# Launch production server
CMD ["python", "main.py"]
