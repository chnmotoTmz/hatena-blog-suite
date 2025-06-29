# HATENA Agent v2

はてなブログの記事管理・自動強化システム

## 新機能（v2.1）

### 🔗 リンク不正確チェック機能
- 既存リンクの有効性を自動検証
- リンク切れの自動検出・修正提案
- HTTPステータスチェック・リダイレクト対応
- 詳細なリンクレポート生成

### 🤖 アフィリエイト自動挿入機能（強化版）
- 記事内容から関連商品の自動検出
- 適切なアフィリエイトリンクの自動挿入
- Amazon・楽天等の主要ASP対応
- 商品情報の自動取得・整形
- パフォーマンス分析機能

### 🔄 参照記事機能強化
- 過去記事の関連性自動検出
- 自動クロスリファレンス生成
- 記事間の類似度計算
- 関連記事リンク自動挿入

### ✍️ 文言の個人化
- ユーザー固有の文体・トーン学習・適用
- パーソナライズされたコンテンツ生成
- 口調・表現パターンの一貫性確保
- 個性的な文章スタイルの維持

### 🕸️ ナレッジネットワーク化
- 記事間の連関性可視化システム
- Google NotebookLM連携でのデータベース化
- 知識グラフ構築・管理
- トピック間の関係性分析

## 既存機能

1. **自己記事抽出エージェント**
   - はてなブログから全記事を自動抽出
   - 記事のメタデータ（タイトル、URL、日付、カテゴリ）を収集
   - 記事本文、画像、リンクを解析

2. **リトリーブエージェント（RAG）**
   - 過去記事の関連リンクを自動挿入
   - 文体・口調の統一
   - ChromaDBを使用したベクトル検索

3. **画像生成エージェント**
   - Bing Image Creator（DALL-E 3）による記事に適した画像の自動生成
   - 既存画像の置き換え提案
   - アイキャッチ画像の作成
   - 無料のMicrosoft Copilotを使用（要認証cookie）

4. **アフィリエイト管理**
   - 楽天アフィリエイトリンク自動変換
   - 商品リンクの最適化
   - アフィリエイトレポート生成

5. **リポスト管理**
   - 記事のパフォーマンス分析
   - 再投稿スケジュールの自動生成
   - 更新内容の追加

## セットアップ

1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

2. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### Bing Image Creator Cookie の取得方法

1. Microsoftアカウントでhttps://www.bing.com/images/create にアクセス
2. 開発者ツール（F12）を開く
3. Application/Storage タブ → Cookies → https://www.bing.com
4. `_U` cookieの値をコピー
5. `.env`ファイルの`BING_AUTH_COOKIE`に設定

3. MeCab（日本語形態素解析）のインストール（アフィリエイト機能を使用する場合）
```bash
sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8
pip install mecab-python3
```

## 使用方法

### 基本的な使い方

```bash
# 全機能を実行
python main.py --hatena-id your-hatena-id

# 記事の抽出のみ
python main.py --hatena-id your-hatena-id --mode extract

# 記事の強化のみ（事前に抽出が必要）
python main.py --hatena-id your-hatena-id --mode enhance

# リポスト計画の作成のみ
python main.py --hatena-id your-hatena-id --mode repost

# 新機能の個別実行
python main.py --hatena-id your-hatena-id --mode linkcheck    # リンクチェック
python main.py --hatena-id your-hatena-id --mode personalize  # 個人化分析
python main.py --hatena-id your-hatena-id --mode network      # 知識ネットワーク構築
```

### 個別エージェントの使用

```python
from src.agents.article_extractor import HatenaArticleExtractor
from src.agents.retrieval_agent import RetrievalAgent

# 記事の抽出
extractor = HatenaArticleExtractor("your-hatena-id")
articles = extractor.extract_all_articles(max_pages=5)

# RAGエージェントの使用
retrieval_agent = RetrievalAgent(openai_api_key="your-key")
retrieval_agent.create_vectorstore_from_articles(articles)

# 関連記事リンクの挿入
enhanced_content = retrieval_agent.generate_article_with_links(
    "記事の内容",
    max_links=3
)
```

## 出力ファイル

### 基本出力
- `output/extracted_articles.json` - 抽出した記事データ
- `output/enhanced_sample.html` - 強化されたサンプル記事
- `output/repost_calendar.json` - リポストスケジュール
- `output/images/` - 生成された画像
- `output/chroma_db/` - ベクトルデータベース

### 新機能出力
- `output/link_check_report.md` - リンクチェック結果レポート
- `output/user_profile.json` - 個人化設定プロファイル
- `output/personalized_sample.html` - 個人化されたサンプル記事
- `output/knowledge_network/` - 知識ネットワークデータ
  - `knowledge_map.png` - 知識マップ可視化
  - `knowledge_graph.graphml` - グラフデータ（GraphML形式）
  - `notebook_lm_export.json` - NotebookLM用エクスポート
- `output/knowledge_network_report.md` - 知識ネットワーク分析レポート

## 注意事項

- **完全無料**: OpenAI APIは使用せず、すべて無料サービスで動作します
- Bing Image Creatorは無料ですが、認証cookieが必要です
- cookieは定期的に更新する必要があります（2-4週間ごと）
- はてなブログのスクレイピングは適度な間隔で行ってください
