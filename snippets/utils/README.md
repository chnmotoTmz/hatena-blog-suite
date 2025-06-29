# Utility スニペット (`utils`)

このカテゴリには、他のスニペットやプロジェクト全体で共通して利用できる汎用的なユーティリティ関数が含まれています。
特定のビジネスロジックに依存せず、さまざまな場面で再利用可能な基本的な機能を提供します。

## 概要

効率的な開発のためには、よく使われる処理を共通化・部品化することが重要です。
このディレクトリのスニペットは、以下のような基本的なタスクを支援します。

*   設定ファイル（`.env`など）からの環境変数の読み込み
*   データファイル（JSON, Pickleなど）の読み書き
*   標準的なロギングの設定

これらのユーティリティは、他のカテゴリのスニペットを動作させる上での前提条件となることもあります（例: APIキーを環境変数から読み込む場合など）。

## 含まれるスニペット

*   **`env_loader.py`**:
    *   `load_env(env_path: str = None) -> bool`
    *   機能: `.env`ファイル（プロジェクトルートなどに配置）から環境変数を読み込み、Pythonの実行環境に設定します。`python-dotenv`ライブラリを利用します。
    *   主要な依存: `python-dotenv`, `os`

*   **`file_io.py`**:
    *   `save_json(data: Any, filepath: str) -> None`
    *   `load_json(filepath: str) -> Any`
    *   `save_pickle(data: Any, filepath: str) -> None`
    *   `load_pickle(filepath: str) -> Any`
    *   機能: Pythonのデータ構造（辞書、リストなど）をJSON形式またはPickle形式でファイルに保存したり、ファイルから読み込んだりするための関数群です。
    *   主要な依存: `json`, `pickle`

*   **`logger_config.py`**:
    *   `setup_logger(...) -> logging.Logger`
    *   機能: Python標準の`logging`モジュールを用いて、ログレベル、フォーマット、出力先（コンソール、ファイル）などを指定してロガーを簡単にセットアップするための関数です。
    *   主要な依存: `logging`, `sys`

## 利用例

環境変数の読み込みと利用：

```python
# --- main_script.py ---
import os
from snippets.utils.env_loader import load_env
from snippets.utils.logger_config import setup_logger

# アプリケーション開始時に一度だけ呼び出す
load_env() # .env ファイルを探して読み込む

# ロガーを設定
logger = setup_logger("MyAppLogger")

API_KEY = os.getenv("MY_SERVICE_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true" # デフォルト値と型変換

if not API_KEY:
    logger.error("環境変数 MY_SERVICE_API_KEY が設定されていません！")
else:
    logger.info(f"APIキーをロードしました。デバッグモード: {DEBUG_MODE}")
    # ... API_KEYを使った処理 ...

# --- .env (プロジェクトルートに配置) ---
# MY_SERVICE_API_KEY="your_actual_api_key_here"
# DEBUG_MODE=True
```

JSONファイルへのデータ保存と読み込み：

```python
from snippets.utils.file_io import save_json, load_json

my_data = {"name": "ブログ設定", "version": 2, "settings": {"theme": "dark", "posts_per_page": 10}}
config_filepath = "blog_config.json"

# データを保存
save_json(my_data, config_filepath)

# 保存したデータを読み込み
loaded_data = load_json(config_filepath)
if loaded_data:
    print(f"読み込んだ設定テーマ: {loaded_data.get('settings', {}).get('theme')}")
```

## 注意点

*   **`.env`ファイルの管理**: `.env`ファイルにはAPIキーなどの機密情報が含まれることが多いため、Gitなどのバージョン管理システムには含めないように注意してください（`.gitignore`に`.env`を追加することを推奨）。代わりに、リポジトリには設定すべき項目を記述した`.env.example`ファイルを含めるのが一般的です。
*   **Pickleのセキュリティ**: `load_pickle`は信頼できないソースからのPickleデータを読み込む際にセキュリティリスク（任意のコード実行の可能性）があります。信頼できるデータソースに対してのみ使用してください。JSONの方が一般的に安全なデータ交換形式です。
*   **ロギング**: `setup_logger`で設定したロガーは、アプリケーションの様々なモジュールから`logging.getLogger("LoggerName")`で取得して利用できます。ルートロガーを設定することも、名前付きロガーを階層的に利用することも可能です。アプリケーション全体で一貫したロギング戦略を立てることが重要です。
