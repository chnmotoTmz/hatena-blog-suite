# Hatena Agent v2 - Multi-stage Docker Build
# クラウドコード環境対応コンテナ

# Stage 1: Python Environment
FROM python:3.11-slim as python-base

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Node.js Environment
FROM node:18-alpine as node-base

WORKDIR /app/hatena-rag-mcp

# Node.js依存関係のインストール
COPY hatena-rag-mcp/package*.json ./
RUN npm ci --production && npm cache clean --force

# TypeScriptのビルド
COPY hatena-rag-mcp/ ./
RUN npm run build

# Stage 3: PowerShell Environment
FROM mcr.microsoft.com/powershell:7.3-ubuntu-22.04 as powershell-base

# Stage 4: Final Runtime
FROM python:3.11-slim

# PowerShellのインストール
RUN apt-get update && apt-get install -y \
    wget \
    apt-transport-https \
    software-properties-common \
    && wget -q https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y powershell \
    && rm -rf /var/lib/apt/lists/* \
    && rm packages-microsoft-prod.deb

# Node.jsのインストール
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 作業ディレクトリの設定
WORKDIR /app

# Python環境のコピー
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Node.js環境のコピー
COPY --from=node-base /app/hatena-rag-mcp /app/hatena-rag-mcp

# アプリケーションファイルのコピー
COPY src/ ./src/
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY main.py ./
COPY run_windows.ps1 ./
COPY cloud-desktop-setup.ps1 ./

# 環境設定
COPY .env.docker .env

# ディレクトリ作成
RUN mkdir -p data logs output temp backup

# 権限設定
RUN chmod +x backend/api.ps1 && \
    chmod +x cloud-desktop-setup.ps1

# ヘルスチェック用スクリプト
COPY docker-healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# ポート公開
EXPOSE 8080 3000

# 環境変数
ENV PYTHONPATH=/app
ENV NODE_ENV=production
ENV API_HOST=0.0.0.0
ENV API_PORT=8080
ENV MCP_PORT=3000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/docker-healthcheck.sh

# 起動スクリプト
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["start"]