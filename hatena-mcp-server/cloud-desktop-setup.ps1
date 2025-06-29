# Hatena Agent v2 - Cloud Desktop Environment Setup
# クラウドデスクトップ環境セットアップスクリプト

param(
    [switch]$InstallDependencies,
    [switch]$ConfigureEnvironment,
    [switch]$StartServices,
    [switch]$All
)

Write-Host "=== Hatena Agent v2 - Cloud Desktop Setup ===" -ForegroundColor Cyan
Write-Host "クラウドデスクトップ環境セットアップを開始します..." -ForegroundColor Green

# 管理者権限チェック
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# PowerShell実行ポリシー設定
function Set-ExecutionPolicy {
    Write-Host "PowerShell実行ポリシーを設定中..." -ForegroundColor Yellow
    try {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-Host "✓ 実行ポリシー設定完了" -ForegroundColor Green
    } catch {
        Write-Host "⚠ 実行ポリシー設定に失敗: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 必要なソフトウェアのインストール
function Install-Dependencies {
    Write-Host "必要なソフトウェアをインストール中..." -ForegroundColor Yellow
    
    # Chocolatey のインストール確認
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "Chocolateyをインストール中..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    }
    
    # 必要なパッケージのインストール
    $packages = @(
        "git",
        "nodejs",
        "python",
        "vscode",
        "googlechrome",
        "7zip"
    )
    
    foreach ($package in $packages) {
        Write-Host "インストール中: $package" -ForegroundColor Yellow
        try {
            choco install $package -y
            Write-Host "✓ $package インストール完了" -ForegroundColor Green
        } catch {
            Write-Host "⚠ $package インストール失敗: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Python パッケージのインストール
    Write-Host "Python依存パッケージをインストール中..." -ForegroundColor Yellow
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
        Write-Host "✓ Python依存パッケージインストール完了" -ForegroundColor Green
    }
    
    # Node.js パッケージのインストール
    Write-Host "Node.js依存パッケージをインストール中..." -ForegroundColor Yellow
    if (Test-Path "hatena-rag-mcp/package.json") {
        Set-Location "hatena-rag-mcp"
        npm install
        Set-Location ".."
        Write-Host "✓ Node.js依存パッケージインストール完了" -ForegroundColor Green
    }
}

# 環境設定
function Configure-Environment {
    Write-Host "環境設定を構成中..." -ForegroundColor Yellow
    
    # .env ファイルの作成
    if (-not (Test-Path ".env")) {
        Write-Host ".envファイルを作成中..." -ForegroundColor Yellow
        $envContent = @"
# Hatena Agent v2 - 環境設定
# クラウドデスクトップ環境用

# === API Keys ===
OPENAI_API_KEY=your_openai_api_key_here
BING_COOKIE=your_bing_cookie_here

# === Blog Configuration ===
BLOG_URL=your_blog_url.hatenablog.com
HATENA_ID=your_hatena_id
HATENA_API_KEY=your_hatena_api_key

# === Database Settings ===
DATABASE_PATH=./data/hatena_agent.db
CHROMA_DB_PATH=./data/chroma_db

# === Cloud Desktop Settings ===
CLOUD_STORAGE_PROVIDER=azure
CLOUD_STORAGE_ACCOUNT=your_storage_account
CLOUD_STORAGE_KEY=your_storage_key

# === Server Configuration ===
API_HOST=localhost
API_PORT=8080
MCP_PORT=3000

# === Feature Flags ===
ENABLE_IMAGE_GENERATION=true
ENABLE_AFFILIATE_LINKS=true
ENABLE_AUTO_REPOST=false
ENABLE_CLOUD_SYNC=true

# === Logging ===
LOG_LEVEL=INFO
LOG_FILE=./logs/hatena_agent.log
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "✓ .envファイル作成完了" -ForegroundColor Green
        Write-Host "⚠ .envファイルを編集してAPIキーを設定してください" -ForegroundColor Yellow
    }
    
    # ディレクトリ構造の作成
    $directories = @(
        "data",
        "logs", 
        "output",
        "temp",
        "backup"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "✓ ディレクトリ作成: $dir" -ForegroundColor Green
        }
    }
    
    # Windowsファイアウォール設定
    Write-Host "ファイアウォール設定を構成中..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule -DisplayName "Hatena Agent API" -Direction Inbound -Port 8080 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
        New-NetFirewallRule -DisplayName "Hatena Agent MCP" -Direction Inbound -Port 3000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
        Write-Host "✓ ファイアウォール設定完了" -ForegroundColor Green
    } catch {
        Write-Host "⚠ ファイアウォール設定をスキップ（要管理者権限）" -ForegroundColor Yellow
    }
}

# サービス開始
function Start-Services {
    Write-Host "サービスを開始中..." -ForegroundColor Yellow
    
    # MCP サーバー開始
    if (Test-Path "hatena-rag-mcp") {
        Write-Host "MCPサーバーを開始中..." -ForegroundColor Yellow
        Start-Process -FilePath "cmd" -ArgumentList "/c", "cd hatena-rag-mcp && npm start" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Host "✓ MCPサーバー開始" -ForegroundColor Green
    }
    
    # PowerShell API サーバー開始
    if (Test-Path "backend/api.ps1") {
        Write-Host "PowerShell APIサーバーを開始中..." -ForegroundColor Yellow
        Start-Process -FilePath "powershell" -ArgumentList "-File", "backend/api.ps1" -WindowStyle Minimized
        Start-Sleep -Seconds 2
        Write-Host "✓ PowerShell APIサーバー開始" -ForegroundColor Green
    }
    
    # フロントエンド開起
    if (Test-Path "frontend/index.html") {
        Write-Host "フロントエンドを開く..." -ForegroundColor Yellow
        Start-Process "frontend/index.html"
        Write-Host "✓ ダッシュボード起動" -ForegroundColor Green
    }
}

# VSCode ワークスペース設定
function Setup-VSCodeWorkspace {
    Write-Host "VSCodeワークスペースを設定中..." -ForegroundColor Yellow
    
    $workspaceConfig = @{
        folders = @(
            @{ path = "." }
        )
        settings = @{
            "python.defaultInterpreterPath" = "./venv/Scripts/python.exe"
            "python.terminal.activateEnvironment" = $true
            "files.associations" = @{
                "*.ps1" = "powershell"
            }
            "terminal.integrated.profiles.windows" = @{
                "PowerShell" = @{
                    source = "PowerShell"
                    icon = "terminal-powershell"
                }
            }
        }
        extensions = @{
            recommendations = @(
                "ms-python.python",
                "ms-vscode.powershell",
                "ms-vscode.vscode-typescript-next",
                "esbenp.prettier-vscode"
            )
        }
    }
    
    $workspaceContent = $workspaceConfig | ConvertTo-Json -Depth 10
    $workspaceContent | Out-File -FilePath "hatena-agent-v2.code-workspace" -Encoding UTF8
    Write-Host "✓ VSCodeワークスペース設定完了" -ForegroundColor Green
}

# システム情報表示
function Show-SystemInfo {
    Write-Host "`n=== システム情報 ===" -ForegroundColor Cyan
    Write-Host "OS: $(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
    Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
    
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "Python: $(python --version)"
    }
    
    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Host "Node.js: $(node --version)"
    }
    
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Host "Git: $(git --version)"
    }
}

