# HATENA Agent v2 - PowerShell Launcher
Write-Host "===== HATENA Agent v2 - PowerShell Launcher =====" -ForegroundColor Cyan

# 仮想環境をアクティベート
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "仮想環境をアクティベートしました。" -ForegroundColor Green
} else {
    Write-Host "仮想環境が見つかりません。作成しますか？ (y/n): " -NoNewline
    $createVenv = Read-Host
    if ($createVenv -eq "y") {
        python -m venv venv
        & "venv\Scripts\Activate.ps1"
        pip install -r requirements.txt
    }
}

# .envファイルをチェック
if (-not (Test-Path ".env")) {
    Write-Host ".envファイルが見つかりません。作成します..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".envファイルを編集してAPIキーを設定してください。" -ForegroundColor Yellow
    notepad .env
    Read-Host "設定が完了したらEnterを押してください"
}

Write-Host ""
Write-Host "利用可能なモード:" -ForegroundColor Yellow
Write-Host "1. 全機能実行 (extract + enhance + repost)"
Write-Host "2. 記事抽出のみ"
Write-Host "3. 記事強化のみ"
Write-Host "4. リポスト計画のみ"
Write-Host "5. 終了"
Write-Host ""

$choice = Read-Host "モードを選択してください (1-5)"
$hatenaId = Read-Host "はてなブログID を入力してください"

switch ($choice) {
    "1" { python main.py --hatena-id $hatenaId --mode full }
    "2" { python main.py --hatena-id $hatenaId --mode extract }
    "3" { python main.py --hatena-id $hatenaId --mode enhance }
    "4" { python main.py --hatena-id $hatenaId --mode repost }
    "5" { exit }
    default { 
        Write-Host "無効な選択です。" -ForegroundColor Red
        Read-Host "Enterを押して終了してください"
    }
}

Write-Host ""
Write-Host "処理が完了しました。" -ForegroundColor Green
Read-Host "Enterを押して終了してください"
