"""
Hatena Blog Suite - MCP Server Configuration
MCPサーバー設定ファイル
"""

import json
from pathlib import Path

# MCP Server Configuration for Claude Desktop
MCP_CONFIG = {
    "mcpServers": {
        "hatena-blog-suite": {
            "command": "python",
            "args": [str(Path(__file__).parent / "mcp" / "hatena-mcp-server" / "server.py")],
            "env": {
                "HATENA_ID": "your-hatena-id",
                "HATENA_API_KEY": "your-api-key",
                "BLOG_DOMAIN": "your-blog.hatenablog.com"
            }
        }
    }
}

def generate_claude_config():
    """Claude Desktop用の設定ファイルを生成"""
    config_file = Path("config") / "claude_desktop_config.json"
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(MCP_CONFIG, f, indent=2, ensure_ascii=False)
    
    print(f"Claude Desktop configuration generated: {config_file}")
    print("Copy this configuration to your Claude Desktop settings:")
    print(f"  Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print(f"  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")

if __name__ == "__main__":
    generate_claude_config()
