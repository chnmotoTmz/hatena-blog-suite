#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ToolSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { HatenaArticleExtractor } from './extractors/article-extractor.js';
import { HatenaRAGService } from './services/rag-service.js';
import { ArticleDatabase } from './database/article-db.js';
import { ArticleExporter } from './exporters/article-exporter.js';

class HatenaRAGServer {
  private server: Server;
  private extractor!: HatenaArticleExtractor;
  private ragService!: HatenaRAGService;
  private database!: ArticleDatabase;
  private exporter!: ArticleExporter;

  constructor() {
    this.server = new Server(
      {
        name: 'hatena-rag-mcp',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
    this.setupServices();
  }

  private setupServices() {
    this.database = new ArticleDatabase();
    this.extractor = new HatenaArticleExtractor();
    this.ragService = new HatenaRAGService(this.database);
    this.exporter = new ArticleExporter(this.database);
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'extract_hatena_articles',
          description: 'Extract articles from Hatena blog',
          inputSchema: {
            type: 'object',
            properties: {
              blog_id: {
                type: 'string',
                description: 'Hatena blog ID'
              },
              blog_domain: {
                type: 'string',
                description: 'Custom blog domain (optional)'
              },
              max_pages: {
                type: 'number',
                description: 'Maximum pages to extract (optional)'
              },
              extract_full_content: {
                type: 'boolean',
                description: 'Whether to extract full article content',
                default: true
              }
            },
            required: ['blog_id']
          }
        },
        {
          name: 'search_article_content',
          description: 'Search articles by content, tags, or metadata',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query'
              },
              tags: {
                type: 'array',
                items: { type: 'string' },
                description: 'Filter by tags/categories'
              },
              date_from: {
                type: 'string',
                description: 'Start date (ISO format)'
              },
              date_to: {
                type: 'string',
                description: 'End date (ISO format)'
              },
              limit: {
                type: 'number',
                description: 'Maximum results to return',
                default: 10
              }
            },
            required: ['query']
          }
        },
        {
          name: 'get_article_details',
          description: 'Get detailed information about a specific article',
          inputSchema: {
            type: 'object',
            properties: {
              article_id: {
                type: 'string',
                description: 'Article ID or URL'
              }
            },
            required: ['article_id']
          }
        },
        {
          name: 'retrieve_related_articles',
          description: 'Find articles related to a query using semantic search',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Query text for finding related articles'
              },
              similarity_threshold: {
                type: 'number',
                description: 'Minimum similarity score (0-1)',
                default: 0.7
              },
              max_results: {
                type: 'number',
                description: 'Maximum number of results',
                default: 5
              }
            },
            required: ['query']
          }
        },
        {
          name: 'generate_article_summary',
          description: 'Generate summary from multiple articles',
          inputSchema: {
            type: 'object',
            properties: {
              article_ids: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of article IDs to summarize'
              },
              summary_type: {
                type: 'string',
                enum: ['brief', 'detailed', 'outline'],
                description: 'Type of summary to generate',
                default: 'brief'
              }
            },
            required: ['article_ids']
          }
        },
        {
          name: 'export_articles_csv',
          description: 'Export articles to CSV format',
          inputSchema: {
            type: 'object',
            properties: {
              filter_conditions: {
                type: 'object',
                description: 'Conditions to filter articles'
              },
              fields: {
                type: 'array',
                items: { type: 'string' },
                description: 'Fields to include in export'
              },
              output_path: {
                type: 'string',
                description: 'Output file path'
              }
            },
            required: ['output_path']
          }
        },
        {
          name: 'export_knowledge_base',
          description: 'Export articles as knowledge base for RAG',
          inputSchema: {
            type: 'object',
            properties: {
              format: {
                type: 'string',
                enum: ['text', 'json', 'markdown'],
                description: 'Export format',
                default: 'json'
              },
              chunking_strategy: {
                type: 'string',
                enum: ['sentence', 'paragraph', 'semantic'],
                description: 'How to chunk the content',
                default: 'paragraph'
              },
              output_path: {
                type: 'string',
                description: 'Output file path'
              }
            },
            required: ['output_path']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'extract_hatena_articles':
            return await this.handleExtractArticles(args);
          
          case 'search_article_content':
            return await this.handleSearchArticles(args);
          
          case 'get_article_details':
            return await this.handleGetArticleDetails(args);
          
          case 'retrieve_related_articles':
            return await this.handleRetrieveRelatedArticles(args);
          
          case 'generate_article_summary':
            return await this.handleGenerateArticleSummary(args);
          
          case 'export_articles_csv':
            return await this.handleExportArticlesCSV(args);
          
          case 'export_knowledge_base':
            return await this.handleExportKnowledgeBase(args);
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error instanceof Error ? error.message : String(error)}`
          }],
          isError: true
        };
      }
    });
  }

  private async handleExtractArticles(args: any) {
    const { blog_id, blog_domain, max_pages, extract_full_content = true } = args;
    
    this.extractor.configure(blog_id, blog_domain);
    const articles = await this.extractor.extractAllArticles(max_pages, extract_full_content);
    
    await this.database.saveArticles(articles);
    
    return {
      content: [{
        type: 'text',
        text: `Successfully extracted ${articles.length} articles from ${blog_id}'s blog`
      }]
    };
  }

  private async handleSearchArticles(args: any) {
    const { query, tags, date_from, date_to, limit = 10 } = args;
    
    const results = await this.database.searchArticles({
      query,
      tags,
      dateFrom: date_from,
      dateTo: date_to,
      limit
    });
    
    return {
      content: [{
        type: 'text',
        text: `Found ${results.length} articles matching the search criteria:\n\n` +
              results.map(article => 
                `• ${article.title}\n  URL: ${article.url}\n  Date: ${article.date}\n`
              ).join('\n')
      }]
    };
  }

  private async handleGetArticleDetails(args: any) {
    const { article_id } = args;
    
    const article = await this.database.getArticleById(article_id);
    if (!article) {
      throw new Error(`Article not found: ${article_id}`);
    }
    
    return {
      content: [{
        type: 'text',
        text: `Title: ${article.title}\nURL: ${article.url}\nDate: ${article.date}\nCategories: ${article.categories.join(', ')}\n\nContent:\n${article.content || article.summary}`
      }]
    };
  }

  private async handleRetrieveRelatedArticles(args: any) {
    const { query, similarity_threshold = 0.7, max_results = 5 } = args;
    
    const relatedArticles = await this.ragService.findRelatedArticles(
      query, 
      similarity_threshold, 
      max_results
    );
    
    return {
      content: [{
        type: 'text',
        text: `Found ${relatedArticles.length} related articles:\n\n` +
              relatedArticles.map(({ article, score }) => 
                `• ${article.title} (similarity: ${score.toFixed(3)})\n  ${article.url}\n`
              ).join('\n')
      }]
    };
  }

  private async handleGenerateArticleSummary(args: any) {
    const { article_ids, summary_type = 'brief' } = args;
    
    const summary = await this.ragService.generateSummary(article_ids, summary_type);
    
    return {
      content: [{
        type: 'text',
        text: summary
      }]
    };
  }

  private async handleExportArticlesCSV(args: any) {
    const { filter_conditions, fields, output_path } = args;
    
    await this.exporter.exportToCSV(output_path, filter_conditions, fields);
    
    return {
      content: [{
        type: 'text',
        text: `Articles exported to CSV: ${output_path}`
      }]
    };
  }

  private async handleExportKnowledgeBase(args: any) {
    const { format = 'json', chunking_strategy = 'paragraph', output_path } = args;
    
    await this.exporter.exportKnowledgeBase(output_path, format, chunking_strategy);
    
    return {
      content: [{
        type: 'text',
        text: `Knowledge base exported: ${output_path}`
      }]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

const server = new HatenaRAGServer();
server.run().catch(console.error);