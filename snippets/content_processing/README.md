# Content Processing スニペット (`content_processing`)

このカテゴリには、ブログ記事のコンテンツ（主にHTMLやテキスト）から情報を抽出したり、解析したりするための基本的な処理を行うスニペットが含まれています。
構造化されていないデータから有用な情報を取り出すための部品を提供します。

## 概要

記事コンテンツは、多くの場合HTML形式で提供されます。これらのスニペットは、HTMLをパースして必要な要素（タイトル、本文、日付、カテゴリ、リンク、画像など）を抽出したり、テキストデータからキーワードを抽出したりする機能を提供します。
他のスニペット（例: コンテンツエンハンスメント、NLP/AI連携）の前処理として利用されることが多いです。

## 含まれるスニペット

*   **`extractor.py`**:
    *   `extract_hatena_article_details(article_url: str, fetch_content: bool = True) -> Optional[HatenaBlogArticleDetails]`
        *   機能: 指定されたはてなブログの記事URLから、記事のタイトル、著者、日付、カテゴリ、本文HTML、テキストコンテンツ、画像リスト、リンクリスト、文字数などの詳細情報を抽出します。`fetch_content=False` の場合は、第一引数にHTML文字列を直接渡すことも可能です。
        *   主要な依存: `requests`, `BeautifulSoup4`, `urllib.parse`
    *   `extract_links_from_html(html_content: str, base_article_url: Optional[str] = None) -> List[LinkDetail]`
        *   機能: HTMLコンテンツ文字列から全てのハイパーリンク（`<a>`タグ）を抽出し、各リンクのURL、アンカーテキスト、内部/外部リンク判定、元HTML要素などをリストで返します。`base_article_url` を指定すると、相対URLの解決や内部/外部リンクの判定精度が向上します。
        *   主要な依存: `BeautifulSoup4`, `urllib.parse`

*   **`keyword_extractor.py` (Class: `KeywordExtractor`)**:
    *   機能: 与えられた日本語テキストからキーワードを抽出します。MeCabが利用可能な場合はMeCabを使用して品詞情報（名詞、形容詞、動詞の原形など）に基づいてキーワードを抽出します。MeCabが利用できない場合は、正規表現に基づいた簡易的な単語分割によるフォールバック処理を行います。
    *   主要メソッド: `extract_keywords(text: str, min_word_length: int = 2, use_mecab_if_available: bool = True) -> List[str]`
    *   主要な依存: `MeCab` (オプション、推奨), `re`

## 利用例

記事URLから詳細情報を抽出する例：

```python
from snippets.content_processing.extractor import extract_hatena_article_details

article_url = "https://staff.hatenablog.com/entry/2024/03/25/150000" # 例: はてなスタッフブログの記事
details = extract_hatena_article_details(article_url)

if details:
    print(f"タイトル: {details.get('title')}")
    print(f"公開日: {details.get('date')}")
    print(f"カテゴリ: {details.get('categories')}")
    print(f"最初の画像URL: {details.get('images')[0]['url'] if details.get('images') else 'N/A'}")
    # print(f"本文 (最初の100文字): {details.get('text_content', '')[:100]}...")
else:
    print(f"記事情報の抽出に失敗しました: {article_url}")
```

テキストからキーワードを抽出する例：

```python
from snippets.content_processing.keyword_extractor import KeywordExtractor

extractor = KeywordExtractor() # MeCabが利用可能ならMeCabを使用
text = "Pythonを使った機械学習とデータ分析の入門。東京特許許可局。"
keywords = extractor.extract_keywords(text)
print(f"抽出されたキーワード: {keywords}")

# MeCabなしで実行を強制する場合
# keywords_fallback = extractor.extract_keywords(text, use_mecab_if_available=False)
# print(f"抽出されたキーワード (フォールバック): {keywords_fallback}")
```

## 注意点

*   HTMLからの情報抽出は、ウェブページの構造に依存するため、対象ブログのテーマやHTML構造が大きく変更された場合に正しく動作しなくなる可能性があります。`extractor.py` は一般的なはてなブログの構造を想定していますが、適宜セレクタの調整が必要になることがあります。
*   `keyword_extractor.py` でMeCabを利用する場合、MeCab本体および適切な辞書（例: `mecab-ipadic-neologd`）がシステムにインストールされている必要があります。インストールされていない場合は、簡易的なフォールバック処理が実行されますが、抽出精度は低下します。
*   大量のURLから記事情報を連続して取得する場合、対象サーバーへの負荷に配慮し、適切なウェイト処理（リクエスト間隔の調整）を実装してください。
