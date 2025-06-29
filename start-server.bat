@echo off
REM Hatena Blog Suite - 環境変数設定付き起動スクリプト
REM PowerShellで実行する場合の代替

echo 🚀 Hatena Blog MCP Server - 環境変数設定中...

REM === Core Hatena Blog Settings ===
set HATENA_API_KEY=lyls7yg12j
set HATENA_ID=motochan1969
set HATENA_BLOG_ID=lifehacking1919

REM === Extended Settings ===
set ALL_BLOG_DOMAINS=motochan1969.hatenablog.com,arafo40tozan.hatenadiary.jp,lifehacking1919.hatenablog.jp
set BLOG_DOMAIN=lifehacking1919.hatenablog.jp

REM === Additional APIs ===
set GEMINI_API_KEY=AIzaSyAyNIKrkKLBNDwrRNuZko3iE2Mb6nZt3T0
set LINE_TOKEN=Kunl7PKmqSwoEV97Y+keZrOtqFDoOmiQ3lNNTIk7MNujqXYe4i96UgReFiHW2cLUYV1DMTUPQLhNJ/BfdzZa02rWwYDRejT748LsaUopWM31LirNQYXR1POh5uIukdXzkTDszrv/txfTqOz/CgWXPgdB04t89/1O/w1cDnyilFU=

echo ✅ 環境変数設定完了
echo 🎯 起動中...

node mcp/hatena-mcp-server.js

pause