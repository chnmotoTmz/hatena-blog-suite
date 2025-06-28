# 🧪 Hatena Blog Suite - テストガイド

## 🚀 クイックテスト (30秒)

### 1. 一発テスト
```bash
# 全て自動でテスト
bash run_tests.sh
```

### 2. Pythonのみテスト
```bash
python quick_test.py
```

### 3. MCPサーバーのみテスト
```bash
node test_mcp_server.js
```

## 📝 テスト項目

### 🔍 基本機能テスト
- ✅ **モジュールインポート**: 必要ライブラリの読み込み
- ✅ **初期化**: HatenaUnifiedクラスのインスタンス作成
- ✅ **設定**: 設定ファイルの読み込み

### 📊 データ処理テスト
- ✅ **記事解析**: サンプルデータの解析
- ✅ **パフォーマンス分析**: SEOスコア算出
- ✅ **リポスト計画**: スケジュール生成
- ✅ **ナレッジグラフ**: キーワード解析

### 📡 MCPサーバーテスト
- ✅ **ツール登録**: 8つのツールが正しく登録されているか
- ✅ **記事抽出**: extract_articlesツール
- ✅ **記事拡張**: enhance_articlesツール
- ✅ **分析機能**: analyze_performanceツール
- ✅ **キャッシュ**: 結果キャッシュ機能

### 📁 ファイル操作テスト
- ✅ **JSON出力**: データのJSON保存
- ✅ **ディレクトリ作成**: 出力フォルダ作成
- ✅ **ファイル確認**: 作成されたファイルの確認

## 🔍 詳細テスト

### フルテストスイート実行
```bash
# 全てのテストを実行
bash run_tests.sh --full

# Pythonユニットテストのみ
python test_suite.py
```

### 手動テスト
```bash
# 基本機能テスト
python -c "from core.hatena_all import HatenaUnified; print('Import OK')"

# MCPサーバー起動テスト
node -e "require('./mcp/unified-server.js'); console.log('MCP OK')"
```

## 📊 テスト結果の見方

### ✅ 成功ケース
```
🎉 All tests PASSED!
🚀 System is ready to use.

Quick start:
  python core/hatena_all.py --blog-id YOUR_BLOG_ID
  node mcp/unified-server.js
```

### ❌ 失敗ケース
```
⚠️ Some tests FAILED.
Please check the error messages above.
```

**一般的な原因**:
- 依存関係がインストールされていない
- PythonやNode.jsのバージョンが古い
- ファイルパスが間違っている

## 🔧 トラブルシューティング

### 依存関係エラー
```bash
# Pythonライブラリ再インストール
pip install -r requirements-optimized.txt

# Node.jsライブラリ再インストール
npm install
```

### ファイルパスエラー
```bash
# 現在ディレクトリ確認
pwd

# ファイル存在確認
ls core/hatena_all.py
ls mcp/unified-server.js
```

### 権限エラー (Linux/Mac)
```bash
# 実行権限付与
chmod +x run_tests.sh
chmod +x quick_test.py
```

## 🚀 実際のブログでテスト

### 安全テスト（推奨）
```bash
# 読み取りのみテスト
python core/hatena_all.py --blog-id YOUR_BLOG_ID --mode extract
```

### フル機能テスト
```bash
# 全機能テスト (注意: ブログを変更する可能性)
python core/hatena_all.py --blog-id YOUR_BLOG_ID --mode full
```

### MCPサーバーテスト
```bash
# MCPサーバー起動
node mcp/unified-server.js

# Claude Desktopでテスト
# 「記事を抽出してください」とチャット
```

## 💸 コスト・安全性

- ✅ **無料**: テストは完全無料
- ✅ **安全**: 読み取りのみ、ブログを変更しない
- ✅ **非破壊**: オリジナルファイルに影響なし
- ✅ **高速**: 30秒以内で完了

---

**🎯 テストで安心して本格運用を開始しましょう！**