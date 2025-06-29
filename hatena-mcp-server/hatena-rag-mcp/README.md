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

## Usage

### 1. Extract Articles

```typescript
// Extract all articles from a Hatena blog
await extract_hatena_articles({
  blog_id: "your_hatena_id",
  max_pages: 10,
  extract_full_content: true
});
```

### 2. Search Articles

```typescript
// Search articles by keywords
await search_article_content({
  query: "React TypeScript",
  tags: ["技術", "プログラミング"],
  limit: 5
});
```

### 3. Find Related Articles

```typescript
// Find semantically related articles
await retrieve_related_articles({
  query: "Machine Learning with Python",
  similarity_threshold: 0.8,
  max_results: 3
});
```

### 4. Export Data

```typescript
// Export to CSV
await export_articles_csv({
  output_path: "./exports/articles.csv",
  fields: ["title", "url", "date", "categories", "wordCount"]
});

// Export as knowledge base
await export_knowledge_base({
  output_path: "./exports/knowledge_base.json",
  format: "json",
  chunking_strategy: "paragraph"
});
```

## API Reference

### Tools

#### extract_hatena_articles
Extract articles from Hatena blog.

**Parameters:**
- `blog_id` (string, required): Hatena blog ID
- `blog_domain` (string, optional): Custom blog domain
- `max_pages` (number, optional): Maximum pages to extract
- `extract_full_content` (boolean, optional): Extract full content vs summary only

#### search_article_content
Search articles by content and metadata.

**Parameters:**
- `query` (string, required): Search query
- `tags` (array, optional): Filter by tags/categories
- `date_from` (string, optional): Start date (ISO format)
- `date_to` (string, optional): End date (ISO format)
- `limit` (number, optional): Maximum results

#### retrieve_related_articles
Find related articles using semantic search.

**Parameters:**
- `query` (string, required): Query text
- `similarity_threshold` (number, optional): Minimum similarity score (0-1)
- `max_results` (number, optional): Maximum results

#### export_articles_csv
Export articles to CSV format.

**Parameters:**
- `output_path` (string, required): Output file path
- `filter_conditions` (object, optional): Conditions to filter articles
- `fields` (array, optional): Fields to include

## Database Schema

The server uses SQLite with the following tables:

- **articles**: Main article data
- **article_images**: Article images
- **article_links**: Article links
- **articles_fts**: Full-text search index

## Development

### Running in Development Mode

```bash
npm run dev
```

### Building

```bash
npm run build
```

### Testing

```bash
npm test
```

## Dependencies

- **@modelcontextprotocol/sdk**: MCP server framework
- **axios**: HTTP client for web scraping
- **cheerio**: HTML parsing
- **sqlite/sqlite3**: Database
- **openai**: OpenAI API for embeddings

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and feature requests, please create an issue in the repository.