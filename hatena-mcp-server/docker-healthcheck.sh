#!/bin/bash
# Hatena Agent v2 - Docker Health Check Script

set -e

# ヘルスチェック関数
check_api_server() {
    local api_host="${API_HOST:-localhost}"
    local api_port="${API_PORT:-8080}"
    
    if curl -f -s "http://${api_host}:${api_port}/api/status" > /dev/null; then
        echo "✓ API Server is healthy"
        return 0
    else
        echo "✗ API Server is not responding"
        return 1
    fi
}

check_mcp_server() {
    local mcp_host="${API_HOST:-localhost}"
    local mcp_port="${MCP_PORT:-3000}"
    
    if curl -f -s "http://${mcp_host}:${mcp_port}/tools" > /dev/null; then
        echo "✓ MCP Server is healthy"
        return 0
    else
        echo "✗ MCP Server is not responding"
        return 1
    fi
}

check_python_environment() {
    if python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor} OK')" > /dev/null 2>&1; then
        echo "✓ Python environment is healthy"
        return 0
    else
        echo "✗ Python environment has issues"
        return 1
    fi
}

check_file_system() {
    local required_dirs=("/app/data" "/app/logs" "/app/output")
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]] || [[ ! -w "$dir" ]]; then
            echo "✗ Directory $dir is not accessible"
            return 1
        fi
    done
    
    echo "✓ File system is healthy"
    return 0
}

check_memory_usage() {
    local memory_limit_mb=1000  # 1GB limit
    local current_usage_mb
    
    # メモリ使用量を取得（MB単位）
    current_usage_mb=$(ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem | awk 'NR>1 {sum+=$4} END {print int(sum * 10)}')
    
    if [[ $current_usage_mb -gt $memory_limit_mb ]]; then
        echo "⚠ High memory usage: ${current_usage_mb}MB"
        return 1
    else
        echo "✓ Memory usage is normal: ${current_usage_mb}MB"
        return 0
    fi
}

# メインヘルスチェック
main() {
    echo "=== Health Check Starting ==="
    local exit_code=0
    
    # 基本システムチェック
    check_python_environment || exit_code=1
    check_file_system || exit_code=1
    
    # サービスチェック（任意のエラーは警告として扱う）
    if ! check_mcp_server; then
        echo "⚠ MCP Server check failed (may be starting up)"
    fi
    
    if ! check_api_server; then
        echo "⚠ API Server check failed (may be starting up)"
    fi
    
    # メモリチェック
    check_memory_usage || echo "⚠ Memory usage warning"
    
    # 総合判定
    if [[ $exit_code -eq 0 ]]; then
        echo "=== Health Check PASSED ==="
    else
        echo "=== Health Check FAILED ==="
    fi
    
    return $exit_code
}

# 詳細モード（デバッグ用）
if [[ "${1}" == "--verbose" ]]; then
    echo "=== Detailed Health Check ==="
    
    echo "Environment Variables:"
    echo "- API_HOST: ${API_HOST:-localhost}"
    echo "- API_PORT: ${API_PORT:-8080}"
    echo "- MCP_PORT: ${MCP_PORT:-3000}"
    echo "- NODE_ENV: ${NODE_ENV:-development}"
    
    echo "Process Information:"
    ps aux | head -1
    ps aux | grep -E "(python|node|pwsh)" | grep -v grep || echo "No target processes found"
    
    echo "Network Ports:"
    netstat -tlnp 2>/dev/null | grep -E ":${API_PORT:-8080}|:${MCP_PORT:-3000}" || echo "Target ports not found"
    
    echo "Disk Usage:"
    df -h /app 2>/dev/null || echo "Disk usage information not available"
    
    echo "Recent Logs:"
    tail -n 5 /app/logs/*.log 2>/dev/null || echo "No log files found"
fi

# メイン実行
main "$@"