import axios from 'axios';
import * as cheerio from 'cheerio';

export interface Article {
  id: string;
  title: string;
  url: string;
  date: string;
  categories: string[];
  summary: string;
  content?: string;
  images: Array<{
    url: string;
    alt: string;
    title: string;
  }>;
  links: Array<{
    url: string;
    text: string;
    isExternal: boolean;
  }>;
  wordCount: number;
}

export class HatenaArticleExtractor {
  private hatenaId: string = '';
  private blogDomain: string = '';
  private baseUrl: string = '';
  private axiosInstance = axios.create({
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    timeout: 30000
  });

  configure(hatenaId: string, blogDomain?: string) {
    this.hatenaId = hatenaId;
    this.blogDomain = blogDomain || `${hatenaId}.hatenablog.com`;
    this.baseUrl = `https://${this.blogDomain}`;
  }

  async extractAllArticles(maxPages?: number, extractFullContent: boolean = true): Promise<Article[]> {
    if (!this.hatenaId) {
      throw new Error('Hatena ID not configured. Call configure() first.');
    }

    const articles: Article[] = [];
    let page = 1;

    while (true) {
      if (maxPages && page > maxPages) {
        break;
      }

      try {
        const pageArticles = await this.extractPageArticles(page);
        if (pageArticles.length === 0) {
          break;
        }

        if (extractFullContent) {
          for (const article of pageArticles) {
            try {
              const fullContent = await this.extractArticleContent(article.url);
              article.content = fullContent.content;
              article.images = fullContent.images;
              article.links = fullContent.links;
              article.wordCount = fullContent.wordCount;
            } catch (error) {
              console.warn(`Failed to extract full content for ${article.url}:`, error);
            }
          }
        }

        articles.push(...pageArticles);
        page++;

        // Add delay to avoid rate limiting
        await this.delay(1000);
      } catch (error) {
        console.error(`Error extracting page ${page}:`, error);
        break;
      }
    }

    return articles;
  }

  private async extractPageArticles(page: number): Promise<Article[]> {
    const url = `${this.baseUrl}/archive?page=${page}`;
    
    try {
      const response = await this.axiosInstance.get(url);
      const $ = cheerio.load(response.data);
      const articles: Article[] = [];

      $('article.archive-entry').each((_, element) => {
        const article = this.parseArticleElement($, element);
        if (article) {
          articles.push(article);
        }
      });

      return articles;
    } catch (error) {
      throw new Error(`Failed to fetch page ${page}: ${error}`);
    }
  }

  private parseArticleElement($: cheerio.CheerioAPI, element: any): Article | null {
    try {
      const $article = $(element);
      
      const titleElement = $article.find('h1.entry-title a');
      if (titleElement.length === 0) {
        return null;
      }

      const title = titleElement.text().trim();
      const url = titleElement.attr('href');
      if (!url) {
        return null;
      }

      const dateElement = $article.find('time');
      const date = dateElement.attr('datetime') || '';

      const categories: string[] = [];
      $article.find('a.archive-category-link').each((_, catElement) => {
        categories.push($(catElement).text().trim());
      });

      const summaryElement = $article.find('p.entry-description');
      const summary = summaryElement.text().trim();

      // Generate ID from URL
      const id = this.generateArticleId(url);

      return {
        id,
        title,
        url,
        date,
        categories,
        summary,
        images: [],
        links: [],
        wordCount: 0
      };
    } catch (error) {
      console.warn('Error parsing article element:', error);
      return null;
    }
  }

  async extractArticleContent(articleUrl: string): Promise<{
    content: string;
    images: Array<{ url: string; alt: string; title: string }>;
    links: Array<{ url: string; text: string; isExternal: boolean }>;
    wordCount: number;
  }> {
    try {
      const response = await this.axiosInstance.get(articleUrl);
      const $ = cheerio.load(response.data);

      const contentElement = $('.entry-content');
      if (contentElement.length === 0) {
        throw new Error('Content element not found');
      }

      // Extract text content
      const textContent = contentElement.text().replace(/\s+/g, ' ').trim();

      // Extract images
      const images: Array<{ url: string; alt: string; title: string }> = [];
      contentElement.find('img').each((_, imgElement) => {
        const $img = $(imgElement);
        const src = $img.attr('src');
        if (src) {
          images.push({
            url: this.resolveUrl(src, articleUrl),
            alt: $img.attr('alt') || '',
            title: $img.attr('title') || ''
          });
        }
      });

      // Extract links
      const links: Array<{ url: string; text: string; isExternal: boolean }> = [];
      contentElement.find('a').each((_, linkElement) => {
        const $link = $(linkElement);
        const href = $link.attr('href');
        if (href && !href.startsWith('#')) {
          const resolvedUrl = this.resolveUrl(href, articleUrl);
          links.push({
            url: resolvedUrl,
            text: $link.text().trim(),
            isExternal: this.isExternalUrl(resolvedUrl)
          });
        }
      });

      return {
        content: textContent,
        images,
        links,
        wordCount: textContent.split(/\s+/).length
      };
    } catch (error) {
      throw new Error(`Failed to extract article content: ${error}`);
    }
  }

  private generateArticleId(url: string): string {
    // Extract article ID from URL or generate one
    const match = url.match(/\/entry\/(\d{4}\/\d{2}\/\d{2}\/\d+)/);
    if (match) {
      return match[1];
    }
    // Fallback: use URL hash
    return Buffer.from(url).toString('base64').slice(0, 12);
  }

  private resolveUrl(url: string, baseUrl: string): string {
    if (url.startsWith('http')) {
      return url;
    }
    if (url.startsWith('//')) {
      return `https:${url}`;
    }
    if (url.startsWith('/')) {
      const base = new URL(baseUrl);
      return `${base.protocol}//${base.host}${url}`;
    }
    return new URL(url, baseUrl).href;
  }

  private isExternalUrl(url: string): boolean {
    try {
      const urlObj = new URL(url);
      return !urlObj.hostname.endsWith('hatena.ne.jp') && 
             !urlObj.hostname.endsWith('hatenablog.com') &&
             !urlObj.hostname.endsWith(this.blogDomain);
    } catch {
      return false;
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}