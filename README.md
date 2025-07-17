# ジャンル別プロンプトCSV（data/genre_prompts.csv）→RAGモデル変換について

このプロジェクトでは、ジャンル別プロンプト（data/genre_prompts.csv）をRAG（Retrieval Augmented Generation）用の検索モデルに変換して利用できます。


## 変換・学習手順

1. `data/genre_prompts.csv` を編集し、ジャンル・キーワード・プロンプトを記載します。
2. `src/rag.py` の `train_and_save_model` 関数を使い、CSVのプロンプト列を学習データとしてモデル（pklファイル）を作成します。
   - 例: genre_prompts.csvの「プロンプト」列をリスト化し、`train_and_save_model(texts, 'genre_prompts')` で保存。
3. モデルは `models/genre_prompts.pkl` として保存されます。
4. 本番APIやバッチ処理から `predict_with_model(query, 'genre_prompts', top_n=1)` でジャンル特化プロンプトを検索・取得できます。

## Docker本番起動時に自動再学習させる方法

1. `src/rag.py` に再学習用のスクリプト（例: `python -c "import pandas as pd; from src.rag import train_and_save_model; df = pd.read_csv('data/genre_prompts.csv'); texts = df['プロンプト'].tolist(); train_and_save_model(texts, 'genre_prompts')"`）をDockerfileやentrypoint.shで実行します。
2. 例: Dockerfileに以下を追加
   ```dockerfile
   RUN python -c "import pandas as pd; from src.rag import train_and_save_model; df = pd.read_csv('data/genre_prompts.csv'); texts = df['プロンプト'].tolist(); train_and_save_model(texts, 'genre_prompts')"
   ```
   または、entrypoint.shで
   ```bash
   python -c "import pandas as pd; from src.rag import train_and_save_model; df = pd.read_csv('data/genre_prompts.csv'); texts = df['プロンプト'].tolist(); train_and_save_model(texts, 'genre_prompts')"
   ```
3. これにより、コンテナ起動時に最新のCSV内容でモデルが再学習されます。


## 注意点
- CSVの文字コードはUTF-8で保存してください。
- 1ジャンル1行でも、複数行でもOKです。
- モデル再学習時は `models/genre_prompts.pkl` を上書きします。
- 必要な依存（janome, scikit-learn, pandas）は requirements.txt に記載済みです。

## サンプルコード
```python
import pandas as pd
from src.rag import train_and_save_model

df = pd.read_csv('data/genre_prompts.csv')
texts = df['プロンプト'].tolist()
success, msg = train_and_save_model(texts, 'genre_prompts')
print(msg)
```

---
# MCP-AI-Agent System (Minimal)

This is a minimal version of the MCP-AI-Agent system.

## Prerequisites

- Docker
- Docker Compose

## How to Run

1.  **Create a `.env.production` file:**

    Use the `.env.example` or `.env.production.template` as a reference.

2.  **Build and run the Docker container:**

    ```bash
    docker-compose up --build
    ```

3.  **The application will be available at `http://localhost:8000`**