# 使用方法表示
function Show-Usage {
    Write-Host "`n=== 使用方法 ===" -ForegroundColor Cyan
    Write-Host "1. 初回セットアップ: .\cloud-desktop-setup.ps1 -All"
    Write-Host "2. 依存関係のみ: .\cloud-desktop-setup.ps1 -InstallDependencies"
    Write-Host "3. 環境設定のみ: .\cloud-desktop-setup.ps1 -ConfigureEnvironment"
    Write-Host "4. サービス開始のみ: .\cloud-desktop-setup.ps1 -StartServices"
    Write-Host ""
    Write-Host "セットアップ後の手順:"
    Write-Host "1. .envファイルを編集してAPIキーを設定"
    Write-Host "2. ブラウザでhttp://localhost:8080にアクセス"
    Write-Host "3. ダッシュボードでエージェントの動作確認"
}

# メイン実行
try {
    # 実行ポリシー設定
    Set-ExecutionPolicy
    
    if ($All -or $InstallDependencies) {
        Install-Dependencies
    }
    
    if ($All -or $ConfigureEnvironment) {
        Configure-Environment
        Setup-VSCodeWorkspace
    }
    
    if ($All -or $StartServices) {
        Start-Services
    }
    
    Show-SystemInfo
    Show-Usage
    
    Write-Host "`n=== セットアップ完了 ===" -ForegroundColor Green
    Write-Host "Hatena Agent v2のクラウドデスクトップ環境が準備されました。" -ForegroundColor Green
    
} catch {
    Write-Host "`n=== エラー ===" -ForegroundColor Red
    Write-Host "セットアップ中にエラーが発生しました: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "管理者権限で実行してください。" -ForegroundColor Yellow
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")