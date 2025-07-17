# 本番環境用 Dockerfile
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# アプリケーションコードとデータディレクトリをコピー
COPY src/ ./src/
COPY data/ ./data/
COPY *.py ./
COPY *.sh ./

# ログディレクトリを作成
RUN mkdir -p /app/logs

# エントリポイントスクリプトを追加
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# ポートを公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーションを起動（entrypoint.shで再学習→本番起動）
ENTRYPOINT ["./entrypoint.sh"]