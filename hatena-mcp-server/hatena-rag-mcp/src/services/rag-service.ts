import { OpenAI } from 'openai';
import { ArticleDatabase } from '../database/article-db.js';
import { Article } from '../extractors/article-extractor.js';

export interface RelatedArticle {
  article: Article;
  score: number;
  reason: string;
}

export class HatenaRAGService {
  private openai: OpenAI | null = null;
  private database: ArticleDatabase;

  constructor(database: ArticleDatabase) {
    this.database = database;
    
    // Initialize OpenAI if API key is available
    const apiKey = process.env.OPENAI_API_KEY;
    if (apiKey) {
      this.openai = new OpenAI({ apiKey });
    }
  }

  async findRelatedArticles(
    query: string,
    similarityThreshold: number = 0.7,
    maxResults: number = 5
  ): Promise<RelatedArticle[]> {
    // First, try semantic similarity if OpenAI is available
    if (this.openai) {
      try {
        return await this.findSemanticallySimilarArticles(query, similarityThreshold, maxResults);
      } catch (error) {
        console.warn('Semantic search failed, falling back to keyword search:', error);
      }
    }

    // Fallback to keyword-based search
    return await this.findKeywordBasedRelatedArticles(query, maxResults);
  }

  private async findSemanticallySimilarArticles(
    query: string,
    similarityThreshold: number,
    maxResults: number
  ): Promise<RelatedArticle[]> {
    if (!this.openai) {
      throw new Error('OpenAI not initialized');
    }

    // Get embedding for the query
    const queryEmbedding = await this.getEmbedding(query);
    
    // Get all articles
    const articles = await this.database.getAllArticles();
    
    // Calculate similarities
    const similarities: RelatedArticle[] = [];
    
    for (const article of articles) {
      try {
        const articleText = this.getArticleText(article);
        const articleEmbedding = await this.getEmbedding(articleText);
        
        const similarity = this.cosineSimilarity(queryEmbedding, articleEmbedding);
        
        if (similarity >= similarityThreshold) {
          similarities.push({
            article,
            score: similarity,
            reason: `セマンティック類似度: ${(similarity * 100).toFixed(1)}%`
          });
        }
      } catch (error) {
        console.warn(`Error processing article ${article.id}:`, error);
      }
    }

    // Sort by similarity score and return top results
    return similarities
      .sort((a, b) => b.score - a.score)
      .slice(0, maxResults);
  }

  private async findKeywordBasedRelatedArticles(
    query: string,
    maxResults: number
  ): Promise<RelatedArticle[]> {
    // Extract keywords from query
    const keywords = this.extractKeywords(query);
    
    // Search using database full-text search
    const searchResults = await this.database.searchArticles({
      query: keywords.join(' '),
      limit: maxResults * 2 // Get more results to filter
    });

    // Calculate relevance scores based on keyword matches
    const scoredResults: RelatedArticle[] = [];
    
    for (const article of searchResults) {
      const score = this.calculateKeywordScore(article, keywords);
      if (score > 0) {
        scoredResults.push({
          article,
          score,
          reason: `キーワードマッチング: ${this.getMatchingKeywords(article, keywords).join(', ')}`
        });
      }
    }

    return scoredResults
      .sort((a, b) => b.score - a.score)
      .slice(0, maxResults);
  }

