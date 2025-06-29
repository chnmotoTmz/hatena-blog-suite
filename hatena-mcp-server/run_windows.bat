@echo off
echo ===== HATENA Agent v2 - Windows Launcher =====

REM 仮想環境をアクティベート
call venv\Scripts\activate.bat

echo 環境変数ファイルをチェック中...
if not exist .env (
    echo .envファイルが見つかりません。.env.exampleからコピーしてください。
    copy .env.example .env
    echo .envファイルを編集してAPIキーを設定してください。
    notepad .env
    pause
    exit /b
)

echo.
echo 利用可能なモード:
echo 1. 全機能実行 (extract + enhance + repost)
echo 2. 記事抽出のみ
echo 3. 記事強化のみ
echo 4. リポスト計画のみ
echo 5. 終了
echo.

set /p choice="モードを選択してください (1-5): "

set /p hatena_id="はてなブログID を入力してください: "

if "%choice%"=="1" (
    python main.py --hatena-id %hatena_id% --mode full
) else if "%choice%"=="2" (
    python main.py --hatena-id %hatena_id% --mode extract
) else if "%choice%"=="3" (
    python main.py --hatena-id %hatena_id% --mode enhance
) else if "%choice%"=="4" (
    python main.py --hatena-id %hatena_id% --mode repost
) else if "%choice%"=="5" (
    exit /b
) else (
    echo 無効な選択です。
    pause
    goto :eof
)

echo.
echo 処理が完了しました。
pause
