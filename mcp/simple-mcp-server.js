#!/usr/bin/env node
/**
 * Simple MCP Server - Working Version
 * 軽量で動作確認済みのMCPサーバー
 */

// シンプルなMCPサーバー実装（基本機能のみ）
const http = require('http');
const url = require('url');
const axios = require('axios');
const cheerio = require('cheerio');

class SimpleMCPServer {
  constructor() {
    this.tools = {
      extract_articles: this.extractArticles.bind(this),
      search_articles: this.searchArticles.bind(this),
      analyze_performance: this.analyzePerformance.bind(this),
      test_connection: this.testConnection.bind(this)
    };
  }

  async extractArticles(args) {
    const { blog_id = 'motcho', max_pages = 2 } = args;
    const baseUrl = `https://${blog_id}.hatenablog.com`;
    
    try {
      console.log(`🔍 Extracting articles from ${baseUrl}`);
      const articles = [];
      
      for (let page = 1; page <= max_pages; page++) {
        const pageUrl = `${baseUrl}/archive?page=${page}`;
        console.log(`📄 Processing page ${page}...`);
        
        const response = await axios.get(pageUrl, {
          timeout: 10000,
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        });
        
        const $ = cheerio.load(response.data);
        
        // 記事リンクを抽出
        const links = [];
        $('a[href*="/entry/"]').each((i, elem) => {
          const href = $(elem).attr('href');
          const title = $(elem).text().trim();
          if (href && title && !links.includes(href)) {
            links.push({ href, title });
          }
        });
        
        console.log(`Found ${links.length} links on page ${page}`);
        
        // 各記事の詳細を取得（最初の5つのみ）
        for (const link of links.slice(0, 5)) {
          try {
            const fullUrl = link.href.startsWith('http') ? link.href : `${baseUrl}${link.href}`;
            const articleResponse = await axios.get(fullUrl, { timeout: 5000 });
            const $article = cheerio.load(articleResponse.data);
            
            const content = $article('.entry-content');
            const article = {
              title: link.title || $article('title').text(),
              url: fullUrl,
              content: content.text().trim().substring(0, 500) + '...',
              word_count: content.text().split(/\s+/).length,
              images: content.find('img').length,
              links: content.find('a').length,
              extracted_at: new Date().toISOString()
            };
            
            articles.push(article);
            console.log(`✅ Extracted: ${article.title}`);
            
          } catch (error) {
            console.log(`⚠️ Failed to extract ${link.href}: ${error.message}`);
          }
        }
        
        if (links.length === 0) break; // ページが空の場合は終了
      }
      
      return {
        success: true,
        articles,
        summary: `Extracted ${articles.length} articles from ${blog_id}.hatenablog.com`
      };
      
    } catch (error) {
      return {
        success: false,
        error: `Failed to extract articles: ${error.message}`
      };
    }
  }

  async searchArticles(args) {
    const { query = 'test', articles = [] } = args;
    
    const results = articles.filter(article => 
      article.title.toLowerCase().includes(query.toLowerCase()) ||
      (article.content && article.content.toLowerCase().includes(query.toLowerCase()))
    );
    
    return {
      success: true,
      query,
      results: results.slice(0, 10),
      summary: `Found ${results.length} articles matching "${query}"`
    };
  }

