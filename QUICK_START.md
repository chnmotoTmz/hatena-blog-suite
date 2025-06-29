# ⚡ Quick Start Guide

## 🚀 Instant Setup (30 seconds)

### Current Path
```bash
cd /home/motoc/redmine-agent-wsl/hatena-blog-suite/
```

### ✅ Ready-to-Use Commands

#### 1. **Python版 - 記事抽出**
```bash
python3 core/hatena_all.py --blog-id YOUR_BLOG_ID --mode extract
```

#### 2. **Python版 - フル機能**
```bash
python3 core/hatena_all.py --blog-id YOUR_BLOG_ID --mode full
```

#### 3. **MCPサーバー起動**
```bash
node mcp/simple-mcp-server.js
```

#### 4. **テスト実行**
```bash
python3 quick_test.py
```

## 🔧 Claude Desktop設定

### Config File Location
```
~/.config/claude-desktop/config.json
```

### Config Content
```json
{
  "mcpServers": {
    "hatena-suite": {
      "command": "node",
      "args": ["/home/motoc/redmine-agent-wsl/hatena-blog-suite/mcp/simple-mcp-server.js", "stdio"]
    }
  }
}
```

## 📁 Key Files

- `core/hatena_all.py` - Main Python engine
- `mcp/simple-mcp-server.js` - MCP server
- `test_output/` - Extracted data
- `package.json` - Node.js dependencies

## 🎯 Everything is ready to use\!
EOF < /dev/null
