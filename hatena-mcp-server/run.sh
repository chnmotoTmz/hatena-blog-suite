#!/bin/bash

echo "===== HATENA Agent v2 - WSL Launcher ====="

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 仮想環境の確認・作成
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}仮想環境が見つかりません。作成しますか？ (y/n): ${NC}"
    read -r create_venv
    if [ "$create_venv" = "y" ]; then
        echo -e "${BLUE}仮想環境を作成中...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}仮想環境を作成しました。${NC}"
    fi
fi

# 仮想環境をアクティベート
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}仮想環境をアクティベートしました。${NC}"
    
    # 依存関係をインストール
    if [ ! -f "venv/.installed" ]; then
        echo -e "${BLUE}依存関係をインストール中...${NC}"
        pip install -r requirements.txt
        touch venv/.installed
        echo -e "${GREEN}依存関係のインストールが完了しました。${NC}"
    fi
fi

# .envファイルの確認
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.envファイルが見つかりません。.env.exampleからコピーします...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}.envファイルを編集してAPIキーを設定してください。${NC}"
    echo "nano .env を実行して編集してください。"
    exit 1
fi

echo ""
echo -e "${YELLOW}利用可能なモード:${NC}"
echo "1. 全機能実行 (extract + enhance + repost)"
echo "2. 記事抽出のみ"
echo "3. 記事強化のみ"
echo "4. リポスト計画のみ"
echo "5. 設定ファイル編集"
echo "6. 終了"
echo ""

echo -n "モードを選択してください (1-6): "
read -r choice

if [ "$choice" = "5" ]; then
    nano .env
    exit 0
elif [ "$choice" = "6" ]; then
    exit 0
fi

# .envからHATENA_BLOG_IDを確認
source .env 2>/dev/null || true
if [ -z "$HATENA_BLOG_ID" ] || [ "$HATENA_BLOG_ID" = "your-hatena-blog-id-here" ]; then
    echo -e "${YELLOW}HATENA_BLOG_IDが設定されていません。設定ファイルを編集してください。${NC}"
    nano .env
    echo "設定が完了したら再度実行してください。"
    exit 1
fi

echo -e "${GREEN}はてなブログID: $HATENA_BLOG_ID${NC}"

case $choice in
    1)
        echo -e "${BLUE}全機能を実行中...${NC}"
        python3 main.py --mode full
        ;;
    2)
        echo -e "${BLUE}記事抽出を実行中...${NC}"
        python3 main.py --mode extract
        ;;
    3)
        echo -e "${BLUE}記事強化を実行中...${NC}"
        python3 main.py --mode enhance
        ;;
    4)
        echo -e "${BLUE}リポスト計画を作成中...${NC}"
        python3 main.py --mode repost
        ;;
    *)
        echo -e "${RED}無効な選択です。${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}処理が完了しました。${NC}"
echo "出力ファイルは output/ ディレクトリに保存されています。"
