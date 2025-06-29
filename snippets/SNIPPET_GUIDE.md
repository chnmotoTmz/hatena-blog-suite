# スニペット解説書 - はてなブログ自動化・支援スニペット集

## 目次

1.  [はじめに](#はじめに)
2.  [共通事項](#共通事項)
    *   [環境設定](#環境設定)
    *   [基本的な使い方](#基本的な使い方)
3.  [カテゴリ別スニペット詳細解説](#カテゴリ別スニペット詳細解説)
    *   [1. `hatena_api` - はてなブログAPI連携](#1-hatena_api---はてなブログapi連携)
        *   [1.1. `HatenaBlogClient`](#11-hatenablogclient)
    *   [2. `content_processing` - 記事コンテンツ処理](#2-content_processing---記事コンテンツ処理)
        *   [2.1. `extractor.extract_hatena_article_details`](#21-extractorextract_hatena_article_details)
    *   [3. `content_enhancement` - コンテンツエンハンスメント](#3-content_enhancement---コンテンツエンハンスメント)
    *   [4. `nlp_ai` - 自然言語処理・AI連携](#4-nlp_ai---自然言語処理ai連携)
        *   [4.1. `vector_store.ChromaVectorStoreManager`](#41-vector_storechromavectorstoremanager)
        *   [4.2. `llm_integration` (Google Gemini & Cohere API連携)](#42-llm_integration-google-gemini--cohere-api連携)
    *   [5. `blog_management` - ブログ運用支援](#5-blog_management---ブログ運用支援)
    *   [6. `utils` - ユーティリティ](#6-utils---ユーティリティ)
4.  [今後の拡充予定](#今後の拡充予定)

---

## はじめに

このドキュメントは、「はてなブログ自動化・支援スニペット集」に含まれる各スニペットの機能、使い方、APIリファレンス、設定方法、注意点などを詳細に解説するものです。
スニペットを利用して独自の自動化ツールや分析システムを構築する際の参考としてください。

各スニペットは、特定のタスクを実行するための独立したコード部品として設計されていますが、組み合わせて使用することでより複雑な処理を実現できます。

---

## 共通事項

### 環境設定

多くのスニペット、特に外部API（はてなブログAPI、OpenAI API、Google Gemini API、Cohere APIなど）を利用するものは、APIキーや設定値を環境変数経由で読み込むように作られています。

1.  **`.env`ファイルの作成**:
    プロジェクトのルートディレクトリ（または`snippets`ディレクトリの親ディレクトリ）に`.env`という名前のファイルを作成してください。
    このファイルに、必要な環境変数をキー=値の形式で記述します。
    例:
    ```env
    # Hatena Blog API
    HATENA_ID="your_hatena_id"
    BLOG_DOMAIN_DEFAULT="your_default_blog.hatenablog.com"
    HATENA_API_KEY_DEFAULT="your_hatena_atompub_api_key"

    # OpenAI API (ChromaVectorStoreManagerのデフォルトEmbeddings用)
    OPENAI_API_KEY="sk-your_openai_api_key"

    # Google Gemini API
    GOOGLE_API_KEY="your_google_ai_studio_api_key"

    # Cohere API
    COHERE_API_KEY="your_cohere_api_key"

    # Bing Image Creator Cookie (image_generation.py用)
    # BING_AUTH_COOKIE_U="your_bing_cookie_U_value"
    ```
    **注意**: `.env`ファイルはGitなどのバージョン管理に含めないでください。リポジトリには、設定すべき項目を記述した`.env.example`ファイルを提供することを推奨します。

2.  **環境変数の読み込み**:
    Pythonスクリプト内でこれらの環境変数を読み込むには、`snippets/utils/env_loader.py`の`load_env()`関数を利用します。
    スクリプトの最初の方で一度呼び出すだけで、以降`os.getenv("VARIABLE_NAME")`でアクセスできるようになります。
    ```python
    from snippets.utils.env_loader import load_env
    load_env()
    # これで.envファイルの内容が環境変数としてロードされる
    ```

3.  **必要なライブラリのインストール**:
    各スニペットは外部ライブラリに依存している場合があります。
    提供される`requirements.txt`（今後作成）を使用して、必要なライブラリを一括でインストールしてください。
    ```bash
    pip install -r requirements.txt
    ```
    個々のスニペットファイルも、冒頭の`import`文で直接的な依存関係を示しています。

### 基本的な使い方

各スニペットは、Pythonファイルとして提供されており、通常はクラスまたは関数として定義されています。
これらを自分のスクリプトにインポートして使用します。

```python
# 例: hatena_api.client の HatenaBlogClient を使う場合
from snippets.hatena_api.client import HatenaBlogClient
import os

# (load_env() で環境変数がロードされている前提)
client = HatenaBlogClient(
    hatena_id=os.getenv("HATENA_ID"),
    blog_domain=os.getenv("BLOG_DOMAIN_DEFAULT"),
    api_key=os.getenv("HATENA_API_KEY_DEFAULT")
)
# result = client.get_entries()
# ...
```
多くのスニペットファイルには、末尾に`if __name__ == '__main__':`ブロックがあり、そのスニペットの基本的な使用例やテストコードが記述されています。これを実行して動作を確認したり、使い方を学んだりすることができます。

---

## カテゴリ別スニペット詳細解説

### 1. `hatena_api` - はてなブログAPI連携

はてなブログのAtomPub APIと直接通信し、記事の投稿、更新、取得などを行うためのスニペット群です。

#### 1.1. `HatenaBlogClient`

*   **ファイル**: `snippets/hatena_api/client.py`
*   **クラス**: `HatenaBlogClient`
*   **概要**: はてなブログAtomPub APIの操作をカプセル化したクライアントクラスです。WSSE認証、XMLペイロード生成、HTTPリクエスト送信、レスポンス解析などを内部で行います。
*   **主要な依存スニペット**:
    *   `snippets.hatena_api.authentication.generate_wsse_header`
    *   `snippets.hatena_api.xml_payload.create_hatena_blog_entry_xml`
*   **主要な外部ライブラリ**: `requests`, `xml.etree.ElementTree`

*   **初期化**:
    ```python
    client = HatenaBlogClient(
        hatena_id: str,      # あなたのはてなID
        blog_domain: str,    # 操作対象ブログのドメイン (例: yourid.hatenablog.com)
        api_key: str         # あなたのはてなブログAtomPub APIキー
    )
    ```

*   **主要メソッド**:

    *   `post_entry(title: str, content: str, is_draft: bool = False, categories: Optional[List[str]] = None) -> Dict`
        *   機能: 新しい記事をブログに投稿します。
        *   引数:
            *   `title`: 記事のタイトル。
            *   `content`: 記事の本文（HTML形式）。
            *   `is_draft`: `True`の場合、下書きとして投稿します（デフォルト: `False`）。
            *   `categories`: カテゴリ名のリスト（オプション）。
        *   戻り値: 投稿結果を示す辞書。
            *   成功時: `{"status": "success", "entry_id": "...", "url": "...", "edit_url": "...", "title": "...", "response_status_code": 201}`
            *   失敗時: `{"status": "error", "message": "...", "title": "...", "status_code": ...}`

    *   `update_entry(entry_id: str, title: str, content: str, is_draft: bool = False, categories: Optional[List[str]] = None) -> Dict`
        *   機能: 既存の記事を更新します。
        *   引数:
            *   `entry_id`: 更新対象記事のはてなエントリーID（数値部分）。
            *   その他引数は`post_entry`と同様。
        *   戻り値: 更新結果を示す辞書。
            *   成功時: `{"status": "success", "entry_id": "...", "title": "...", "public_link": "...", "response_status_code": 200}`
            *   失敗時: `{"status": "error", ...}`

    *   `get_entries(page_url: Optional[str] = None) -> Dict`
        *   機能: ブログの記事一覧を取得します。はてなAPIはページネーションを行うため、`page_url`引数で次ページのURLを指定できます。
        *   引数:
            *   `page_url`: 特定のページの記事一覧を取得するためのURL（APIレスポンス内の`next`リンクの値）。初回は`None`でOK。
        *   戻り値: 記事一覧データを含む辞書。
            *   成功時: `{"status": "success", "entries": List[Dict], "next_page_url": Optional[str], "response_status_code": 200}`
                *   `entries`内の各辞書は、記事ID(`id`), タイトル(`title`), 公開URL(`public_link`), 下書き状態(`is_draft`), 公開日(`published_date`), 更新日(`updated_date`), カテゴリ(`categories`)などを含みます。
            *   失敗時: `{"status": "error", ...}`

    *   `delete_entry(entry_id: str) -> Dict`
        *   機能: 指定されたエントリーIDの記事を削除します。**注意: この操作は元に戻せません。**
        *   引数:
            *   `entry_id`: 削除対象記事のはてなエントリーID。
        *   戻り値: 削除結果を示す辞書。
            *   成功時: `{"status": "success", "entry_id": "...", "message": "...", "response_status_code": 200 or 204}`
            *   失敗時: `{"status": "error", ...}`

*   **使用例**:
    ```python
    # (clientは初期化済みとする)
    # 新規投稿
    post_res = client.post_entry("APIテスト記事", "<p>こんにちは！</p>", categories=["テスト"])
    if post_res["status"] == "success":
        new_entry_id = post_res["entry_id"]
        print(f"投稿成功: ID={new_entry_id}")

        # 更新
        update_res = client.update_entry(new_entry_id, "APIテスト記事 (更新)", "<p>こんにちは！更新しました。</p>", is_draft=True)
        print(f"更新結果: {update_res['status']}")

        # 削除 (注意して実行)
        # delete_res = client.delete_entry(new_entry_id)
        # print(f"削除結果: {delete_res['status']}")
    else:
        print(f"投稿失敗: {post_res['message']}")

    # 記事一覧取得
    list_res = client.get_entries()
    if list_res["status"] == "success":
        print(f"{len(list_res['entries'])}件の記事を取得しました。")
        if list_res['entries']:
            print(f"最初の記事のタイトル: {list_res['entries'][0]['title']}")
    ```

*   **注意点**:
    *   APIキーは機密情報です。安全に管理してください。
    *   APIリクエスト制限に注意し、短時間に大量のリクエストを行わないでください。
    *   エラーハンドリング: 各メソッドは結果辞書に`status`キーを含みます。APIエラーやネットワークエラーが発生した場合、`status`は`"error"`となり、`message`キーに詳細が含まれることがあります。適宜確認してください。HTTPエラーが発生した場合は`requests.RequestException`が再送出される可能性があります。

---
(他のスニペットの解説は順次追加予定)

### 2. `content_processing` - 記事コンテンツ処理

記事コンテンツの抽出、解析、キーワード抽出などの基本的な処理を行います。

#### 2.1. `extractor.extract_hatena_article_details`

*   **ファイル**: `snippets/content_processing/extractor.py`
*   **関数**: `extract_hatena_article_details(article_url: str, fetch_content: bool = True) -> Optional[HatenaBlogArticleDetails]`
*   **概要**: 指定されたはてなブログの記事URLから、記事の構造化された詳細情報（タイトル、著者、日付、カテゴリ、本文HTML、テキストコンテンツ、画像リスト、リンクリスト、文字数など）を抽出します。`fetch_content=False` の場合、第一引数 `article_url` にHTML文字列を直接渡してパースすることも可能です。
*   **型エイリアス**:
    *   `HatenaBlogArticleDetails`: 抽出結果の辞書の型です。キーには `title`, `url`, `author`, `date`, `categories`, `full_html_content`, `text_content`, `images`, `links`, `word_count`, `raw_response_content` などが含まれます。
*   **主要な外部ライブラリ**: `requests` (URLからのHTML取得時), `BeautifulSoup4` (HTMLパース)

*   **引数**:
    *   `article_url: str`: 抽出対象のはてなブログ記事の完全なURL。または、`fetch_content=False` の場合は記事ページのHTMLコンテンツ文字列。
    *   `fetch_content: bool = True`:
        *   `True` (デフォルト): `article_url` をURLとして扱い、requestsでHTMLを取得してからパースします。
        *   `False`: `article_url` をHTMLコンテンツ文字列として直接パースします。この場合、抽出結果の `url` フィールドは空になるか、HTML内から取得できた場合に設定されます。

*   **戻り値**: `Optional[HatenaBlogArticleDetails]`
    *   抽出に成功した場合: 記事詳細情報を含む `HatenaBlogArticleDetails` 辞書。
    *   抽出に失敗した場合（URLアクセス不可、必須要素の欠如など）: `None`。

*   **抽出される主な情報**:
    *   `title`: 記事タイトル (主に `h1.entry-title` から)。
    *   `url`: 元の `article_url` (またはHTML内から取得できた場合)。
    *   `author`: 著者のはてなID (主にプロファイルリンクやメタタグから推定)。
    *   `date`: 記事の公開日（または更新日、ISO 8601形式の文字列、主に `<time datetime="...">` から）。
    *   `categories`: カテゴリ名のリスト (主に `a.entry-category-link` から)。
    *   `full_html_content`: 記事本文のHTMLコンテンツ (主に `div.entry-content` の内容)。
    *   `text_content`: `full_html_content` から抽出されたプレーンテキスト。
    *   `word_count`: `text_content` の単語数（簡易的なスペース区切り）。
    *   `images`: 記事本文中の画像情報リスト。各要素は `{'url': ..., 'alt': ..., 'title': ...}` 形式の辞書。
    *   `links`: 記事本文中のリンク情報リスト。各要素は `LinkDetail` 辞書（URL、アンカーテキスト、内部/外部リンク判定、元HTML要素など）。`extract_links_from_html` 関数によって抽出されます。
    *   `raw_response_content`: `fetch_content=True` の場合に取得した生のHTMLページコンテンツ。

*   **使用例**:
    ```python
    from snippets.content_processing.extractor import extract_hatena_article_details

    # URLから直接取得
    # url = "https://staff.hatenablog.com/entry/2024/03/25/150000" # 例
    # details = extract_hatena_article_details(url)
    # if details:
    #     print(f"タイトル: {details['title']}")
    #     print(f"著者: {details.get('author', 'N/A')}")
    #     print(f"カテゴリ数: {len(details.get('categories', []))}")

    # HTML文字列から抽出
    sample_html = """
    <html><head><title>テスト記事</title></head><body>
    <h1 class="entry-title"><a href="http://example.com/test">テスト記事のタイトル</a></h1>
    <div class="entry-content"><p>これが本文です。<img src="image.png"></p>
    <a class="entry-category-link">技術</a></div>
    <time datetime="2024-01-01T00:00:00Z"></time>
    </body></html>
    """
    details_from_html = extract_hatena_article_details(sample_html, fetch_content=False)
    if details_from_html:
        print(f"HTMLからのタイトル: {details_from_html['title']}")
        # HTMLから抽出する場合、base_article_urlを別途指定してリンクのis_internalを正しく判定させる必要がある
        # from snippets.content_processing.extractor import extract_links_from_html
        # if details_from_html['full_html_content']:
        #     links = extract_links_from_html(details_from_html['full_html_content'], base_article_url="http://example.com/test")
        #     print(f"HTMLからのリンク数: {len(links)}")
    ```

*   **注意点**:
    *   HTML構造への依存: この関数は一般的なはてなブログのHTML構造（特定のクラス名やタグ）を前提として情報を抽出します。ブログテーマのカスタマイズや、はてなブログ自体の仕様変更により、期待通りに情報が抽出できなくなる可能性があります。その場合は、コード内のCSSセレクタ等を調整する必要があります。
    *   著者IDの推定: 著者のはてなIDは複数の箇所から推定を試みますが、確実ではない場合があります。
    *   日付情報: `<time>` タグの `datetime` 属性から取得しますが、これが更新日なのか公開日なのかはブログテーマに依存する可能性があります。
    *   `fetch_content=True` の場合、`requests` ライブラリによるHTTP GETリクエストが発生します。大量のURLを処理する場合は、対象サーバーへの負荷や自身のネットワーク環境に注意してください。

---
### 3. `content_enhancement` - コンテンツエンハンスメント
(主要スニペットの詳細解説をここに追加)

---
### 4. `nlp_ai` - 自然言語処理・AI連携

自然言語処理技術や外部AIサービスを利用した高度な機能を提供します。

#### 4.1. `vector_store.ChromaVectorStoreManager`

*   **ファイル**: `snippets/nlp_ai/vector_store.py`
*   **クラス**: `ChromaVectorStoreManager`
*   **概要**: LangchainライブラリとChromaDBを利用して、テキストドキュメント（記事など）のVectorStore（ベクトルデータベース）を管理します。ドキュメントのチャンキング（適切な長さに分割）、エンベディング（テキストをベクトルに変換）、ChromaDBへの保存、およびクエリに基づいた類似度検索（セマンティック検索）機能を提供します。デフォルトではOpenAIのテキストエンベディングモデル（`text-embedding-ada-002`など）を利用しますが、他のLangchain互換エンベディング関数も指定可能です。
*   **主要な外部ライブラリ**: `langchain`, `openai` (デフォルトEmbeddings用), `chromadb` (VectorStore本体), `tiktoken` (OpenAIのトークナイザ)

*   **初期化**:
    ```python
    manager = ChromaVectorStoreManager(
        openai_api_key: str,  # OpenAI APIキー (デフォルトEmbeddings用)
        persist_directory: Optional[str] = "./chroma_db_store", # DB保存先
        collection_name: Optional[str] = "langchain",          # ChromaDBコレクション名
        embedding_function: Optional[Any] = None,              # カスタムEmbeddings関数
        text_splitter_chunk_size: int = 1000,                  # テキスト分割チャンクサイズ
        text_splitter_chunk_overlap: int = 200                 # チャンクオーバーラップ
    )
    ```
    *   `openai_api_key` は `embedding_function` を指定しない場合に必須です。
    *   `persist_directory` にデータベースファイルが保存されます。指定しない場合、デフォルトのパスが使用されます。

*   **主要メソッド**:

    *   `add_articles(articles: List[Dict[str, Any]], batch_size: int = 100) -> bool`
        *   機能: 記事（辞書のリスト）をVectorStoreに追加します。各記事はLangchainの`Document`オブジェクトに変換され、テキスト分割、エンベディングが行われた上でChromaDBに格納されます。
        *   引数:
            *   `articles`: 記事データのリスト。各辞書は最低でも`content`（または`text`）キーに本文を含み、任意で`metadata`キーにメタデータ辞書を持つことができます。`id`, `title`, `url`などのトップレベルキーも自動的にメタデータに含められます。
            *   `batch_size`: (現在は内部処理に影響しないが、将来的な大規模追加用)
        *   戻り値: 追加処理が成功すれば`True`、失敗すれば`False`。

    *   `load_store() -> bool`
        *   機能: `persist_directory` から既存のChromaDBを読み込みます。`add_articles` を呼ばずに既存DBに対して検索を行いたい場合に事前に呼び出します。
        *   戻り値: ロード成功なら`True`、失敗なら`False`。

    *   `similarity_search(query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[LangchainDocument, float]]`
        *   機能: 指定されたクエリ文字列に意味的に類似するドキュメントをVectorStoreから検索します。
        *   引数:
            *   `query`: 検索クエリ文字列。
            *   `k`: 取得する類似ドキュメントの最大数（デフォルト: 5）。
            *   `filter_metadata`: メタデータに基づいて検索結果をフィルタリングするための辞書（例: `{"source": "blog_X", "year": 2023}`）。ChromaDBの`where`句に渡されます。
        *   戻り値: `(LangchainDocument, float)` のタプルのリスト。各タプルは類似したドキュメントとその類似度スコア（通常、距離なので低いほど類似度が高いが、Langchainのラッパーはスコアとして返す場合がある。Chromaのデフォルトは距離）。リストは類似度が高い順にソートされます。

    *   `get_collection_count() -> Optional[int]`
        *   機能: VectorStore内のアイテム（チャンク）数を返します。

*   **使用例**:
    ```python
    # from snippets.utils.env_loader import load_env
    # import os
    # load_env()
    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # if OPENAI_API_KEY:
    #     db_manager = ChromaVectorStoreManager(
    #         openai_api_key=OPENAI_API_KEY,
    #         persist_directory="./my_article_embeddings"
    #     )

    #     # サンプル記事データ
    #     my_articles = [
    #         {"id": "a001", "title": "Python入門", "content": "Pythonは初心者にも学びやすい言語です。多くのライブラリがあります。", "metadata": {"tags": ["python", "beginner"]}},
    #         {"id": "a002", "title": "データサイエンスとPython", "content": "データ分析や機械学習の分野ではPythonが広く使われています。", "metadata": {"tags": ["python", "ml", "data"]}},
    #         {"id": "a003", "title": "Web開発をはじめよう", "content": "DjangoやFlaskといったフレームワークでWebアプリを作れます。", "metadata": {"tags": ["web", "django"]}}
    #     ]

    #     # 記事をVectorStoreに追加 (初回はDBが作成される)
    #     db_manager.add_articles(my_articles)

    #     # 類似記事を検索
    #     query_text = "パイソンで機械学習をやるには"
    #     search_results = db_manager.similarity_search(query_text, k=1)

    #     if search_results:
    #         doc, score = search_results[0]
    #         print(f"クエリ「{query_text}」に最も類似する記事:")
    #         print(f"  ID: {doc.metadata.get('id')}, Title: {doc.metadata.get('title')}")
    #         print(f"  類似度スコア: {score:.4f}") # スコアの意味はEmbeddingと距離関数による
    #         print(f"  内容抜粋: {doc.page_content[:100]}...")
    # else:
    #     print("OPENAI_API_KEYが設定されていません。ChromaVectorStoreManagerのテストをスキップします。")
    ```

*   **設定と注意点**:
    *   **OpenAI APIキー**: デフォルトの`OpenAIEmbeddings`を利用する場合、環境変数`OPENAI_API_KEY`が設定されているか、初期化時に`openai_api_key`引数で渡す必要があります。
    *   **チャンキング**: `text_splitter_chunk_size`と`text_splitter_chunk_overlap`は、ドキュメントをどの程度の大きさに分割してエンベディングするかの設定です。検索精度やコンテキストの保持に影響します。対象ドキュメントの性質に合わせて調整してください。
    *   **永続化**: `persist_directory`に指定されたパスにChromaDBのデータファイルが保存されます。再度同じパスで初期化するか`load_store()`を呼ぶことで、既存のDBを再利用できます。
    *   **Embeddings**: デフォルトはOpenAIですが、`HuggingFaceEmbeddings`など、Langchainがサポートする他のエンベディング関数インスタンスを`embedding_function`引数で渡すことで、異なるエンベディングモデルも利用可能です。その場合、`openai_api_key`は不要になることがあります。
    *   **コスト**: OpenAI Embeddings APIなど、外部のエンベディングサービスを利用する場合、APIコール数やトークン数に応じた費用が発生します。
    *   **類似度スコア**: ChromaDBの`similarity_search_with_score`が返すスコアは、使用する距離関数によって意味合いが変わります（例: コサイン類似度なら高い方が類似、ユークリッド距離なら低い方が類似）。LangchainのChromaラッパーはこれを正規化したり、特定のスコアタイプで返したりすることがあります。ChromaDBのデフォルトはL2距離（ユークリッド距離）なので、スコアが低いほど類似度が高いです。

#### 4.2. `llm_integration` (Google Gemini & Cohere API連携)

*   **ファイル**: `snippets/nlp_ai/llm_integration.py`
*   **概要**: GoogleのGemini APIおよびCohereのAPIと連携し、テキスト生成、要約、キーワード抽出などの機能を提供する関数群です。これらの関数を利用することで、ブログ記事のアイデア発想、下書き作成、内容改善などをAIの支援を受けながら行うことができます。
*   **主要な外部ライブラリ**: `requests` (HTTP通信用), `json`

*   **共通事項**:
    *   **APIキー**: 各関数を利用するには、それぞれのサービスプロバイダ（Google AI Studio, Cohere Dashboard）から取得したAPIキーが必要です。これらは環境変数 (`GOOGLE_API_KEY`, `COHERE_API_KEY`) 経由で渡すことを推奨します。
    *   **エラーハンドリング**: 各関数は、APIリクエストの失敗や予期せぬレスポンスの場合に`None`を返すか、エラーメッセージを含む文字列を返すことがあります。利用時は戻り値を確認してください。詳細は各関数のdocstringを参照。
    *   **モデル指定**: 各関数には使用するモデルを指定する引数 (`model`) があります。利用可能なモデルは各サービスのドキュメントを確認してください（例: Gemini: `gemini-1.5-flash-latest`, `gemini-pro`; Cohere: `command`, `command-r`, `command-light`など）。

*   **Google Gemini API連携関数**:

    *   `summarize_chat_history_google(chat_history: List[Dict[str, str]], api_key: str, model: str = "gemini-1.5-flash-latest") -> Optional[str]`
        *   機能: チャット履歴（ユーザーとモデルの発言リスト）をGemini APIに送信し、その要約を取得します。
        *   引数:
            *   `chat_history`: メッセージ辞書（`{"role": "USER" or "CHATBOT", "message": "..."}`）のリスト。
            *   `api_key`: Google APIキー。
            *   `model`: 使用するGeminiモデル名。
        *   戻り値: 要約されたテキスト文字列、またはエラー時`None`。

    *   `generate_response_google(chat_history: List[Dict[str, str]], new_message: str, api_key: str, model: str = "gemini-1.5-flash-latest", system_instruction: Optional[str] = None) -> Optional[str]`
        *   機能: チャット履歴と新しいユーザーメッセージに基づき、Gemini APIから次の応答を生成します。
        *   引数:
            *   `chat_history`: 既存のチャット履歴。
            *   `new_message`: ユーザーの新しい発言。
            *   `api_key`: Google APIキー。
            *   `model`: 使用するGeminiモデル名。
            *   `system_instruction`: モデルへのシステムレベルの指示（オプション）。Gemini APIでは、履歴の最初のユーザー発言としてシステム指示を組み込むことが一般的です。
        *   戻り値: 生成された応答テキスト文字列、またはエラー時`None`。

*   **Cohere API連携関数**:

    *   `generate_summary_cohere(text_to_summarize: str, api_key: str, length: str = "medium", model: str = "command") -> Optional[str]`
        *   機能: Cohere APIを利用して、与えられたテキストを要約します。
        *   引数:
            *   `text_to_summarize`: 要約対象のテキスト。
            *   `api_key`: Cohere APIキー。
            *   `length`: 要約の長さ（`"short"`, `"medium"`, `"long"`）。
            *   `model`: 使用するCohereモデル名。
        *   戻り値: 要約されたテキスト文字列、またはエラー時`None`。

    *   `extract_keywords_cohere(text_to_extract_from: str, api_key: str, num_keywords: int = 5, model: str = "command") -> Optional[List[str]]`
        *   機能: Cohere APIのGenerateエンドポイントを利用して、テキストから指定された数のキーワードを抽出します。内部的にはキーワード抽出に適したプロンプトを生成してAPIを呼び出します。
        *   引数:
            *   `text_to_extract_from`: キーワード抽出対象のテキスト。
            *   `api_key`: Cohere APIキー。
            *   `num_keywords`: 抽出したいキーワードの数。
            *   `model`: 使用するCohereモデル名。
        *   戻り値: 抽出されたキーワードのリスト（文字列）、またはエラー時`None`。

    *   `generate_response_cohere(chat_history: List[Dict[str, str]], new_message: str, api_key: str, model: str = "command-r", system_message: Optional[str] = None, connectors: Optional[List[Dict[str, str]]] = None) -> Optional[str]`
        *   機能: CohereのChat APIを利用して、チャット履歴と新しいユーザーメッセージに基づき応答を生成します。Web検索などのコネクタも利用可能です。
        *   引数:
            *   `chat_history`: 既存のチャット履歴。Cohere APIが期待するロール（`"USER"`, `"CHATBOT"`, `"SYSTEM"`, `"TOOL"`）に変換されます。
            *   `new_message`: ユーザーの新しい発言。
            *   `api_key`: Cohere APIキー。
            *   `model`: 使用するCohereモデル名（`command-r`などがチャットに適しています）。
            *   `system_message`: モデルへのシステムレベルの指示（Cohereでは`preamble`として扱われます）。
            *   `connectors`: 使用するコネクタのリスト（例: `[{"id": "web-search"}]`）。
        *   戻り値: 生成された応答テキスト文字列、またはエラー時`None`。ツールコールが返された場合はその旨を示す文字列を返すことがあります。

*   **使用例 (Cohereキーワード抽出)**:
    ```python
    # from snippets.utils.env_loader import load_env
    # import os
    # from snippets.nlp_ai.llm_integration import extract_keywords_cohere

    # load_env()
    # COHERE_API_KEY = os.getenv("COHERE_API_KEY")

    # if COHERE_API_KEY:
    #     sample_text = "この記事では、最新のAI技術トレンドと、それがビジネスに与える影響について詳しく解説します。特に生成AIと倫理的側面が重要です。"
    #     keywords = extract_keywords_cohere(sample_text, api_key=COHERE_API_KEY, num_keywords=4)
    #     if keywords:
    #         print(f"抽出されたキーワード: {keywords}")
    #     else:
    #         print("キーワードの抽出に失敗しました。")
    # else:
    #     print("COHERE_API_KEYが設定されていません。")
    ```

*   **注意点**:
    *   **コストと利用制限**: Gemini API、Cohere APIともに、利用量に応じた課金が発生したり、無料利用枠には制限があったりします。各サービスの最新の料金体系と利用規約を確認してください。
    *   **レスポンス時間**: LLM APIからのレスポンスには数秒から数十秒かかることがあります。非同期処理やタイムアウト設定を適切に行ってください（このスニペット内の関数は同期的なHTTPリクエストです）。
    *   **プロンプトエンジニアリング**: 生成されるテキストの品質は、APIに渡すプロンプト（指示）の内容に大きく依存します。期待する結果を得るためには、プロンプトの工夫（明確な指示、例示、文脈提供など）が重要です。
    *   **エラーハンドリング**: APIからのエラーレスポンス（レート制限、認証エラー、無効なリクエストなど）を適切に処理できるように、呼び出し側で戻り値を確認し、必要に応じてリトライ処理などを実装してください。
    *   **コンテンツの信頼性**: LLMは時に誤った情報や不自然なテキストを生成すること（ハルシネーション）があります。生成されたコンテンツは必ず人間が確認し、ファクトチェックを行うなど、慎重に扱ってください。

---
### 5. `blog_management` - ブログ運用支援
(主要スニペットの詳細解説をここに追加)

---
### 6. `utils` - ユーティリティ
(主要スニペットの詳細解説をここに追加)

---

## 今後の拡充予定

*   各カテゴリの未解説スニペットに関する詳細情報を追加。
*   より実践的な組み合わせ利用例の追加。
*   各スニペットのパフォーマンスに関する情報や最適化のヒント。
*   トラブルシューティングガイド。
*   貢献方法（もしあれば）。

---
