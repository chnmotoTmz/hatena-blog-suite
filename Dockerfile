# ================================================
# Hatena Blog Suite - Multi-stage Docker Build
# 統合はてなブログ管理・自動化スイート
# ================================================

# Stage 1: Python Base
FROM python:3.11-slim as python-base

LABEL maintainer="Hatena Blog Suite Team"
LABEL description="Comprehensive Hatena Blog management and automation suite"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Node.js for Frontend
FROM node:18-alpine as node-base

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
RUN npm ci --production && npm cache clean --force

# Build frontend
COPY frontend/ ./
RUN npm run build

# Stage 3: Final Runtime
FROM python:3.11-slim

# Install Node.js and system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python environment
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Copy built frontend
COPY --from=node-base /app/frontend/build ./frontend/build

# Copy application files
COPY automation/ ./automation/
COPY image/ ./image/
COPY optimization/ ./optimization/
COPY core/ ./core/
COPY mcp/ ./mcp/
COPY backend/ ./backend/
COPY config/ ./config/
COPY main.py ./
COPY requirements.txt ./

# Create necessary directories
RUN mkdir -p \
    data \
    logs \
    output \
    generated_images \
    chroma_db \
    temp \
    backup

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV ENVIRONMENT=docker

# Environment defaults
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV MCP_SERVER_PORT=8083
ENV FLASK_PORT=8084
ENV FRONTEND_PORT=3000

# Expose ports
EXPOSE 8000 8083 8084 3000

# Health check script
COPY docker/healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Entry point script
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Default command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["start"]

# ================================================
# Build Arguments (optional)
# ================================================
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="hatena-blog-suite" \
      org.label-schema.description="Comprehensive Hatena Blog management and automation suite" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/chnmotoTmz/hatena-blog-suite" \
      org.label-schema.schema-version="1.0"
