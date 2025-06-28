# 🤖 Gemini API設定ガイド

## Claude Desktop設定（Gemini版）

### 1. Gemini API キーの取得
1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. 新しいAPIキーを作成
3. キーをコピーして保存

### 2. Claude Desktop設定

**設定ファイルパス**: 
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**設定内容**:
```json
{
  "mcpServers": {
    "hatena-blog-suite": {
      "command": "node",
      "args": ["C:/Users/motoc/hatena-blog-suite/mcp/hatena-rag-mcp/dist/index.js"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "GEMINI_MODEL": "gemini-1.5-pro",
        "HATENA_BLOG_ID": "your_hatena_id",
        "DATABASE_PATH": "./data/articles.db"
      }
    }
  }
}
```

### 3. 環境設定

**`.env`ファイル作成**:
```bash
cd mcp/hatena-rag-mcp
cp .env.example .env
```

**`.env`編集**:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-1.5-pro
DEFAULT_BLOG_ID=your_hatena_id
DEFAULT_BLOG_DOMAIN=your_hatena_id.hatenablog.com
```

### 4. セットアップ

```bash
# 依存関係インストール
npm install @google/generative-ai

# または、Gemini版package.jsonを使用
cp package-gemini.json package.json
npm install

# ビルド
npm run build
```

### 5. 動作確認

```bash
# MCPサーバー単体テスト
npm start

# Claude Desktopから確認
# チャットで「記事を抽出してください」など
```

## 📊 Gemini vs OpenAI 比較

| 機能 | Gemini | OpenAI |
|------|---------|--------|
| テキスト生成 | ✅ gemini-1.5-pro | ✅ gpt-4 |
| 埋め込み | ⚠️ 限定的サポート | ✅ text-embedding-ada-002 |
| 料金 | 🆓 無料枠あり | 💰 従量課金 |
| 日本語 | ✅ 優秀 | ✅ 優秀 |
| API制限 | 緩い | 厳しい |

## 🔧 トラブルシューティング

### API キーエラー
```
Error: Gemini API error: API_KEY_INVALID
```
**解決策**: 
1. APIキーが正しく設定されているか確認
2. Google AI Studioでキーが有効か確認

### 埋め込み機能エラー
```
Warning: Gemini embedding not available
```
**解決策**: 
- 自動的にテキスト類似度フォールバックが動作
- 機能に問題なし

### Claude Desktop認識エラー
```
MCP server not found
```
**解決策**:
1. Claude Desktop再起動
2. 設定ファイルのパス確認
3. Node.jsバージョン確認 (v18以上推奨)

## 🎯 推奨設定

**高速処理用**:
```json
"GEMINI_MODEL": "gemini-1.5-flash"
```

**高品質処理用**:
```json
"GEMINI_MODEL": "gemini-1.5-pro"
```

**コスト重視**:
```json
"GEMINI_MODEL": "gemini-1.0-pro"
```

---

✅ **設定完了後、Claude Desktopを再起動してMCPサーバーを有効化してください！**