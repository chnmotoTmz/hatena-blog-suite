# 📦 Windows移行パッケージ - 緊急展開用

## 🚨 緊急時5分セットアップ

### 📁 移行必須ファイル（4ファイル）
```
multi_blog_manager.py      ← コア機能（327行）
enhanced_hatena_agent.py   ← メインAPI（243行）  
.env                       ← 設定ファイル
simple_test.py            ← 動作確認用（62行）
```

### ⚡ 即座実行コマンド
```bash
# 1. Windowsターミナルで実行
cd C:\Users\motoc\hatena-agent\hatena-mcp-server-clean

# 2. 依存関係インストール（2分）
pip install requests python-dotenv

# 3. 動作確認（30秒）
python simple_test.py

# 4. 認証テスト（1分）
python -c "from enhanced_hatena_agent import EnhancedHatenaAgent; agent = EnhancedHatenaAgent(); print(agent.test_blog_authentication())"

# 5. ライフハック→登山移行開始（即座）
python enhanced_hatena_agent.py
```

## 🎯 最小限requirements.txt
```
requests>=2.31.0
python-dotenv>=1.0.0
```

## 🔧 環境変数設定（.env）
```env
# 認証情報（実際の値に置換）
HATENA_BLOG_ATOMPUB_KEY_1=あなたのAPIキー1
HATENA_BLOG_ATOMPUB_KEY_2=あなたのAPIキー2

# レガシー互換性
HATENA_ID=motochan1969
BLOG_DOMAIN=arafo40tozan.hatenadiary.jp
```

## 🚀 即座使用可能なAPI
```python
from enhanced_hatena_agent import EnhancedHatenaAgent

# エージェント初期化
agent = EnhancedHatenaAgent()

# ブログ一覧確認
blogs = agent.list_blogs()

# ライフハックブログの記事取得
articles = agent.get_articles('lifehack_blog', limit=10)

# 登山関連記事検索
mountain_articles = agent.search_articles_by_title('lifehack_blog', '登山')

# 記事移行（安全なコピーモード）
result = agent.migrate_article(
    source_blog='lifehack_blog',
    target_blog='mountain_blog', 
    article_id='記事ID',
    copy_mode=True
)
```

## 🔍 トラブルシューティング（事前対処）

### Python未インストール
```bash
# Python 3.9+ 確認
python --version

# 未インストールの場合
# https://python.org からインストール
```

### パッケージインストールエラー
```bash
# 管理者権限で実行
pip install --user requests python-dotenv

# または仮想環境作成
python -m venv hatena_env
hatena_env\Scripts\activate
pip install requests python-dotenv
```

### 文字エンコードエラー
```python
# ファイル先頭に追加
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 認証エラー（401/404）
```python
# APIキー確認スクリプト
import os
print("API Key 1:", os.getenv('HATENA_BLOG_ATOMPUB_KEY_1'))
print("API Key 2:", os.getenv('HATENA_BLOG_ATOMPUB_KEY_2'))

# はてなブログ設定 → AtomPub → APIキーをコピー
```

## 📋 移行チェックリスト

### ✅ 事前準備
- [ ] Python 3.9+ インストール確認
- [ ] はてなブログAPIキー取得
- [ ] Windows環境でのファイルアクセス確認

### ✅ ファイル移行
- [ ] multi_blog_manager.py コピー
- [ ] enhanced_hatena_agent.py コピー  
- [ ] .env作成・設定
- [ ] simple_test.py コピー

### ✅ 動作確認
- [ ] `python simple_test.py` 実行
- [ ] 認証テスト成功
- [ ] ブログ一覧取得成功
- [ ] 記事取得テスト成功

### ✅ 本格運用
- [ ] 登山関連記事検索
- [ ] テスト移行（1-2記事）
- [ ] 移行結果確認
- [ ] バッチ移行実行

## 🎯 成功パターン
```
1. 5分セットアップ完了
2. 認証成功確認
3. ライフハックブログから登山記事検索
4. 安全なコピーモードで移行テスト
5. 確認後、バッチ移行実行
```

## 🔄 Docker化は後日検討
現在のシンプル実装で動作確認後、必要に応じて：
- 監視機能追加
- ログ集約
- スケーラビリティ対応
- セキュリティ強化

---
**優先度**: 直接移行 → 動作確認 → 記事移行 → Docker化検討