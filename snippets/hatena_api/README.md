# Hatena API スニペット (`hatena_api`)

このカテゴリには、はてなブログのAtomPub APIと直接やり取りするためのスニペットが含まれています。
認証処理、APIリクエストの送信、レスポンスの解析など、API連携の基本的な部品を提供します。

## 概要

はてなブログAPIを利用することで、ブログ記事の投稿、更新、取得、削除などの操作をプログラムから自動的に行うことができます。
これらのスニペットは、そのためのコア機能を提供します。

## 含まれるスニペット

*   **`authentication.py`**:
    *   `generate_wsse_header(username: str, api_key: str) -> str`
    *   機能: はてなAPIリクエストに必要なWSSE認証ヘッダを生成します。
    *   主要な依存: `base64`, `hashlib`, `datetime`

*   **`xml_payload.py`**:
    *   `create_hatena_blog_entry_xml(...) -> bytes`
    *   機能: 記事の投稿や更新時にAtomPub APIへ送信するXMLペイロードを生成します。タイトル、本文、カテゴリ、下書き状態などを指定できます。
    *   主要な依存: `datetime`, `xml.sax.saxutils.escape`

*   **`client.py` (Class: `HatenaBlogClient`)**:
    *   機能: はてなブログAPIとの通信を行うクライアントクラスです。以下の主要メソッドを提供します。
        *   `post_entry(...)`: 新規記事を投稿します。
        *   `update_entry(...)`: 既存記事を更新します。
        *   `get_entries(...)`: 記事一覧を取得します（ページネーション対応）。
        *   `delete_entry(...)`: 記事を削除します。
    *   利用スニペット: `authentication.generate_wsse_header`, `xml_payload.create_hatena_blog_entry_xml`
    *   主要な依存: `requests`, `xml.etree.ElementTree`

*   **`multi_blog_config.py` (Class: `MultiBlogConfigManager`)**:
    *   機能: 複数の異なるはてなブログアカウントやドメインの設定（Hatena ID, Blog Domain, API Keyなど）を環境変数から読み込み、管理します。
    *   主要な依存: `os`, `python-dotenv` (間接的に利用されることを想定)

## 利用例

`HatenaBlogClient` を使った記事投稿の例：

```python
import os
from snippets.utils.env_loader import load_env # 環境変数読み込み用ユーティリティ
from snippets.hatena_api.client import HatenaBlogClient

# .envファイルからAPIキーなどを読み込む
load_env()

HATENA_ID = os.getenv("HATENA_ID")
BLOG_DOMAIN = os.getenv("BLOG_DOMAIN_TECH") # 例: 技術ブログ用ドメイン
API_KEY = os.getenv("HATENA_API_KEY_TECH")  # 例: 技術ブログ用APIキー

if not all([HATENA_ID, BLOG_DOMAIN, API_KEY]):
    print("必要な環境変数 (HATENA_ID, BLOG_DOMAIN_TECH, HATENA_API_KEY_TECH) を設定してください。")
else:
    client = HatenaBlogClient(hatena_id=HATENA_ID, blog_domain=BLOG_DOMAIN, api_key=API_KEY)

    title = "APIからのテスト投稿"
    content = "<p>これは <code>HatenaBlogClient</code> スニペットを使ったテスト投稿です。</p>"
    categories = ["テスト", "API投稿"]

    result = client.post_entry(title, content, is_draft=True, categories=categories)

    if result.get("status") == "success":
        print(f"投稿成功！ エントリーID: {result.get('entry_id')}, URL: {result.get('url')}")
    else:
        print(f"投稿失敗: {result.get('message')}")
```

## 注意点

*   APIキーは機密情報ですので、直接コードに記述せず、環境変数や設定ファイルを通じて安全に管理してください (`.env` ファイルと `env_loader.py` の利用を推奨)。
*   はてなブログAPIにはリクエスト数の制限がある場合があります。短時間に大量のリクエストを送信しないように注意してください。
*   各APIエンドポイントの正確な仕様や制約については、はてなブログの公式ドキュメントも参照してください。
