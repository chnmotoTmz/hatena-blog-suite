#!/usr/bin/env node
/**
 * Minimal MCP Server for Hatena Blog - 軽量版
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');
const cheerio = require('cheerio');

class HatenaMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'hatena-simple',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );
    
    this.setupTools();
  }

  setupTools() {
    // 記事抽出ツール
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      if (request.params.name === 'extract_articles') {
        return this.extractArticles(request.params.arguments);
      }
      throw new Error(`Unknown tool: ${request.params.name}`);
    });
  }

  async extractArticles(args) {
    const { blog_id, max_count = 5 } = args;
    const url = `https://${blog_id}.hatenablog.com/archive`;
    
    try {
      const response = await axios.get(url);
      const $ = cheerio.load(response.data);
      const articles = [];
      
      $('a[href*="/entry/"]').slice(0, max_count).each((i, elem) => {
        articles.push({
          title: $(elem).text().trim(),
          url: $(elem).attr('href')
        });
      });
      
      return {
        content: [{
          type: 'text',
          text: `Found ${articles.length} articles:\n${JSON.stringify(articles, null, 2)}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text', 
          text: `Error: ${error.message}`
        }]
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

// サーバー起動
if (require.main === module) {
  const server = new HatenaMCPServer();
  server.run().catch(console.error);
}

module.exports = HatenaMCPServer;