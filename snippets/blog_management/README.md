# Blog Management スニペット (`blog_management`)

このカテゴリには、ブログの日常的な運用や戦略的な管理を支援するためのスニペットが含まれています。
リンクの健全性チェック、記事パフォーマンスの分析、コンテンツの再利用（リポスト）戦略の立案と実行支援、ブログ間の記事移行などが主な機能です。

## 概要

効果的なブログ運用には、コンテンツの品質維持だけでなく、戦略的な視点も不可欠です。
これらのスニペットは、以下のようなタスクを自動化または支援することで、ブログ管理の効率化と品質向上を目指します。

*   記事内のリンク切れを定期的にチェックし、ユーザビリティを維持します。
*   記事のパフォーマンス（例: 公開日からの経過、エンゲージメント指標など）を分析し、改善点や人気コンテンツを把握します。
*   過去の優良な記事を適切なタイミングで再編集・再投稿（リポスト）するための計画を立て、実行を支援します。
*   複数のブログを運営している場合に、ブログ間で記事を移行する作業を支援します。

## 含まれるスニペット

*   **`link_checker.py` (Class: `AsyncLinkChecker`)**:
    *   機能: HTMLコンテンツ内からリンクを抽出し、それらのURLの有効性（200 OK, 404 Not Found, リダイレクトなど）を非同期で高速にチェックします。チェック結果から簡易的なレポートを生成する機能も持ちます。
    *   利用スニペット（内部で想定）: `snippets.content_processing.extractor.extract_links_from_html`
    *   主要メソッド: `check_multiple_urls(...)`, `check_links_in_html_content(...)`, `generate_report_from_results(...)`
    *   主要な依存: `aiohttp`, `asyncio` (Python標準)

*   **`performance_analyzer.py` (Class: `ArticlePerformanceScorer`)**:
    *   機能: 個々の記事のメタデータ（公開日、カテゴリ数、文字数、アクセス数、コメント数など、利用可能な指標に基づく）から、カスタマイズ可能な重み付けで「パフォーマンススコア」を算出します。これにより、記事の相対的なパフォーマンスを評価し、ランキングすることができます。
    *   主要メソッド: `calculate_score(article_meta: ArticleMetadata) -> float`, `rank_articles(articles_metadata: List[ArticleMetadata]) -> List[Dict[str, Any]]`
    *   主要な依存: `datetime`

*   **`repost_scheduler.py` (Class: `RepostScheduler`)**:
    *   機能: 記事の再投稿（リポスト）戦略を支援します。
        *   `performance_analyzer` でスコアリングされた記事とリポスト履歴を元に、再投稿に適した記事候補を選定します。
        *   選定された記事に対して、数週間分のリポストカレンダー（推奨公開日、更新タイプ、準備メモなどを含む）を生成します。
        *   リポスト用の記事コンテンツ（新しいタイトル、導入文、更新点、元記事へのリンクなど）を生成します。
        *   リポストの実行履歴を記録・管理します。
    *   利用スニペット（内部で想定）: `snippets.blog_management.performance_analyzer.ArticlePerformanceScorer`
    *   主要メソッド: `select_articles_for_reposting(...)`, `create_repost_calendar(...)`, `generate_repost_content_from_candidate(...)`, `record_repost_in_history(...)`
    *   主要な依存: `datetime`, `json` (履歴保存用), `hashlib`

*   **`article_migrator.py` (Class: `ArticleMigrator`)**:
    *   機能: あるはてなブログから別の（または同じ）はてなブログへ記事を移行（コピーまたは移動）します。移行元記事のコンテンツ、タイトル、カテゴリなどを取得し、移行先ブログに新しい記事として投稿します。移行元記事の削除オプションも提供します。
    *   利用スニペット（内部で想定）: `snippets.hatena_api.client.HatenaBlogClient`
    *   主要メソッド: `migrate_article(source_entry_id: str, ... ) -> Dict[str, Any]`
    *   主要な依存: (HatenaBlogClientに依存)

## 利用例

記事内リンクのチェック例：

