#!/usr/bin/env node
/**
 * Hatena Blog MCP Server - 修正版（Basic認証対応）
 * Claude Desktop完全対応
 */

// 環境変数読み込み（dotenv不要）
try {
  require('dotenv').config();
} catch (e) {
  // dotenvがない場合はスキップ
  console.error('⚠️ dotenv not found, using system environment variables only');
}

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');
const cheerio = require('cheerio');

class HatenaMCPServer {
  constructor() {
    this.server = new Server({
      name: 'hatena-blog-mcp',
      version: '2.1.0'
    }, {
      capabilities: {
        tools: {}
      }
    });

    // Hatena認証情報を環境変数から取得（Basic認証用）
    this.hatenaId = process.env.HATENA_ID;
    this.hatenaBlogId = process.env.HATENA_BLOG_ID || 'lifehacking1919.hatenablog.jp'; // フルドメイン形式
    this.hatenaApiKey = process.env.HATENA_API_KEY;
    
    console.error(`🔧 Hatena Config: ${this.hatenaId}/${this.hatenaBlogId}`);
    console.error(`🔐 Using Basic Authentication (like Python script)`);
    
    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // ツール一覧の提供
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'extract_articles',
            description: 'Extract articles from Hatena Blog',
            inputSchema: {
              type: 'object',
              properties: {
                blog_id: {
                  type: 'string',
                  description: 'Blog ID (e.g., "motcho")'
                },
                max_pages: {
                  type: 'number',
                  description: 'Maximum pages to extract',
                  default: 2
                },
                extract_content: {
                  type: 'boolean',
                  description: 'Whether to extract full content',
                  default: true
                }
              },
              required: ['blog_id']
            }
          },
          {
            name: 'publish_article',
            description: 'Publish article to Hatena Blog',
            inputSchema: {
              type: 'object',
              properties: {
                title: {
                  type: 'string',
                  description: 'Article title'
                },
                content: {
                  type: 'string',
                  description: 'Article content (Markdown supported)'
                },
                tags: {
                  type: 'array',
                  description: 'Article tags',
                  items: { type: 'string' },
                  default: []
                },
                category: {
                  type: 'string',
                  description: 'Article category',
                  default: ''
                },
                draft: {
                  type: 'boolean',
                  description: 'Publish as draft',
                  default: false
                }
              },
              required: ['title', 'content']
            }
          },
          {
            name: 'test_connection',
            description: 'Test MCP server connection',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          }
        ]
      };
    });

    // ツール実行の処理
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let result;
        switch (name) {
          case 'extract_articles':
            result = await this.extractArticles(args);
            break;
          case 'publish_article':
            result = await this.publishArticle(args);
            break;
          case 'test_connection':
            result = await this.testConnection(args);
            break;
          default:
            throw new Error(`Unknown tool: ${name}`);
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: false,
                error: error.message,
                tool: name
              }, null, 2)
            }
          ],
          isError: true
        };
      }
    });
  }

  // ======================
  // 記事投稿機能（Basic認証対応）
  // ======================
  async publishArticle(args) {
    const { title, content, tags = [], category = '', draft = false } = args;
    
    try {
      // 認証情報チェック
      if (!this.hatenaId || !this.hatenaBlogId || !this.hatenaApiKey) {
        throw new Error('Hatena credentials not configured. Please set HATENA_ID, HATENA_BLOG_ID, and HATENA_API_KEY environment variables.');
      }

      console.error(`📝 Publishing article: ${title}`);
      
      // カテゴリをタグに追加
      const allTags = [...tags];
      if (category) {
        allTags.push(category);
      }
      
      // AtomPub XML作成
      const entryXml = this.createEntryXml(title, content, allTags, draft);
      
      // はてなブログAPIに投稿（Basic認証に変更）
      const url = `https://blog.hatena.ne.jp/${this.hatenaId}/${this.hatenaBlogId}/atom/entry`;
      
      console.error(`🔍 POST to: ${url}`);
      console.error(`📄 XML preview: ${entryXml.substring(0, 200)}...`);
      
      const response = await axios.post(url, entryXml, {
        auth: {
          username: this.hatenaId,
          password: this.hatenaApiKey
        },
        headers: {
          'Content-Type': 'application/xml; charset=utf-8'
        },
        timeout: 30000
      });
      
      if (response.status === 201) {
        const result = this.parseAtomResponse(response.data);
        console.error(`✅ Article published: ${result.url}`);
        
        return {
          success: true,
          id: result.entry_id,
          url: result.url,
          title: title,
          content: content.substring(0, 100) + '...',
          tags: allTags,
          category: category,
          draft: draft,
          status: draft ? 'draft' : 'published',
          published_at: new Date().toISOString(),
          api_response_status: response.status
        };
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      console.error(`❌ Publication failed: ${error.message}`);
      if (error.response) {
        console.error(`📊 Response status: ${error.response.status}`);
        console.error(`📊 Response data: ${error.response.data}`);
      }
      return {
        success: false,
        error: `Failed to publish article: ${error.message}`,
        title: title,
        http_status: error.response?.status,
        response_data: error.response?.data
      };
    }
  }

  // ======================
  // 記事抽出機能（既存）
  // ======================
  async extractArticles(args) {
    const { blog_id, max_pages = 2, extract_content = true } = args;
    
    // マルチドメイン対応
    const supportedDomains = ['hatenablog.com', 'hatenablog.jp', 'hateblo.jp'];
    let baseUrl = null;
    let workingDomain = null;
    
    // 有効なドメインを探索
    for (const domain of supportedDomains) {
      const testUrl = `https://${blog_id}.${domain}`;
      try {
        console.error(`🔍 Testing ${testUrl}...`);
        const response = await axios.head(testUrl, {
          timeout: 5000,
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        });
        
        if (response.status === 200) {
          baseUrl = testUrl;
          workingDomain = domain;
          console.error(`✅ Found working domain: ${domain}`);
          break;
        }
      } catch (error) {
        console.error(`❌ ${domain}: ${error.message}`);
        continue;
      }
    }
    
    if (!baseUrl) {
      throw new Error(`Blog "${blog_id}" not found on any supported domain`);
    }
    
    console.error(`🔍 Extracting articles from ${baseUrl}`);
    
    try {
      const articles = [];
      
      for (let page = 1; page <= max_pages; page++) {
        const pageUrl = `${baseUrl}/archive?page=${page}`;
        console.error(`📄 Processing page ${page}...`);
        
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
          if (href && title && !links.find(l => l.href === href)) {
            links.push({ href, title });
          }
        });
        
        console.error(`Found ${links.length} links on page ${page}`);
        
        // 各記事の詳細を取得（最初の5つのみ）
        for (const link of links.slice(0, 5)) {
          try {
            const fullUrl = link.href.startsWith('http') ? link.href : `${baseUrl}${link.href}`;
            
            if (extract_content) {
              const articleResponse = await axios.get(fullUrl, { 
                timeout: 5000,
                headers: {
                  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
              });
              const $article = cheerio.load(articleResponse.data);
              
              const content = $article('.entry-content');
              const article = {
                title: link.title || $article('title').text(),
                url: fullUrl,
                content: content.text().trim().substring(0, 500) + '...',
                word_count: content.text().split(/\s+/).length,
                images: content.find('img').length,
                links: content.find('a').length,
                categories: $article('.archive-category-link').map((i, cat) => $(cat).text()).get(),
                extracted_at: new Date().toISOString()
              };
              
              articles.push(article);
              console.error(`✅ Extracted: ${article.title}`);
            } else {
              articles.push({
                title: link.title,
                url: fullUrl,
                extracted_at: new Date().toISOString()
              });
            }
            
          } catch (error) {
            console.error(`⚠️ Failed to extract ${link.href}: ${error.message}`);
          }
        }
        
        if (links.length === 0) break;
      }
      
      return {
        success: true,
        blog_id,
        blog_url: baseUrl,
        domain: workingDomain,
        articles,
        summary: `Extracted ${articles.length} articles from ${baseUrl}`,
        extracted_at: new Date().toISOString()
      };
      
    } catch (error) {
      return {
        success: false,
        error: `Failed to extract articles: ${error.message}`,
        blog_id
      };
    }
  }

  // ======================
  // ユーティリティ関数
  // ======================
  createEntryXml(title, content, tags = [], draft = false) {
    const cleanContent = this.cleanContent(title, content);
    const draftStatus = draft ? 'yes' : 'no';
    
    let xml = `<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
  <title>${this.escapeXml(title)}</title>
  <content type="text/x-markdown">${this.escapeXml(cleanContent)}</content>`;

    // タグを追加
    for (const tag of tags) {
      xml += `\n  <category term="${this.escapeXml(tag)}" />`;
    }

    xml += `\n  <app:control>
    <app:draft>${draftStatus}</app:draft>
  </app:control>
</entry>`;

    return xml;
  }

  cleanContent(title, content) {
    // タイトルの重複を除去
    if (!title || !content) return content || '';
    
    const lines = content.split('\n');
    const cleanedLines = lines.filter(line => {
      const trimmed = line.trim();
      return trimmed !== title && 
             !trimmed.startsWith(`# ${title}`) &&
             !trimmed.startsWith(`## ${title}`);
    });
    
    return cleanedLines.join('\n').trim();
  }

  escapeXml(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  parseAtomResponse(xmlData) {
    try {
      // 簡易XML解析（IDとURLを抽出）
      const idMatch = xmlData.match(/<id[^>]*>(.*?)<\/id>/);
      const linkMatch = xmlData.match(/<link[^>]*rel="alternate"[^>]*href="([^"]*)"[^>]*>/);
      
      return {
        entry_id: idMatch ? idMatch[1].split('/').pop() : '',
        url: linkMatch ? linkMatch[1] : '',
        xml: xmlData
      };
    } catch (error) {
      console.error(`XML parsing error: ${error.message}`);
      return { entry_id: '', url: '', xml: xmlData };
    }
  }

  async testConnection(args) {
    const hasCredentials = !!(this.hatenaId && this.hatenaBlogId && this.hatenaApiKey);
    
    return {
      success: true,
      message: 'Hatena Blog MCP Server is running successfully!',
      timestamp: new Date().toISOString(),
      server_info: {
        name: 'hatena-blog-mcp',
        version: '2.1.0',
        protocol: 'MCP (Model Context Protocol)',
        authentication: 'Basic Auth (like Python script)'
      },
      configuration: {
        hatena_id: this.hatenaId,
        blog_domain: this.hatenaBlogId,
        credentials_configured: hasCredentials,
        api_endpoint: hasCredentials ? `https://blog.hatena.ne.jp/${this.hatenaId}/${this.hatenaBlogId}/atom/entry` : 'N/A'
      },
      features: {
        extract_articles: true,
        publish_article: hasCredentials,
        search_articles: false,
        analyze_performance: false
      },
      available_tools: [
        'extract_articles',
        'publish_article',
        'test_connection'
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('🚀 Hatena Blog MCP Server v2.1.0 started successfully');
    console.error('🔧 Fixed: Basic Authentication (matching Python script)');
    
    if (this.hatenaId && this.hatenaBlogId && this.hatenaApiKey) {
      console.error('✅ Hatena credentials configured - publishing enabled');
      console.error(`📡 API Endpoint: https://blog.hatena.ne.jp/${this.hatenaId}/${this.hatenaBlogId}/atom/entry`);
    } else {
      console.error('⚠️ Hatena credentials not configured - publishing disabled');
    }
  }
}

// サーバー起動
if (require.main === module) {
  const server = new HatenaMCPServer();
  server.run().catch((error) => {
    console.error('❌ Server failed to start:', error);
    process.exit(1);
  });
}

module.exports = HatenaMCPServer;