  private async getEmbedding(text: string): Promise<number[]> {
    if (!this.openai) {
      throw new Error('OpenAI not initialized');
    }

    // Truncate text if too long
    const maxTokens = 8000;
    const truncatedText = text.length > maxTokens * 4 ? 
      text.substring(0, maxTokens * 4) : text;

    const response = await this.openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: truncatedText,
    });

    return response.data[0].embedding;
  }

  private cosineSimilarity(vecA: number[], vecB: number[]): number {
    if (vecA.length !== vecB.length) {
      throw new Error('Vectors must have the same length');
    }

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < vecA.length; i++) {
      dotProduct += vecA[i] * vecB[i];
      normA += vecA[i] * vecA[i];
      normB += vecB[i] * vecB[i];
    }

    normA = Math.sqrt(normA);
    normB = Math.sqrt(normB);

    if (normA === 0 || normB === 0) {
      return 0;
    }

    return dotProduct / (normA * normB);
  }

  private getArticleText(article: Article): string {
    return `${article.title}\n\n${article.content || article.summary}`;
  }

  private extractKeywords(query: string): string[] {
    // Simple keyword extraction - can be enhanced with NLP libraries
    return query
      .toLowerCase()
      .replace(/[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 1)
      .slice(0, 10); // Limit to top 10 keywords
  }

  private calculateKeywordScore(article: Article, keywords: string[]): number {
    const text = this.getArticleText(article).toLowerCase();
    let score = 0;

    for (const keyword of keywords) {
      const regex = new RegExp(keyword, 'gi');
      const matches = text.match(regex);
      if (matches) {
        // Score based on frequency and position (title matches score higher)
        const titleMatches = article.title.toLowerCase().match(regex);
        score += matches.length * (titleMatches ? 3 : 1);
      }
    }

    return score / keywords.length; // Normalize by number of keywords
  }

  private getMatchingKeywords(article: Article, keywords: string[]): string[] {
    const text = this.getArticleText(article).toLowerCase();
    return keywords.filter(keyword => 
      text.includes(keyword.toLowerCase())
    );
  }

  async generateSummary(articleIds: string[], summaryType: 'brief' | 'detailed' | 'outline'): Promise<string> {
    const articles: Article[] = [];
    
    for (const id of articleIds) {
      const article = await this.database.getArticleById(id);
      if (article) {
        articles.push(article);
      }
    }

    if (articles.length === 0) {
      return '指定された記事が見つかりませんでした。';
    }

    if (!this.openai) {
      return this.generateSimpleSummary(articles, summaryType);
    }

    try {
      return await this.generateAISummary(articles, summaryType);
    } catch (error) {
      console.warn('AI summary generation failed, using simple summary:', error);
      return this.generateSimpleSummary(articles, summaryType);
    }
  }

  private async generateAISummary(articles: Article[], summaryType: string): Promise<string> {
    if (!this.openai) {
      throw new Error('OpenAI not initialized');
    }

    const articlesText = articles.map(article => 
      `タイトル: ${article.title}\n日付: ${article.date}\nURL: ${article.url}\n内容: ${article.content || article.summary}`
    ).join('\n\n---\n\n');

    let prompt = '';
    switch (summaryType) {
      case 'brief':
        prompt = '以下の記事群を簡潔に要約してください（200文字以内）：\n\n';
        break;
      case 'detailed':
        prompt = '以下の記事群の詳細な要約を作成してください（各記事の主要ポイントを含む）：\n\n';
        break;
      case 'outline':
        prompt = '以下の記事群のアウトライン形式の要約を作成してください（箇条書き形式）：\n\n';
        break;
    }

    const response = await this.openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'user',
          content: prompt + articlesText
        }
      ],
      max_tokens: summaryType === 'brief' ? 300 : 1000,
      temperature: 0.7
    });

    return response.choices[0]?.message?.content || '要約の生成に失敗しました。';
  }

  private generateSimpleSummary(articles: Article[], summaryType: string): string {
    const titles = articles.map(article => `• ${article.title}`).join('\n');
    const dateRange = this.getDateRange(articles);
    
    let summary = `記事数: ${articles.length}件\n期間: ${dateRange}\n\n記事一覧:\n${titles}`;
    
    if (summaryType === 'detailed') {
      summary += '\n\n各記事の概要:\n';
      articles.forEach((article, index) => {
        summary += `${index + 1}. ${article.title}\n   ${article.summary}\n   ${article.url}\n\n`;
      });
    }
    
    return summary;
  }

  private getDateRange(articles: Article[]): string {
    const dates = articles
      .map(article => article.date)
      .filter(date => date)
      .sort();
    
    if (dates.length === 0) {
      return '不明';
    }
    
    if (dates.length === 1) {
      return dates[0];
    }
    
    return `${dates[0]} ～ ${dates[dates.length - 1]}`;
  }
}