```python
import asyncio
from snippets.blog_management.link_checker import AsyncLinkChecker
# from snippets.content_processing.extractor import extract_hatena_article_details # 記事HTML取得用

# async def check_article_links(article_url_to_check):
#    # 1. 記事HTMLを取得 (例: extract_hatena_article_detailsを使用)
#    # article_details = extract_hatena_article_details(article_url_to_check)
#    # if not article_details or not article_details.get('full_html_content'):
#    #     print(f"記事HTMLの取得失敗: {article_url_to_check}")
#    #     return

#    # html_content = article_details['full_html_content']
#    # base_url = article_details['url']
#    # article_title = article_details['title']

#    # ダミーHTMLでテスト
#    html_content = "<p><a href='http://example.com/good'>Good</a> <a href='http://example.com/broken'>Broken</a></p>"
#    base_url = "http://example.com"
#    article_title = "Test Article for Links"

#    checker = AsyncLinkChecker()
#    link_check_results = await checker.check_links_in_html_content(html_content, base_url)
#    report = checker.generate_report_from_results(link_check_results, article_title=article_title)
#    print(report)

# if __name__ == '__main__':
#    asyncio.run(check_article_links("YOUR_ARTICLE_URL_HERE"))
```

リポストスケジュールの作成例：

```python
# from snippets.blog_management.performance_analyzer import ArticlePerformanceScorer, ArticleMetadata
# from snippets.blog_management.repost_scheduler import RepostScheduler
# from datetime import datetime, timedelta, timezone

# # 1. スコアラーとスケジューラーを初期化
# scorer = ArticlePerformanceScorer()
# scheduler = RepostScheduler(performance_scorer=scorer, min_days_between_reposts=60)

# # 2. 分析対象の記事メタデータリストを準備 (実際にはAPIやDBから取得)
# articles_meta = [
#    ArticleMetadata(id="1", title="古いけど良い記事", url="http://example.com/1", date_published=(datetime.now(timezone.utc)-timedelta(days=300)).isoformat(), categories=["Tech"], word_count=1500),
#    ArticleMetadata(id="2", title="最近の記事", url="http://example.com/2", date_published=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat(), categories=["News"], word_count=500),
# ]
# # ... 他の記事メタデータを追加

# # 3. リポスト候補を選定
# candidates = scheduler.select_articles_for_reposting(articles_meta, max_candidates=5)

# # 4. リポストカレンダーを作成
# calendar = scheduler.create_repost_calendar(candidates, weeks_ahead_to_schedule=4, posts_per_week=1)

# print("リポストカレンダー:")
# for item in calendar:
#    print(f"- {item['suggested_publish_date'][:10]}: {item['article_metadata']['title']} ({item['suggested_update_type']})")
#    print(f"  準備メモ: {item['preparation_notes']}")

# # 5. (オプション) 最初の候補記事のリポスト用コンテンツを生成
# if calendar:
#    first_candidate = calendar[0]
#    # 元記事のHTMLコンテンツを取得する処理が別途必要
#    original_html = f"<p>これが「{first_candidate['article_metadata']['title']}」の素晴らしい元記事コンテンツです。</p>"
#    repost_details = scheduler.generate_repost_content_from_candidate(first_candidate, original_html)
#    print(f"\\nリポスト用タイトル: {repost_details['title']}")
```

## 注意点

*   **外部依存**: `link_checker`は`aiohttp`に、`article_migrator`は`hatena_api.client`に依存します。
*   **設定ファイル**: `repost_scheduler`はリポスト履歴をJSONファイルに保存・読み込みします。ファイルパスは適切に設定してください。
*   **API利用**: `article_migrator`がはてなブログAPIを利用する際は、APIの利用規約とリクエスト制限に注意してください。
*   **データ取得**: `performance_analyzer`や`repost_scheduler`が効果的に機能するためには、分析対象となる記事の正確なメタデータ（公開日、カテゴリ、文字数、可能であればアクセス数など）が必要です。これらのデータをどのように取得・管理するかは、これらのスニペットの範囲外です。
*   **非同期処理**: `link_checker`は`asyncio`を使用しているため、呼び出し側も非同期処理に対応する必要があります。
*   **カスタマイズ**: 特に`performance_analyzer`のスコアリングロジックや、`repost_scheduler`の更新タイプ判定ロジック、準備メモ生成ロジックは、ブログの特性や運用方針に合わせてカスタマイズすることが推奨されます。
