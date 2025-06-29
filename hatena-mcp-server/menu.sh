#!/bin/bash

# HATENA Agent v2 CLI メニュー起動スクリプト

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}HATENA Agent v2 CLI メニューを起動します...${NC}"

# 仮想環境の確認とアクティベート
if [ -d "venv" ]; then
    echo -e "${YELLOW}仮想環境をアクティベートしています...${NC}"
    source venv/bin/activate
elif [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}仮想環境は既にアクティベートされています${NC}"
else
    echo -e "${YELLOW}警告: 仮想環境が見つかりません${NC}"
fi

# CLIメニューを起動
python3 cli_menu.py

# 終了時のメッセージ
echo -e "\n${GREEN}HATENA Agent v2 を終了しました${NC}"