# Hatena RAG MCP Server

MCP (Model Context Protocol) server for Hatena blog RAG (Retrieval-Augmented Generation) functionality.

## Features

### Article Management Tools
- **extract_hatena_articles**: Extract articles from Hatena blog with full content
- **search_article_content**: Search articles by content, tags, and metadata
- **get_article_details**: Get detailed information about specific articles

### RAG Integration Tools  
- **retrieve_related_articles**: Find semantically related articles using OpenAI embeddings
- **generate_article_summary**: Generate summaries from multiple articles

### Data Export Tools
- **export_articles_csv**: Export article data to CSV format
- **export_knowledge_base**: Export as knowledge base for RAG systems

## Installation

1. Install dependencies:
```bash
npm install
```

2. Build the TypeScript code:
```bash
npm run build
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

### Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=./data/articles.db
DEFAULT_BLOG_ID=your_hatena_id
DEFAULT_BLOG_DOMAIN=your_hatena_id.hatenablog.com
EXPORT_DIR=./exports
REQUEST_DELAY_MS=1000
MAX_CONCURRENT_REQUESTS=3
```

### VS Code Integration

Add to your VS Code settings.json:

```json
{
  "mcp.servers": {
    "hatena-rag": {
      "command": "node",
      "args": ["/path/to/hatena-rag-mcp/dist/index.js"],
      "env": {
        "OPENAI_API_KEY": "your_key_here"
      }
    }
  }
}
```