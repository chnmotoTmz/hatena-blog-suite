# はてなブログ自動化・支援スニペット集

このリポジトリは、はてなブログの運用を自動化・支援するためのPythonコードスニペット集です。
各スニペットは機能ごとにモジュール化されており、個別に利用したり、組み合わせてより高度な自動化システムを構築したりすることができます。

## 概要

このスニペット集は、以下のような目的で開発されました。

*   はてなブログAPIを利用した記事の投稿、更新、情報取得の自動化
*   記事コンテンツの品質向上（アフィリエイトリンクの管理、画像生成、内部リンクの最適化など）
*   自然言語処理技術やAI APIを活用した高度なテキスト分析とコンテンツ生成支援
*   ブログ運用戦略の効率化（リポスト管理、リンクチェック、パフォーマンス分析など）

各機能は独立したPythonファイル（スニペット）として提供されており、特定のタスクに再利用しやすくなっています。

## ディレクトリ構成

スニペットは、以下のカテゴリ別に分類されています。

*   `hatena_api/`: はてなブログAtomPub APIとの直接的な連携機能（認証、クライアントなど）。
*   `content_processing/`: 記事コンテンツの抽出、解析、キーワード抽出などの基本的な処理。
*   `content_enhancement/`: 既存コンテンツを強化する機能（アフィリエイト管理、画像生成など）。
*   `nlp_ai/`: 自然言語処理技術や外部AIサービス（Google Gemini, Cohere, OpenAI Embeddings, VectorDBなど）を利用した高度な機能。
*   `blog_management/`: ブログ運用全般を支援する機能（リンクチェック、パフォーマンス分析、リポスト戦略、記事移行など）。
*   `utils/`: 設定読み込み、ファイルI/O、ロギングなど、他のスニペットで共通して利用されるユーティリティ機能。

各カテゴリディレクトリ内にも、そのカテゴリのスニペットに関する詳細な`README.md`が含まれている場合があります。

## 利用方法

1.  **必要なライブラリのインストール**:
    各スニペットは特定の外部ライブラリに依存している場合があります。
    プロジェクトルート（または`snippets`ディレクトリ）に配置される`requirements.txt`（今後作成予定）を参照し、必要なライブラリをインストールしてください。
    ```bash
    pip install -r requirements.txt
    ```
    個々のスニペットファイルも、冒頭のimport文で依存関係を示しています。

2.  **環境変数の設定**:
    多くのスニペット（特にAPI連携やAIサービスを利用するもの）は、APIキーや設定値を環境変数経由で読み込みます。
    ルートディレクトリに`.env`ファイルを作成し、必要な情報を記述してください。
    テンプレートとして`.env.example`が提供されている場合は、それを参考にしてください。
    環境変数を読み込むためには、`snippets/utils/env_loader.py`のスニペットが利用できます。

3.  **スニペットの利用**:
    各`.py`ファイル内のクラスや関数をインポートして利用します。
    多くのファイルは、`if __name__ == '__main__':`ブロック内に簡単な使用例を含んでいますので、それを参考にしてください。

    例：はてなブログAPIクライアントの利用
    ```python
    from snippets.hatena_api.client import HatenaBlogClient
    from snippets.utils.env_loader import load_env

    load_env() # .envファイルから環境変数を読み込み

    HATENA_ID = os.getenv("HATENA_ID")
    BLOG_DOMAIN = os.getenv("BLOG_DOMAIN")
    API_KEY = os.getenv("HATENA_API_KEY")

    if HATENA_ID and BLOG_DOMAIN and API_KEY:
        client = HatenaBlogClient(hatena_id=HATENA_ID, blog_domain=BLOG_DOMAIN, api_key=API_KEY)
        entries_data = client.get_entries()
        if entries_data.get("status") == "success":
            for entry in entries_data.get("entries", []):
                print(f"Title: {entry.get('title')}")
    else:
        print("必要な環境変数が設定されていません。")
    ```

## スニペット解説書

各スニペットのより詳細な機能、使い方、APIリファレンス、設定方法、注意点などについては、`SNIPPET_GUIDE.md`（今後作成予定）を参照してください。

## 注意事項

*   APIを利用するスニペットは、各サービスの利用規約とAPIリクエスト制限に従って利用してください。
*   多くのスニペットはエラーハンドリングを含んでいますが、実際の運用では追加の堅牢なエラー処理が必要になる場合があります。
*   このスニペット集は学習・実験目的で提供されており、そのまま本番環境で利用する際には十分なテストと検証を行ってください。

## 今後の予定

*   各カテゴリごとの`README.md`の充実。
*   `SNIPPET_GUIDE.md`の作成。
*   `requirements.txt`の整備。
*   各スニペットのテストコードまたは実行サンプルの拡充。

ご不明な点や改善提案があれば、Issue等でお知らせください。
