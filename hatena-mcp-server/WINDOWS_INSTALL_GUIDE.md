# 🪟 Windows インストールガイド

## 🚀 クイックスタート（5分）

### 前提条件
- Windows 10/11
- Python 3.9 以上
- インターネット接続

### 自動セットアップ
1. **ファイルをダウンロード/コピー**
   ```
   multi_blog_manager.py
   enhanced_hatena_agent.py
   test_multi_blog.py
   simple_test.py
   requirements-windows.txt
   .env.template
   windows_setup.bat
   ```

2. **自動セットアップ実行**
   - `windows_setup.bat` をダブルクリック
   - 指示に従って進行

3. **APIキー設定**
   - `.env` ファイルを編集
   - はてなブログからAPIキーを取得・設定

### 手動セットアップ
```cmd
# 1. 依存関係インストール
pip install -r requirements-windows.txt

# 2. 環境設定
copy .env.template .env
notepad .env

# 3. テスト実行
python simple_test.py
```

## 📝 設定ファイル編集

### .env ファイル設定
```env
# 必須: はてなブログAPIキー
HATENA_BLOG_ATOMPUB_KEY_1=あなたのAPIキー1
HATENA_BLOG_ATOMPUB_KEY_2=あなたのAPIキー2

# オプション: レガシー互換性
HATENA_ID=あなたのはてなID
BLOG_DOMAIN=あなたのブログドメイン.hatenadiary.jp
```

### APIキー取得方法
1. はてなブログにログイン
2. 設定 → 詳細設定 → AtomPub
3. APIキーをコピー
4. `.env`ファイルに貼り付け

## 🧪 テスト手順

### 基本テスト
```cmd
python simple_test.py
```
**期待結果**: ブログ設定の確認

### 認証テスト
```cmd
python test_multi_blog.py
```
**期待結果**: 認証成功とブログ一覧表示

### API機能テスト
```cmd
python -c "from enhanced_hatena_agent import EnhancedHatenaAgent; agent = EnhancedHatenaAgent(); print(agent.list_blogs())"
```
**期待結果**: 設定済みブログのJSON表示

## 🎯 基本操作

### ブログ一覧確認
```python
from enhanced_hatena_agent import EnhancedHatenaAgent
agent = EnhancedHatenaAgent()
blogs = agent.list_blogs()
print(blogs)
```

### 記事取得
```python
articles = agent.get_articles('lifehack_blog', limit=5)
print(f"取得記事数: {len(articles['articles'])}")
```

### 記事検索
```python
results = agent.search_articles_by_title('lifehack_blog', '登山')
print(f"検索結果: {len(results['articles'])}件")
```

### 記事移行
```python
result = agent.migrate_article(
    source_blog='lifehack_blog',
    target_blog='mountain_blog',
    article_id='記事ID',
    copy_mode=True  # 安全なコピーモード
)
print(result)
```

## 🔧 トラブルシューティング

### Python未インストール
**症状**: 'python' は、内部コマンドまたは外部コマンドとして認識されていません
**解決**: https://python.org からPython 3.9+をインストール

### パッケージインストールエラー
**症状**: pip install 失敗
**解決**: 
```cmd
pip install --user requests python-dotenv
```

### 権限エラー
**症状**: アクセスが拒否されました
**解決**: 管理者として実行

### 文字化け
**症状**: 日本語が表示されない
**解決**: コマンドプロンプトのエンコードをUTF-8に設定
```cmd
chcp 65001
```

### 認証エラー（401/404）
**症状**: Authentication failed
**解決**: 
1. `.env`ファイルのAPIキー確認
2. はてなブログでAPIキーを再発行
3. ブログドメイン名の確認

## 📊 システム要件

### 最小要件
- Python 3.9+
- RAM: 100MB
- ディスク: 50MB
- ネットワーク: HTTPS接続

### 推奨環境
- Python 3.11+
- RAM: 500MB
- ディスク: 200MB
- SSD推奨

## 🎉 インストール完了確認

インストールが成功すると以下が表示されます：
```
🎌 Hatena Multi-Blog System - Simple Test
==================================================
📚 Configured Blogs:
  • lifehack_blog: ライフハックブログ
  • mountain_blog: 登山ブログ  
  • tech_blog: 技術ブログ

✅ Found 3 configured blogs
🔐 Testing Authentication...
✅ All authentication tests passed
```

---
**サポート**: 問題が発生した場合は設定ファイルとエラーメッセージを確認してください