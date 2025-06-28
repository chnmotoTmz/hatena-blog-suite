# 🚀 Hatena Blog Suite - Minimal Edition

**軽量版: 必要最小限の機能で高速動作**

## 📦 最小構成

```
hatena-blog-suite-minimal/
├── core/hatena_client.py    # メインクライアント (50行)
├── mcp/simple-server.js     # MCPサーバー (60行) 
├── cli.py                   # CLIツール (30行)
├── requirements-minimal.txt # 最小依存関係 (3個)
└── package-minimal.json     # Node最小依存 (3個)
```

## ⚡ クイックスタート

### 1秒セットアップ
```bash
bash setup-minimal.sh
```

### 即座に実行
```bash
# 記事抽出
python cli.py --blog-id your_hatena_id

# MCPサーバー起動
npm start
```

## 🎯 機能（軽量版）

- ✅ **記事抽出**: はてなブログから記事一覧・内容取得
- ✅ **JSON出力**: 構造化データ保存
- ✅ **MCPサーバー**: Claude Desktop連携
- ✅ **高速処理**: 必要最小限のコード

## 📊 サイズ比較

| 版 | ファイル数 | 依存関係 | コード行数 |
|----|-----------|----------|----------|
| フル版 | 50+ | 15+ | 2000+ |
| **軽量版** | **5** | **6** | **140** |

## 🔧 Claude Desktop設定

```json
{
  "mcpServers": {
    "hatena-minimal": {
      "command": "node",
      "args": ["path/to/mcp/simple-server.js"]
    }
  }
}
```

## 💡 使用例

```bash
# 5記事抽出
python cli.py --blog-id motcho --count 5

# 結果確認
cat articles.json
```

---

**🎯 軽量・高速・シンプル！必要な機能だけでブログ管理**