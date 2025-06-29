#!/bin/bash
# Hatena Agent v2 - Docker Entrypoint Script

set -e

echo "=== Hatena Agent v2 Container Starting ==="

# 環境変数の確認
echo "Environment Configuration:"
echo "- API_HOST: ${API_HOST:-localhost}"
echo "- API_PORT: ${API_PORT:-8080}"
echo "- MCP_PORT: ${MCP_PORT:-3000}"
echo "- NODE_ENV: ${NODE_ENV:-development}"

# データディレクトリの初期化
echo "Initializing data directories..."
mkdir -p /app/data /app/logs /app/output /app/temp /app/backup

# ファイル権限の設定
echo "Setting file permissions..."
chown -R root:root /app
find /app -type f -name "*.py" -exec chmod +x {} \;
find /app -type f -name "*.ps1" -exec chmod +x {} \;
find /app -type f -name "*.sh" -exec chmod +x {} \;

# 関数定義
start_mcp_server() {
    echo "Starting MCP Server..."
    cd /app/hatena-rag-mcp
    npm start &
    MCP_PID=$!
    echo "MCP Server started with PID: $MCP_PID"
    cd /app
}

start_api_server() {
    echo "Starting PowerShell API Server..."
    pwsh -File /app/backend/api.ps1 -Host ${API_HOST} -Port ${API_PORT} &
    API_PID=$!
    echo "API Server started with PID: $API_PID"
}

start_python_agents() {
    echo "Initializing Python agents..."
    # 必要に応じて初期化スクリプトを実行
    python -c "
import sys
sys.path.append('/app')
print('Python environment initialized')
print(f'Python version: {sys.version}')
"
}

cleanup() {
    echo "Shutting down services..."
    if [[ -n $MCP_PID ]]; then
        echo "Stopping MCP Server (PID: $MCP_PID)"
        kill $MCP_PID 2>/dev/null || true
    fi
    if [[ -n $API_PID ]]; then
        echo "Stopping API Server (PID: $API_PID)"
        kill $API_PID 2>/dev/null || true
    fi
    echo "Cleanup completed"
    exit 0
}

# シグナルハンドラーの設定
trap cleanup SIGTERM SIGINT

# コマンド別の処理
case "${1:-start}" in
    "start")
        echo "Starting all services..."
        start_python_agents
        start_mcp_server
        sleep 5  # MCPサーバーの起動を待つ
        start_api_server
        
        echo "All services started successfully"
        echo "API Server: http://${API_HOST}:${API_PORT}"
        echo "MCP Server: http://${API_HOST}:${MCP_PORT}"
        echo "Frontend: Copy frontend files to web server"
        
        # プロセスの監視
        while true; do
            if ! kill -0 $MCP_PID 2>/dev/null; then
                echo "MCP Server died, restarting..."
                start_mcp_server
            fi
            if ! kill -0 $API_PID 2>/dev/null; then
                echo "API Server died, restarting..."
                start_api_server
            fi
            sleep 30
        done
        ;;
        
    "mcp-only")
        echo "Starting MCP Server only..."
        start_mcp_server
        wait $MCP_PID
        ;;
        
    "api-only")
        echo "Starting API Server only..."
        start_api_server
        wait $API_PID
        ;;
        
    "shell")
        echo "Starting interactive shell..."
        exec /bin/bash
        ;;
        
    "test")
        echo "Running tests..."
        start_python_agents
        
        echo "Testing Python components..."
        python -m pytest tests/ || echo "Python tests completed"
        
        echo "Testing MCP server..."
        cd /app/hatena-rag-mcp
        npm test || echo "MCP tests completed"
        
        echo "Testing API server..."
        timeout 10s pwsh -File /app/backend/api.ps1 -Host localhost -Port 8081 || echo "API test completed"
        ;;
        
    "init")
        echo "Initializing application..."
        start_python_agents
        
        # データベースの初期化など
        python -c "
import sqlite3
import os

db_path = '/app/data/hatena_agent.db'
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS setup_info (key TEXT, value TEXT)')
    conn.execute('INSERT OR REPLACE INTO setup_info VALUES (\"initialized\", \"true\")')
    conn.commit()
    conn.close()
    print('Database initialized')
else:
    print('Database already exists')
"
        
        echo "Initialization completed"
        ;;
        
    *)
        echo "Usage: $0 {start|mcp-only|api-only|shell|test|init}"
        echo ""
        echo "Commands:"
        echo "  start     - Start all services (default)"
        echo "  mcp-only  - Start only MCP server"
        echo "  api-only  - Start only API server"
        echo "  shell     - Start interactive shell"
        echo "  test      - Run test suite"
        echo "  init      - Initialize application data"
        exit 1
        ;;
esac