#!/usr/bin/env node
/**
 * Hatena Blog MCP Server - DEBUG版（404エラー解決）
 * 環境変数の一貫性を完全保証
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');
const cheerio = require('cheerio');

class HatenaMCPServer {
  constructor() {
    this.server = new Server({
      name: 'hatena-blog-mcp',
      version: '2.2.0'
    }, {
      capabilities: {
        tools: {}
      }
    });

    // 環境変数を直接取得（dotenvは使わない）
    this.hatenaId = process.env.HATENA_ID;
    this.hatenaBlogId = process.env.HATENA_BLOG_ID;
    this.hatenaApiKey = process.env.HATENA_API_KEY;
    
    // デバッグ情報を詳細出力
    console.error(`🔧 DEBUG - Environment Variables:`);
    console.error(`   HATENA_ID: "${this.hatenaId}"`);
    console.error(`   HATENA_BLOG_ID: "${this.hatenaBlogId}"`);
    console.error(`   HATENA_API_KEY: "${this.hatenaApiKey ? 'SET' : 'NOT SET'}"`);
    console.error(`🔐 Using Basic Authentication`);
    
    // 設定検証
    if (!this.hatenaId || !this.hatenaBlogId || !this.hatenaApiKey) {
      console.error(`❌ Missing required environment variables!`);
      console.error(`   Missing: ${[
        !this.hatenaId && 'HATENA_ID',
        !this.hatenaBlogId && 'HATENA_BLOG_ID', 
        !this.hatenaApiKey && 'HATENA_API_KEY'
      ].filter(Boolean).join(', ')}`);
    }
    
    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // ツール一覧の提供
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
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
            description: 'Test MCP server connection with debug info',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          },
          {
            name: 'debug_environment',
            description: 'Debug environment variables',
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
          case 'publish_article':
            result = await this.publishArticle(args);
            break;
          case 'test_connection':
            result = await this.testConnection(args);
            break;
          case 'debug_environment':
            result = await this.debugEnvironment(args);
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
                tool: name,
                stack: error.stack
              }, null, 2)
            }
          ],
          isError: true
        };
      }
    });
  }

  // ======================
  // デバッグ機能
  // ======================
  async debugEnvironment(args) {
    return {
      success: true,
      debug_info: {
        process_env: {
          HATENA_ID: process.env.HATENA_ID,
          HATENA_BLOG_ID: process.env.HATENA_BLOG_ID,
          HATENA_API_KEY: process.env.HATENA_API_KEY ? 'SET' : 'NOT SET'
        },
        instance_vars: {
          hatenaId: this.hatenaId,
          hatenaBlogId: this.hatenaBlogId,
          hatenaApiKey: this.hatenaApiKey ? 'SET' : 'NOT SET'
        },
        constructed_url: this.hatenaId && this.hatenaBlogId ? 
          `https://blog.hatena.ne.jp/${this.hatenaId}/${this.hatenaBlogId}/atom/entry` : 'UNABLE TO CONSTRUCT',
        timestamp: new Date().toISOString()
      }
    };
  }

  // ======================
  // 記事投稿機能（完全デバッグ対応）
  // ======================
  async publishArticle(args) {
    const { title, content, tags = [], category = '', draft = false } = args;
    
    try {
      // 再度環境変数を確認（実行時の状態を保証）
      const currentHatenaId = process.env.HATENA_ID;
      const currentHatenaBlogId = process.env.HATENA_BLOG_ID;
      const currentHatenaApiKey = process.env.HATENA_API_KEY;
      
      console.error(`📝 Publishing article: "${title}"`);
      console.error(`🔍 Runtime Environment Check:`);
      console.error(`   HATENA_ID: "${currentHatenaId}"`);
      console.error(`   HATENA_BLOG_ID: "${currentHatenaBlogId}"`);
      console.error(`   API_KEY: ${currentHatenaApiKey ? 'SET' : 'NOT SET'}`);

      // 認証情報チェック
      if (!currentHatenaId || !currentHatenaBlogId || !currentHatenaApiKey) {
        const missing = [
          !currentHatenaId && 'HATENA_ID',
          !currentHatenaBlogId && 'HATENA_BLOG_ID',
          !currentHatenaApiKey && 'HATENA_API_KEY'
        ].filter(Boolean);
        
        throw new Error(`Missing environment variables: ${missing.join(', ')}`);
      }

      // カテゴリをタグに追加
      const allTags = [...tags];
      if (category) {
        allTags.push(category);
      }
      
      // AtomPub XML作成
      const entryXml = this.createEntryXml(title, content, allTags, draft);
      
      // APIエンドポイント構築（実行時の値を使用）
      const url = `https://blog.hatena.ne.jp/${currentHatenaId}/${currentHatenaBlogId}/atom/entry`;
      
      console.error(`🌐 POST URL: ${url}`);
      console.error(`📄 XML Preview (first 300 chars): ${entryXml.substring(0, 300)}...`);
      console.error(`🔐 Auth: username="${currentHatenaId}", password="${currentHatenaApiKey.substring(0, 4)}..."`);
      
      // HTTP リクエスト実行
      const response = await axios.post(url, entryXml, {
        auth: {
          username: currentHatenaId,
          password: currentHatenaApiKey
        },
        headers: {
          'Content-Type': 'application/xml; charset=utf-8',
          'User-Agent': 'Hatena-MCP-Server/2.2.0'
        },
        timeout: 30000,
        validateStatus: function (status) {
          return status < 500; // 500未満はrejectedしない
        }
      });
      
      console.error(`📊 Response Status: ${response.status}`);
      console.error(`📊 Response Headers: ${JSON.stringify(response.headers, null, 2)}`);
      console.error(`📊 Response Data (first 500 chars): ${JSON.stringify(response.data).substring(0, 500)}...`);
      
      if (response.status === 201) {
        const result = this.parseAtomResponse(response.data);
        console.error(`✅ Article published successfully: ${result.url}`);
        
        return {
          success: true,
          id: result.entry_id,
          url: result.url,
          title: title,
          tags: allTags,
          draft: draft,
          status: draft ? 'draft' : 'published',
          published_at: new Date().toISOString(),
          debug_info: {
            api_endpoint: url,
            http_status: response.status,
            response_size: JSON.stringify(response.data).length
          }
        };
      } else {
        // 詳細なエラー情報を返す
        throw new Error(`HTTP ${response.status}: ${response.statusText}. Response: ${JSON.stringify(response.data)}`);
      }
      
    } catch (error) {
      console.error(`❌ Publication failed: ${error.message}`);
      if (error.response) {
        console.error(`📊 Error Response Status: ${error.response.status}`);
        console.error(`📊 Error Response Data: ${JSON.stringify(error.response.data)}`);
        console.error(`📊 Error Response Headers: ${JSON.stringify(error.response.headers)}`);
      }
      
      return {
        success: false,
        error: `Publication failed: ${error.message}`,
        title: title,
        debug_info: {
          error_type: error.constructor.name,
          has_response: !!error.response,
          http_status: error.response?.status,
          response_data: error.response?.data,
          runtime_env: {
            HATENA_ID: process.env.HATENA_ID,
            HATENA_BLOG_ID: process.env.HATENA_BLOG_ID,
            API_KEY_SET: !!process.env.HATENA_API_KEY
          }
        }
      };
    }
  }

  // ======================
  // 修正されたテスト接続
  // ======================
  async testConnection(args) {
    // 実行時の環境変数を使用（インスタンス変数ではない）
    const currentHatenaId = process.env.HATENA_ID;
    const currentHatenaBlogId = process.env.HATENA_BLOG_ID;
    const currentHatenaApiKey = process.env.HATENA_API_KEY;
    const hasCredentials = !!(currentHatenaId && currentHatenaBlogId && currentHatenaApiKey);
    
    return {
      success: true,
      message: 'Hatena Blog MCP Server - DEBUG VERSION',
      timestamp: new Date().toISOString(),
      server_info: {
        name: 'hatena-blog-mcp',
        version: '2.2.0',
        protocol: 'MCP (Model Context Protocol)',
        authentication: 'Basic Auth'
      },
      configuration: {
        hatena_id: currentHatenaId,
        blog_domain: currentHatenaBlogId, // 実行時の値を使用
        credentials_configured: hasCredentials,
        api_endpoint: hasCredentials ? `https://blog.hatena.ne.jp/${currentHatenaId}/${currentHatenaBlogId}/atom/entry` : 'N/A'
      },
      debug_verification: {
        env_vars_at_runtime: {
          HATENA_ID: currentHatenaId,
          HATENA_BLOG_ID: currentHatenaBlogId,
          HATENA_API_KEY_SET: !!currentHatenaApiKey
        },
        instance_vars: {
          hatenaId: this.hatenaId,
          hatenaBlogId: this.hatenaBlogId,
          hatenaApiKeySet: !!this.hatenaApiKey
        },
        vars_match: {
          id_match: currentHatenaId === this.hatenaId,
          blog_match: currentHatenaBlogId === this.hatenaBlogId,
          key_match: currentHatenaApiKey === this.hatenaApiKey
        }
      },
      available_tools: [
        'publish_article',
        'test_connection',
        'debug_environment'
      ]
    };
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

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('🚀 Hatena Blog MCP Server v2.2.0 (DEBUG) started successfully');
    console.error('🔧 Complete environment variable debugging enabled');
    
    const currentHatenaId = process.env.HATENA_ID;
    const currentHatenaBlogId = process.env.HATENA_BLOG_ID;
    const currentHatenaApiKey = process.env.HATENA_API_KEY;
    
    if (currentHatenaId && currentHatenaBlogId && currentHatenaApiKey) {
      console.error('✅ All credentials configured properly');
      console.error(`📡 API Endpoint: https://blog.hatena.ne.jp/${currentHatenaId}/${currentHatenaBlogId}/atom/entry`);
    } else {
      console.error('⚠️ Missing credentials - check environment variables');
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