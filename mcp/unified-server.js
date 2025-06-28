#!/usr/bin/env node
/**
 * Unified MCP Server - 全機能統合版（90%削減）
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs').promises;
const path = require('path');

class UnifiedMCPServer {
  constructor() {
    this.server = new Server({ name: 'hatena-unified', version: '1.0.0' }, { capabilities: { tools: {} } });
    this.cache = new Map(); // 結果キャッシュ
    this.setupTools();
  }

  setupTools() {
    // 全ツールを統一ハンドラで処理
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      const tools = {
        extract_articles: () => this.extractArticles(args),
        enhance_articles: () => this.enhanceArticles(args),
        analyze_performance: () => this.analyzePerformance(args),
        check_links: () => this.checkLinks(args),
        generate_repost_plan: () => this.generateRepostPlan(args),
        build_knowledge_graph: () => this.buildKnowledgeGraph(args),
        search_articles: () => this.searchArticles(args),
        export_data: () => this.exportData(args)
      };
      
      if (!tools[name]) throw new Error(`Unknown tool: ${name}`);
      return tools[name]();
    });
  }

  async extractArticles({ blog_id, max_pages = 3, extract_content = true }) {
    const cacheKey = `extract_${blog_id}_${max_pages}`;
    if (this.cache.has(cacheKey)) return this.cache.get(cacheKey);

    try {
      const articles = [];
      for (let page = 1; page <= max_pages; page++) {
        const { data } = await axios.get(`https://${blog_id}.hatenablog.com/archive?page=${page}`);
        const $ = cheerio.load(data);
        
        const links = [...new Set($('a[href*="/entry/"]').map((i, el) => $(el).attr('href')).get())];
        if (!links.length) break;
        
        for (const link of links.slice(0, 10)) {
          const fullUrl = link.startsWith('http') ? link : `https://${blog_id}.hatenablog.com${link}`;
          
          if (extract_content) {
            const { data: articleData } = await axios.get(fullUrl);
            const $article = cheerio.load(articleData);
            const content = $article('.entry-content');
            
            articles.push({
              title: $article('title').text() || link.split('/').pop(),
              url: fullUrl,
              content: content.text().trim(),
              html_content: content.html(),
              word_count: content.text().split(/\s+/).length,
              images: content.find('img').map((i, img) => ({ url: $(img).attr('src'), alt: $(img).attr('alt') })).get(),
              links: content.find('a').map((i, a) => ({ url: $(a).attr('href'), text: $(a).text() })).get(),
              categories: $article('.archive-category-link').map((i, cat) => $(cat).text()).get(),
              extracted_at: new Date().toISOString()
            });
          } else {
            articles.push({ title: $(link).text(), url: fullUrl });
          }
        }
      }
      
      const result = { content: [{ type: 'text', text: `抽出完了: ${articles.length}記事\n${JSON.stringify(articles, null, 2)}` }] };
      this.cache.set(cacheKey, result);
      return result;
    } catch (error) {
      return { content: [{ type: 'text', text: `エラー: ${error.message}` }] };
    }
  }

  async enhanceArticles({ articles, options = {} }) {
    const enhanced = articles.map(article => {
      const result = { ...article };
      
      // アフィリエイトリンク処理
      if (options.affiliate && article.content) {
        result.enhanced_content = article.content
          .replace(/(https?:\/\/[^\s]*amazon\.[^\s]*)/g, `$1?tag=${options.amazon_tag || 'default'}`)
          .replace(/(https?:\/\/[^\s]*rakuten\.[^\s]*)/g, `$1?tag=${options.rakuten_tag || 'default'}`);
      }
      
      // 関連記事検索
      if (options.find_related) {
        const keywords = article.title.split(' ').slice(0, 3);
        result.related_articles = articles.filter(other => 
          other !== article && keywords.some(kw => other.title.toLowerCase().includes(kw.toLowerCase()))
        ).slice(0, 3).map(r => ({ title: r.title, url: r.url }));
      }
      
      return result;
    });
    
    return { content: [{ type: 'text', text: `拡張完了: ${enhanced.length}記事\n${JSON.stringify(enhanced, null, 2)}` }] };
  }

  async analyzePerformance({ articles }) {
    const totalWords = articles.reduce((sum, a) => sum + (a.word_count || 0), 0);
    const avgWords = totalWords / articles.length;
    const categories = articles.flatMap(a => a.categories || []);
    const categoryCount = categories.reduce((acc, cat) => ({ ...acc, [cat]: (acc[cat] || 0) + 1 }), {});
    
    const analysis = {
      total_articles: articles.length,
      total_words: totalWords,
      avg_words: Math.round(avgWords),
      top_categories: Object.entries(categoryCount).sort(([,a], [,b]) => b - a).slice(0, 5),
      seo_score: Math.min(100, (avgWords / 500) * 50 + 30),
      recommendations: avgWords < 300 ? ['記事の文字数を増やしましょう'] : ['良好な状態です']
    };
    
    return { content: [{ type: 'text', text: `分析完了:\n${JSON.stringify(analysis, null, 2)}` }] };
  }

  async checkLinks({ articles }) {
    const allLinks = articles.flatMap(a => (a.links || []).map(l => ({ ...l, article: a.title })));
    const results = { working: 0, broken: [], total: allLinks.length };
    
    for (const link of allLinks.slice(0, 20)) { // 負荷軽減
      try {
        const response = await axios.head(link.url, { timeout: 3000 });
        if (response.status >= 400) {
          results.broken.push({ url: link.url, article: link.article, status: response.status });
        } else {
          results.working++;
        }
      } catch {
        results.broken.push({ url: link.url, article: link.article, status: 'timeout' });
      }
    }
    
    return { content: [{ type: 'text', text: `リンクチェック完了:\n正常: ${results.working}\n破損: ${results.broken.length}\n${JSON.stringify(results.broken, null, 2)}` }] };
  }

  async generateRepostPlan({ articles, weeks = 4 }) {
    const scored = articles.map(a => ({
      ...a,
      score: (a.word_count || 0) * 0.1 + (a.links?.length || 0) * 5 + (a.categories?.length || 0) * 2
    })).sort((a, b) => b.score - a.score).slice(0, weeks);
    
    const plan = scored.map((article, i) => ({
      week: i + 1,
      article: { title: article.title, url: article.url },
      update_type: ['content_refresh', 'link_update', 'seo_optimize'][i % 3],
      priority: article.score > 100 ? 'high' : 'medium'
    }));
    
    return { content: [{ type: 'text', text: `リポスト計画生成完了:\n${JSON.stringify(plan, null, 2)}` }] };
  }

  async buildKnowledgeGraph({ articles }) {
    const keywords = {};
    articles.forEach(article => {
      const words = (article.content || '').toLowerCase().match(/\b\w{3,}\b/g) || [];
      [...new Set(words)].forEach(word => {
        if (!keywords[word]) keywords[word] = [];
        keywords[word].push(article.title);
      });
    });
    
    const connections = Object.entries(keywords).filter(([, titles]) => titles.length > 1);
    const graph = {
      total_keywords: Object.keys(keywords).length,
      connections: connections.length,
      top_keywords: Object.entries(keywords).sort(([,a], [,b]) => b.length - a.length).slice(0, 10)
    };
    
    return { content: [{ type: 'text', text: `ナレッジグラフ構築完了:\n${JSON.stringify(graph, null, 2)}` }] };
  }

  async searchArticles({ query, articles }) {
    const results = articles.filter(article => 
      article.title.toLowerCase().includes(query.toLowerCase()) ||
      (article.content || '').toLowerCase().includes(query.toLowerCase())
    );
    
    return { content: [{ type: 'text', text: `検索結果: ${results.length}件\n${JSON.stringify(results.map(r => ({ title: r.title, url: r.url })), null, 2)}` }] };
  }

  async exportData({ articles, format = 'json' }) {
    const data = format === 'csv' 
      ? articles.map(a => `"${a.title}","${a.url}",${a.word_count || 0}`).join('\n')
      : JSON.stringify(articles, null, 2);
    
    return { content: [{ type: 'text', text: `エクスポート完了 (${format}):\n${data}` }] };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

// サーバー起動
if (require.main === module) {
  new UnifiedMCPServer().run().catch(console.error);
}

module.exports = UnifiedMCPServer;