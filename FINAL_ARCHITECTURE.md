# 🏗️ Hatena Blog Suite - 最終アーキテクチャ

## 📐 システム構成図

```
┌─────────────────────────────────────────────────────┐
│                   Claude Desktop                     │
│                  (MCP Client)                       │
└────────────────────┬───────────────────────────────┘
                     │ MCP Protocol
┌────────────────────▼───────────────────────────────┐
│              MCP Server Layer                       │
│         mcp/simple-mcp-server.js                   │
│  ┌──────────┬──────────┬──────────┬──────────┐   │
│  │ extract  │ analyze  │  search  │   test   │   │
│  │ articles │ perform. │ articles │ connect. │   │
│  └──────────┴──────────┴──────────┴──────────┘   │
└────────────────────┬───────────────────────────────┘
                     │ Python Bridge
┌────────────────────▼───────────────────────────────┐
│              Python Core Engine                     │
│           core/hatena_all.py                       │
│  ┌────────────────────────────────────────────┐   │
│  │        HatenaAllInOne Class                │   │
│  │  ├─ Article Extraction                     │   │
│  │  ├─ Content Analysis                       │   │
│  │  ├─ Search & Retrieval                     │   │
│  │  └─ Performance Optimization               │   │
│  └────────────────────────────────────────────┘   │
└────────────────────┬───────────────────────────────┘
                     │ API Calls
┌────────────────────▼───────────────────────────────┐
│              External Services                      │
│  ┌──────────────┬─────────────┬──────────────┐   │
│  │ Hatena Blog  │  OpenAI API │  Gemini API  │   │
│  │     API      │  (Optional) │  (Optional)  │   │
│  └──────────────┴─────────────┴──────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 🗂️ ディレクトリ構造

```
hatena-blog-suite/
├── core/                      # Pythonコアエンジン
│   └── hatena_all.py         # 統合型実装（200行）
│
├── mcp/                       # MCPサーバー層
│   └── simple-mcp-server.js  # MCPサーバー実装
│
├── test_output/              # テスト結果・実データ
│   └── extracted_articles.json
│
├── output/                   # 分析結果
│   └── performance_analysis.json
│
├── node_modules/             # Node.js依存関係
├── package.json              # Node.js設定
├── package-lock.json         # 依存関係ロック
│
├── requirements-optimized.txt # Python依存関係（最小）
├── quick_test.py             # テストスイート
│
├── PROJECT_SUMMARY.md        # プロジェクト成果
├── QUICK_START.md           # クイックスタート
└── FINAL_ARCHITECTURE.md    # このファイル
```

## 🔧 技術スタック

### Backend
- **言語**: Python 3.9+
- **主要ライブラリ**:
  - `requests`: HTTP通信
  - `beautifulsoup4`: HTML解析
  - `python-dotenv`: 環境変数管理

### MCP Server
- **言語**: Node.js 18+
- **主要ライブラリ**:
  - `@modelcontextprotocol/sdk`: MCP SDK
  - `dotenv`: 環境変数
  - `child_process`: Python連携

### 統合レイヤー
- **プロトコル**: JSON-RPC over stdio
- **データ形式**: JSON
- **エンコーディング**: UTF-8

## 🌐 API設計

### MCP Tools

#### 1. extract_articles
```typescript
{
  name: "extract_articles",
  description: "はてなブログから記事を抽出",
  parameters: {
    limit?: number,      // 取得件数
    category?: string,   // カテゴリー
    tag?: string        // タグ
  }
}
```

#### 2. analyze_performance
```typescript
{
  name: "analyze_performance",
  description: "記事のパフォーマンス分析",
  parameters: {
    article_id?: string, // 記事ID
    metrics?: string[]   // 分析指標
  }
}
```

#### 3. search_articles
```typescript
{
  name: "search_articles",
  description: "記事を検索",
  parameters: {
    query: string,       // 検索クエリ
    type?: string       // 検索タイプ
  }
}
```

#### 4. test_connection
```typescript
{
  name: "test_connection",
  description: "接続テスト",
  parameters: {}
}
```

## 💾 データフロー

```
1. Claude Desktop → MCP Server
   - Tool呼び出し（JSON-RPC）
   
2. MCP Server → Python Core
   - subprocess経由でPythonスクリプト実行
   - 引数としてパラメータ渡し
   
3. Python Core → Hatena API
   - REST API呼び出し
   - XML/JSONレスポンス処理
   
4. Python Core → MCP Server
   - 処理結果をJSON出力
   
5. MCP Server → Claude Desktop
   - Tool実行結果返却
```

## 🔐 セキュリティ設計

### 環境変数管理
- `.env`ファイルでAPIキー管理
- 環境変数経由でアクセス
- `.gitignore`で除外

### API認証
- Basic認証（Hatena API）
- Bearer Token（OpenAI/Gemini）

### エラーハンドリング
- 全APIコールでtry-catch
- 適切なエラーメッセージ
- フォールバック処理

## 🚀 パフォーマンス最適化

### コード最適化
- 単一ファイル化で起動時間短縮
- 必要最小限のインポート
- 効率的なデータ構造

### キャッシング
- APIレスポンスのメモリキャッシュ
- 重複リクエストの削減

### 並列処理
- 非同期処理は必要最小限
- バッチ処理の最適化

## 📊 メトリクス

### サイズ
- Python: 200行
- JavaScript: 280行
- 総計: 480行（コアのみ）

### パフォーマンス
- 起動時間: 0.5秒
- API応答: 1-2秒
- メモリ使用: 30MB

### 依存関係
- Python: 3パッケージ
- Node.js: 3パッケージ

## 🔄 拡張ポイント

### 新機能追加
1. `core/hatena_all.py`の`HatenaAllInOne`クラスにメソッド追加
2. `mcp/simple-mcp-server.js`にツール定義追加
3. 必要に応じてテスト追加

### 他プラットフォーム対応
- 基本設計を流用可能
- APIクライアントの差し替えのみ

### UI追加
- Web UIやCLIツールを別レイヤーとして追加可能

---
*アーキテクチャバージョン: 1.0.0*
*最終更新: 2025-06-29*