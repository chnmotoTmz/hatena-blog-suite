import { GoogleGenerativeAI } from '@google/generative-ai';

export interface GeminiConfig {
  apiKey: string;
  model?: string;
}

export class GeminiService {
  private genAI: GoogleGenerativeAI;
  private model: string;

  constructor(config: GeminiConfig) {
    this.genAI = new GoogleGenerativeAI(config.apiKey);
    this.model = config.model || 'gemini-1.5-pro';
  }

  async generateEmbedding(text: string): Promise<number[]> {
    // Gemini doesn't have a direct embedding API like OpenAI
    // We'll use a text-to-vector approach or fallback to similarity matching
    try {
      const model = this.genAI.getGenerativeModel({ model: 'embedding-001' });
      const result = await model.embedContent(text);
      return result.embedding.values || [];
    } catch (error) {
      console.warn('Gemini embedding not available, using text similarity fallback');
      // Fallback: Convert text to simple numerical representation
      return this.textToSimpleVector(text);
    }
  }

  async generateText(prompt: string): Promise<string> {
    try {
      const model = this.genAI.getGenerativeModel({ model: this.model });
      const result = await model.generateContent(prompt);
      return result.response.text();
    } catch (error) {
      console.error('Gemini text generation error:', error);
      throw new Error(`Gemini API error: ${error.message}`);
    }
  }

  async summarizeArticles(articles: any[]): Promise<string> {
    const articlesText = articles.map(article => 
      `Title: ${article.title}\nContent: ${article.content?.substring(0, 500)}...`
    ).join('\n\n');

    const prompt = `以下の記事群を分析して、包括的な要約を日本語で作成してください：

${articlesText}

要約:`;

    return await this.generateText(prompt);
  }

  async findRelatedContent(query: string, articles: any[], maxResults: number = 5): Promise<any[]> {
    // Simple keyword-based similarity for Gemini compatibility
    const queryWords = query.toLowerCase().split(/\s+/);
    
    const scoredArticles = articles.map(article => {
      const content = (article.title + ' ' + (article.content || '')).toLowerCase();
      const score = queryWords.reduce((acc, word) => {
        const regex = new RegExp(word, 'gi');
        const matches = content.match(regex);
        return acc + (matches ? matches.length : 0);
      }, 0);
      
      return { ...article, relevanceScore: score };
    }).filter(article => article.relevanceScore > 0)
      .sort((a, b) => b.relevanceScore - a.relevanceScore)
      .slice(0, maxResults);

    return scoredArticles;
  }

  private textToSimpleVector(text: string): number[] {
    // Simple text-to-vector conversion for fallback
    const words = text.toLowerCase().split(/\s+/);
    const vector = new Array(100).fill(0);
    
    words.forEach((word, index) => {
      const hash = this.simpleHash(word);
      vector[hash % 100] += 1;
    });
    
    return vector;
  }

  private simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
}