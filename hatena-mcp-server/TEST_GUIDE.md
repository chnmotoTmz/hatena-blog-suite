# HATENA Agent v2 テストガイド

## 概要

このプロジェクトには3つのテストツールが含まれています：

1. **test_cli.py** - 自動テストスクリプト
2. **interactive_cli.py** - 対話型テストツール
3. **mock_server.py** - ローカルモックサーバー

## クイックスタート

### 1. 対話型テストツール（推奨）

最も簡単にテストを開始できます：

```bash
python interactive_cli.py
```

メニューから機能を選択してテストできます：
- 環境設定の確認
- 各機能の個別テスト
- 統合テスト

### 2. 自動テストスクリプト

全機能を一括でテストする場合：

```bash
# すべてのテストを実行
python test_cli.py

# 特定の機能のみテスト
python test_cli.py --test extract    # 記事抽出
python test_cli.py --test rag        # RAG機能
python test_cli.py --test image      # 画像生成
python test_cli.py --test affiliate  # アフィリエイト
python test_cli.py --test repost     # リポスト
```

### 3. モックサーバーでのテスト

実際のはてなブログにアクセスせずにテスト：

```bash
# ターミナル1: モックサーバーを起動
python src/utils/mock_server.py

# ターミナル2: テスト環境をセットアップ
python src/utils/mock_server.py --setup

# .env.test を使用してテスト
cp .env.test .env
python main.py --mode extract
```

## テストシナリオ

### シナリオ1: 環境設定の確認

```bash
python interactive_cli.py
# メニューから「1」を選択
```

必要な環境変数：
- `HATENA_BLOG_ID` - はてなブログID（必須）
- `BLOG_DOMAIN` - カスタムドメイン（オプション）
- `BING_AUTH_COOKIE` - 画像生成用（オプション）
- `RAKUTEN_AFFILIATE_TAG` - アフィリエイト用（オプション）

### シナリオ2: 基本機能のテスト

```bash
python test_cli.py
```

このコマンドで以下がテストされます：
1. モック記事の生成
2. RAG機能のシミュレーション
3. 画像生成のログ
4. アフィリエイトリンク処理
5. リポストスケジュール作成

### シナリオ3: 実際のブログでのテスト

環境変数を設定後：

```bash
# 記事の抽出のみ
python main.py --mode extract --hatena-id your-blog-id

# 全機能を実行
python main.py --mode full --hatena-id your-blog-id
```

## 出力ファイル

テスト実行後、以下のファイルが生成されます：

```
test_output/
├── mock_articles.json          # モック記事データ
├── enhanced_content.txt        # RAG処理後のコンテンツ
├── image_generation_log.json   # 画像生成ログ
├── affiliate_report.md         # アフィリエイトレポート
├── repost_calendar.json        # リポストスケジュール
└── integration_test_summary.json # 統合テストサマリー
```

## トラブルシューティング

### Bing画像生成が動作しない

1. Bing認証Cookieを取得：
   - https://www.bing.com/images/create にアクセス
   - F12で開発者ツールを開く
   - Application → Cookies → `_U` の値をコピー
   - `.env`の`BING_AUTH_COOKIE`に設定

### 記事抽出でエラーが出る

1. はてなブログIDが正しいか確認
2. カスタムドメインを使用している場合は`BLOG_DOMAIN`を設定
3. モックサーバーでまずテスト

### RAG機能が動作しない

- OpenAI APIキーは不要（無料版のため）
- ChromaDBの代わりに簡易検索を使用

## 開発者向け情報

### モックデータのカスタマイズ

`test_cli.py`の`create_mock_articles()`関数を編集：

```python
def create_mock_articles(num_articles=5):
    # カスタムデータを追加
    pass
```

### 新機能の追加

`interactive_cli.py`に新しいテストメソッドを追加：

```python
def test_new_feature(self):
    print("\n=== 新機能のテスト ===")
    # テストロジック
    pass
```

## 注意事項

- テストツールは本番環境では使用しないでください
- モックサーバーはローカル環境でのみ使用してください
- 実際のブログデータを扱う際は慎重に操作してください