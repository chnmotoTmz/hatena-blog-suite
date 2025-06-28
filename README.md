# 🚀 Hatena Blog Suite - 統合はてなブログ管理・自動化スイート

> **3つのリポジトリを統合した包括的なはてなブログ管理システム**

[![GitHub](https://img.shields.io/badge/GitHub-Suite-blue)](https://github.com/chnmotoTmz/hatena-blog-suite)
[![Docker](https://img.shields.io/badge/Docker-Ready-green)](./docker-compose.yml)
[![MCP](https://img.shields.io/badge/MCP-Server-orange)](./mcp/)

## 📦 統合された機能

### 🔄 **自動化エージェント** (from hatena-agent)
- はてなブログ記事の自動管理・更新
- MCP（Model Context Protocol）サーバー
- Docker対応の完全な開発環境
- リアルタイム記事監視・最適化

### 🎨 **画像生成・管理** (from hatenablog)  
- DALL-E 3による自動画像生成
- アイキャッチ画像の最適化
- 画像メタデータ管理
- Bing Image Creator連携

### ⚡ **最適化・分析** (from hatenablog-optimizer)
- 高度なCLIインターフェース
- はてなブログAPI最適化
- パフォーマンス分析・レポート
- SEO最適化機能

## 🎯 主要機能

### 🤖 **自動化・AI機能**
- **記事抽出エージェント**: はてなブログから全記事を自動収集
- **RAGエージェント**: 過去記事の関連リンク自動挿入
- **リンクチェック**: 不正確リンクの自動検出・修正
- **アフィリエイト管理**: Amazon・楽天リンクの自動最適化
- **文体パーソナライズ**: 個人の文体学習・適用

### 🔗 **統合システム**
- **MCP Server**: Claude Desktop連携
- **ナレッジネットワーク**: 記事間関係性の可視化
- **Google NotebookLM**: 知識グラフのエクスポート
- **Docker環境**: ワンクリックデプロイ

### 🎨 **コンテンツ生成**
- **画像自動生成**: Bing Image Creator (DALL-E 3)
- **アイキャッチ最適化**: 記事に応じた画像選択
- **テンプレート管理**: 再利用可能なコンテンツパーツ

## 📁 プロジェクト構造

```
hatena-blog-suite/
├── 📂 core/                    # 基本機能
│   ├── hatena_client.py        # はてなAPI クライアント
│   ├── data_store.py           # データ管理
│   └── utils.py                # 共通ユーティリティ
│
├── 📂 automation/              # 自動化機能
│   ├── hatena_agent.py         # メイン自動化エージェント
│   ├── article_updater.py      # 記事更新システム
│   └── api_utils.py            # API処理ユーティリティ
│
├── 📂 image/                   # 画像関連
│   ├── image_generator.py      # 画像生成エンジン
│   └── image_creator.py        # 画像作成ツール
│
├── 📂 optimization/            # 最適化機能
│   ├── cli_test.py             # CLI テストスイート
│   └── main.py                 # 最適化メインモジュール
│
├── 📂 mcp/                     # MCP サーバー
│   ├── hatena-mcp-server/      # メインMCP実装
│   └── hatena-rag-mcp/         # RAG機能MCP
│
├── 📂 frontend/                # Webインターフェース
├── 📂 backend/                 # バックエンドAPI
├── 📂 config/                  # 設定管理
├── 📂 tests/                   # テストスイート
└── 📂 docs/                    # ドキュメント
```

## 🚀 クイックスタート

### Option A: Docker で起動（推奨）
```bash
# リポジトリをクローン
git clone https://github.com/chnmotoTmz/hatena-blog-suite.git
cd hatena-blog-suite

# 環境変数を設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# Docker Compose で全システムを起動
docker-compose up -d
```

### Option B: ローカル環境で起動
```bash
# 依存関係をインストール
pip install -r requirements.txt

# MCPサーバーを起動（バックグラウンド）
cd mcp/hatena-mcp-server
python app.py &

# メインシステムを起動
python main.py --hatena-id your-id
```

## 🔧 設定

### 必要なAPIキー・認証
```bash
# .envファイルに設定
HATENA_ID=your-hatena-id
HATENA_API_KEY=your-api-key
BLOG_DOMAIN=your-blog.hatenablog.com

# Bing Image Creator (無料)
BING_AUTH_COOKIE=your-bing-cookie

# アフィリエイト（オプション）
RAKUTEN_APP_ID=your-rakuten-id
AMAZON_ASSOCIATE_ID=your-amazon-id
```

### MCP Server 設定
Claude Desktopと連携する場合：
```json
{
  "mcpServers": {
    "hatena-blog-suite": {
      "command": "python",
      "args": ["path/to/hatena-blog-suite/mcp/hatena-mcp-server/app.py"],
      "env": {
        "HATENA_ID": "your-id"
      }
    }
  }
}
```

## 📖 使用方法

### CLIコマンド
```bash
# 全機能実行
python main.py --hatena-id your-id

# 記事抽出のみ
python main.py --mode extract --hatena-id your-id

# 画像生成のみ  
python main.py --mode image --hatena-id your-id

# リンクチェック
python main.py --mode linkcheck --hatena-id your-id

# 最適化分析
python optimization/main.py --analyze
```

### MCPサーバー経由（Claude Desktop）
```
# Claude Desktop チャットで
記事を抽出してください
画像を生成してください
リンクをチェックしてください
```

### Web インターフェース
```bash
# フロントエンド起動（Port 3000）
cd frontend && npm start

# バックエンドAPI（Port 8000）
cd backend && uvicorn main:app --reload
```

## 📊 出力・レポート

### 📁 `output/` ディレクトリ
- `📄 extracted_articles.json` - 抽出記事データ
- `🖼️ images/` - 生成画像保存場所
- `📈 link_check_report.md` - リンクチェック結果  
- `🧠 knowledge_network/` - ナレッジマップ
- `📋 repost_calendar.json` - リポストスケジュール

### 📈 分析レポート
- パフォーマンス分析
- SEO最適化提案
- アフィリエイト収益レポート
- 記事間関連性マップ

## 🛠️ 開発・貢献

### 開発環境セットアップ
```bash
# 開発用の追加依存関係
pip install -r requirements-dev.txt

# テスト実行
pytest tests/

# コード品質チェック
flake8 --config .flake8
black --check .
```

### 貢献ガイドライン
1. Issueで改善提案・バグ報告
2. Feature branchでの開発
3. Pull Request作成
4. コードレビュー・マージ

## 📋 移行元リポジトリ

| 元リポジトリ | 主要機能 | Status |
|-------------|---------|--------|
| [hatena-agent](https://github.com/chnmotoTmz/hatena-agent) | 自動化・MCP | 🔄 Archived |
| [hatenablog](https://github.com/chnmotoTmz/hatenablog) | 画像生成 | 🔄 Archived |  
| [hatenablog-optimizer](https://github.com/chnmotoTmz/hatenablog-optimizer) | 最適化 | 🔄 Archived |

## 📞 サポート

- 🐛 **バグレポート**: [Issues](https://github.com/chnmotoTmz/hatena-blog-suite/issues)
- 💡 **機能リクエスト**: [Discussions](https://github.com/chnmotoTmz/hatena-blog-suite/discussions)
- 📚 **ドキュメント**: [Wiki](https://github.com/chnmotoTmz/hatena-blog-suite/wiki)

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

---

## 🎉 Changelog

### v1.0.0 (2025-06-28) - 統合リリース
- ✨ 3つのリポジトリを統合
- 🚀 Docker完全対応
- 🔗 MCP Server実装
- 🎨 画像生成機能統合
- ⚡ CLI最適化機能統合

---

**🚀 統合されたパワーで、はてなブログをレベルアップしましょう！**