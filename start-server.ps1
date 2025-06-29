# Hatena Blog Suite - PowerShell起動スクリプト
Write-Host "🚀 Hatena Blog MCP Server - 環境変数設定中..." -ForegroundColor Green

# === Core Hatena Blog Settings ===
$env:HATENA_API_KEY = "lyls7yg12j"
$env:HATENA_ID = "motochan1969"
$env:HATENA_BLOG_ID = "lifehacking1919"

# === Extended Settings ===
$env:ALL_BLOG_DOMAINS = "motochan1969.hatenablog.com,arafo40tozan.hatenadiary.jp,lifehacking1919.hatenablog.jp"
$env:BLOG_DOMAIN = "lifehacking1919.hatenablog.jp"

# === Additional APIs ===
$env:GEMINI_API_KEY = "AIzaSyAyNIKrkKLBNDwrRNuZko3iE2Mb6nZt3T0"
$env:LINE_TOKEN = "Kunl7PKmqSwoEV97Y+keZrOtqFDoOmiQ3lNNTIk7MNujqXYe4i96UgReFiHW2cLUYV1DMTUPQLhNJ/BfdzZa02rWwYDRejT748LsaUopWM31LirNQYXR1POh5uIukdXzkTDszrv/txfTqOz/CgWXPgdB04t89/1O/w1cDnyilFU="

Write-Host "✅ 環境変数設定完了" -ForegroundColor Green
Write-Host "🎯 MCPサーバー起動中..." -ForegroundColor Cyan

# サーバー起動
node mcp/hatena-mcp-server.js