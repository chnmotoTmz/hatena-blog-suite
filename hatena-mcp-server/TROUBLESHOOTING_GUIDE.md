# 🆘 立ち上げトラブルシューティングガイド

## 🚨 現在の問題分析

### 認証エラーの詳細
```
❌ lifehack_blog: 404 Client Error (Not Found)
URL: https://blog.hatena.ne.jp/motochan1969/motochan1969.hatenadiary.jp/atom

❌ mountain_blog: 401 Client Error (Unauthorized)  
URL: https://blog.hatena.ne.jp/motochan1969/arafo40tozan.hatenadiary.jp/atom
```

## 🔍 問題の原因

### 1. 404 Error (Not Found)
**原因**: ブログドメインが存在しない
- `motochan1969.hatenadiary.jp` が存在しない可能性
- ドメイン名が間違っている可能性

### 2. 401 Error (Unauthorized)
**原因**: 認証情報が無効
- APIキーが間違っている
- APIキーが期限切れ
- WSSE認証ヘッダーの問題

## 🛠️ 修正手順

### STEP 1: 実際のブログドメイン確認
```bash
# 1. はてなブログにログイン
# 2. 設定 → 詳細設定 → AtomPub
# 3. 「ルートエンドポイント」を確認
```

### STEP 2: APIキー再取得
```bash
# 1. はてなブログ → 設定 → 詳細設定 → AtomPub
# 2. 「APIキー」を確認/再生成
# 3. .envファイルに正確にコピー
```

### STEP 3: 設定ファイル修正
現在の`.env`ファイルを実際の値に更新：

```env
# 実際のブログ情報に修正が必要
HATENA_BLOG_ATOMPUB_KEY_1=実際のAPIキー1
HATENA_BLOG_ATOMPUB_KEY_2=実際のAPIキー2

# レガシー互換性
HATENA_ID=実際のはてなID
BLOG_DOMAIN=実際のブログドメイン
```

## 🧪 段階的テスト手順

### Phase 1: ブログ存在確認
```bash
# ブラウザで以下URLにアクセスして確認
https://motochan1969.hatenadiary.jp/
https://arafo40tozan.hatenadiary.jp/
```

### Phase 2: API接続テスト
```python
import requests

# 基本的なHTTP接続テスト
test_urls = [
    "https://motochan1969.hatenadiary.jp/",
    "https://arafo40tozan.hatenadiary.jp/"
]

for url in test_urls:
    try:
        response = requests.get(url, timeout=10)
        print(f"{url}: {response.status_code}")
    except Exception as e:
        print(f"{url}: ERROR - {e}")
```

### Phase 3: 手動設定版作成
```python
# manual_test.py - 手動設定版
from multi_blog_manager import MultiBlogManager
import os

# 手動でAPIキーを設定
os.environ["HATENA_BLOG_ATOMPUB_KEY_1"] = "あなたの実際のAPIキー"
os.environ["HATENA_BLOG_ATOMPUB_KEY_2"] = "あなたの実際のAPIキー"

# 実際のブログドメインでテスト
manager = MultiBlogManager()
blogs = manager.list_blogs()
print("設定されたブログ:", blogs)
```

## 🔧 即座修正版の作成

実際の設定情報が必要です。以下を教えてください：

1. **はてなID**: 
2. **実際のブログドメイン**: 
   - ライフハックブログ: `??.hatenablog.com` or `??.hatenadiary.jp`
   - 登山ブログ: `??.hatenablog.com` or `??.hatenadiary.jp`
3. **APIキー**: はてなブログ設定から取得

## 🚀 クイック修正スクリプト

```python
# quick_fix.py
import os

# 実際の情報を入力してください
ACTUAL_HATENA_ID = "your_actual_hatena_id"
ACTUAL_LIFEHACK_DOMAIN = "your_actual_lifehack_domain.hatenablog.com"
ACTUAL_MOUNTAIN_DOMAIN = "your_actual_mountain_domain.hatenablog.com"
ACTUAL_API_KEY_1 = "your_actual_api_key_1"
ACTUAL_API_KEY_2 = "your_actual_api_key_2"

# 環境変数設定
os.environ["HATENA_BLOG_ATOMPUB_KEY_1"] = ACTUAL_API_KEY_1
os.environ["HATENA_BLOG_ATOMPUB_KEY_2"] = ACTUAL_API_KEY_2

# テスト実行
from enhanced_hatena_agent import EnhancedHatenaAgent
agent = EnhancedHatenaAgent()
result = agent.test_blog_authentication()
print("認証テスト結果:", result)
```

## 📞 次のアクション

1. **実際の設定情報を確認**
   - はてなブログの設定画面から正確な情報を取得
   
2. **設定ファイル修正**
   - `.env`ファイルを実際の値に更新
   
3. **段階的テスト**
   - まず1つのブログで認証テスト
   - 成功したら他のブログも設定

**どの手順で具体的に問題が発生していますか？実際のブログドメインとAPIキーの情報を確認していただけますか？**