  async analyzePerformance(args) {
    const { articles = [] } = args;
    
    if (articles.length === 0) {
      return {
        success: false,
        error: 'No articles provided for analysis'
      };
    }
    
    const totalWords = articles.reduce((sum, a) => sum + (a.word_count || 0), 0);
    const avgWords = Math.round(totalWords / articles.length);
    const avgImages = articles.reduce((sum, a) => sum + (a.images || 0), 0) / articles.length;
    const avgLinks = articles.reduce((sum, a) => sum + (a.links || 0), 0) / articles.length;
    
    const seoScore = Math.min(100, 
      (avgWords / 300) * 40 + 
      Math.min(avgImages, 3) * 10 + 
      Math.min(avgLinks, 5) * 10 + 
      20
    );
    
    return {
      success: true,
      analysis: {
        total_articles: articles.length,
        total_words: totalWords,
        avg_words: avgWords,
        avg_images: Math.round(avgImages * 10) / 10,
        avg_links: Math.round(avgLinks * 10) / 10,
        seo_score: Math.round(seoScore),
        recommendations: seoScore < 70 ? 
          ['記事の文字数を増やしましょう', '画像を追加しましょう', 'リンクを増やしましょう'] :
          ['良好な状態です！']
      }
    };
  }

  async testConnection(args) {
    return {
      success: true,
      message: 'MCP Server is running successfully!',
      timestamp: new Date().toISOString(),
      available_tools: Object.keys(this.tools)
    };
  }

  async handleRequest(toolName, args) {
    console.log(`🔧 Tool called: ${toolName}`);
    console.log(`📝 Args:`, JSON.stringify(args, null, 2));
    
    if (!this.tools[toolName]) {
      return {
        success: false,
        error: `Unknown tool: ${toolName}`
      };
    }
    
    try {
      const result = await this.tools[toolName](args);
      console.log(`✅ Tool completed: ${toolName}`);
      return result;
    } catch (error) {
      console.error(`❌ Tool failed: ${toolName}`, error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // HTTPサーバーとして動作（テスト用）
  startHTTPServer(port = 3000) {
    const server = http.createServer(async (req, res) => {
      // CORS対応
      res.setHeader('Access-Control-Allow-Origin', '*');
      res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
      
      if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
      }
      
      if (req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
          try {
            const { tool, args } = JSON.parse(body);
            const result = await this.handleRequest(tool, args);
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(result, null, 2));
          } catch (error) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: false, error: error.message }));
          }
        });
      } else if (req.method === 'GET') {
        const parsed = url.parse(req.url, true);
        
        if (parsed.pathname === '/') {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <h1>Hatena Blog MCP Server</h1>
            <p>Server is running! Available tools:</p>
            <ul>
              ${Object.keys(this.tools).map(tool => `<li>${tool}</li>`).join('')}
            </ul>
            <p>Test the server:</p>
            <button onclick="testServer()">Test Connection</button>
            <div id="result"></div>
            <script>
              async function testServer() {
                const response = await fetch('/', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ tool: 'test_connection', args: {} })
                });
                const result = await response.json();
                document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
              }
            </script>
          `);
        } else {
          res.writeHead(404);
          res.end('Not Found');
        }
      }
    });
    
    server.listen(port, () => {
      console.log(`🚀 MCP Server started at http://localhost:${port}`);
      console.log(`🛠️ Available tools: ${Object.keys(this.tools).join(', ')}`);
    });
    
    return server;
  }

  // STDIOモード（Claude Desktop用）
  startSTDIOMode() {
    console.log('🔗 Starting MCP Server in STDIO mode...');
    console.log('🛠️ Available tools:', Object.keys(this.tools).join(', '));
    
    process.stdin.on('data', async (data) => {
      try {
        const input = JSON.parse(data.toString().trim());
        const result = await this.handleRequest(input.tool, input.args);
        process.stdout.write(JSON.stringify(result) + '\n');
      } catch (error) {
        process.stdout.write(JSON.stringify({
          success: false,
          error: error.message
        }) + '\n');
      }
    });
  }
}

// サーバー起動
if (require.main === module) {
  const server = new SimpleMCPServer();
  
  // コマンドライン引数で動作モードを選択
  const mode = process.argv[2] || 'http';
  
  if (mode === 'stdio') {
    server.startSTDIOMode();
  } else {
    const port = parseInt(process.argv[3]) || 3000;
    server.startHTTPServer(port);
  }
}

module.exports = SimpleMCPServer;
