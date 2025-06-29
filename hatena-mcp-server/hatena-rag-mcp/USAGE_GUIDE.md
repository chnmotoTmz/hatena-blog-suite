# Hatena RAG MCP Server 使用ガイド

## セットアップ手順

### 1. 環境構築

```bash
cd /home/moto/hatena-agent-v2/hatena-rag-mcp
npm install
npm run build
```

### 2. 環境変数設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して必要な設定を入力：

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=./data/articles.db
DEFAULT_BLOG_ID=your_hatena_id
DEFAULT_BLOG_DOMAIN=your_hatena_id.hatenablog.com
```

### 3. VS Code MCP統合

VS Codeの`settings.json`に以下を追加：

```json
{
  "mcp.servers": {
    "hatena-rag": {
      "command": "node",
      "args": ["/home/moto/hatena-agent-v2/hatena-rag-mcp/dist/index.js"],
      "env": {
        "OPENAI_API_KEY": "your_key_here",
        "DATABASE_PATH": "./data/articles.db"
      }
    }
  }
}
```

## 利用例

### 1. はてなブログから記事を抽出

```javascript
// 基本的な抽出（最初の5ページ）
await extract_hatena_articles({
  blog_id: "your_hatena_id",
  max_pages: 5,
  extract_full_content: true
});

// カスタムドメインの場合
await extract_hatena_articles({
  blog_id: "your_hatena_id", 
  blog_domain: "example.hatenablog.jp",
  max_pages: 10
});
```

### 2. 記事検索

```javascript
// キーワード検索
await search_article_content({
  query: "React TypeScript フロントエンド",
  limit: 10
});

// タグとキーワードで絞り込み
await search_article_content({
  query: "機械学習",
  tags: ["AI", "Python"],
  date_from: "2023-01-01",
  date_to: "2023-12-31",
  limit: 5
});
```

### 3. 関連記事検索（RAG）

```javascript
// セマンティック検索
await retrieve_related_articles({
  query: "React Hooksを使った状態管理の最適化について教えて",
  similarity_threshold: 0.8,
  max_results: 3
});
```

### 4. 記事要約生成

```javascript
// 複数記事の簡潔な要約
await generate_article_summary({
  article_ids: ["article1", "article2", "article3"],
  summary_type: "brief"
});

// 詳細な要約
await generate_article_summary({
  article_ids: ["article1", "article2"],
  summary_type: "detailed"
});
```

### 5. データエクスポート

```javascript
// CSV形式でエクスポート
await export_articles_csv({
  output_path: "./exports/articles.csv",
  fields: ["title", "url", "date", "categories", "wordCount"],
  filter_conditions: {
    tags: ["技術"],
    date_from: "2023-01-01"
  }
});

// ナレッジベース形式でエクスポート
await export_knowledge_base({
  output_path: "./exports/knowledge_base.json",
  format: "json",
  chunking_strategy: "paragraph"
});
```

## 活用シナリオ

### 個人ナレッジ管理

1. **記事の一括抽出**: 過去のブログ記事をすべて抽出してローカルに保存
2. **関連記事の発見**: 新しい記事を書く際に関連する過去記事を自動発見
3. **知識の整理**: カテゴリやタグで記事を体系的に整理

### 技術ブログの活用

1. **コード例の再利用**: 過去の技術記事からコードスニペットを検索
2. **技術トレンドの分析**: 記事の傾向から技術的興味の変遷を分析
3. **関連技術の探索**: 特定技術に関連する記事群を発見

### AI支援執筆

1. **執筆支援**: 新記事執筆時に関連する過去記事を参照
2. **一貫性確保**: 過去の記述と矛盾しない内容で執筆
3. **内部リンク提案**: 関連記事への自然なリンク挿入の提案

## トラブルシューティング

### よくある問題

#### 1. 記事抽出が失敗する

- **原因**: ネットワーク接続やはてなブログの構造変更
- **対処**: `REQUEST_DELAY_MS`を増やしてリトライ

#### 2. RAG検索で結果が出ない

- **原因**: OpenAI API設定やembedding生成の問題
- **対処**: API キーを確認し、フォールバックのキーワード検索を利用

#### 3. データベースエラー

- **原因**: SQLiteファイルのアクセス権限
- **対処**: `data/`ディレクトリの書き込み権限を確認

### ログ確認

```bash
# サーバーログを確認
node dist/index.js 2>&1 | tee server.log

# デバッグモードで実行
DEBUG=1 node dist/index.js
```

## パフォーマンス最適化

### 推奨設定

```env
REQUEST_DELAY_MS=1000  # レート制限対策
MAX_CONCURRENT_REQUESTS=3  # 同時接続数制限
DATABASE_PATH=./data/articles.db  # SSD上に配置
```

### 大量データ処理

- 記事数が1000件を超える場合は分割処理を推奨
- `max_pages`を設定して段階的に抽出
- 定期的なデータベースメンテナンス（VACUUM）

## セキュリティ考慮事項

1. **API キー管理**: `.env`ファイルはgit管理から除外
2. **アクセス制限**: 公開サーバーでの実行時はファイアウォール設定
3. **データ保護**: 機密情報を含む記事の取り扱いに注意

## 今後の拡張予定

- [ ] 画像抽出・解析機能
- [ ] 他のブログプラットフォーム対応
- [ ] より高度な自然言語処理
- [ ] ビジュアル化ダッシュボード
- [ ] バックアップ・同期機能