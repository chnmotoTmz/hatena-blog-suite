import sqlite3 from 'sqlite3';
import { open, Database } from 'sqlite';
import { Article } from '../extractors/article-extractor.js';

export interface SearchOptions {
  query?: string;
  tags?: string[];
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
}

export class ArticleDatabase {
  private db: Database | null = null;
  private dbPath: string;

  constructor(dbPath: string = './articles.db') {
    this.dbPath = dbPath;
  }

  async initialize(): Promise<void> {
    this.db = await open({
      filename: this.dbPath,
      driver: sqlite3.Database
    });

    await this.createTables();
  }

  private async createTables(): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS articles (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        date TEXT,
        categories TEXT,
        summary TEXT,
        content TEXT,
        word_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS article_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id TEXT,
        url TEXT,
        alt TEXT,
        title TEXT,
        FOREIGN KEY (article_id) REFERENCES articles (id)
      );

      CREATE TABLE IF NOT EXISTS article_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id TEXT,
        url TEXT,
        text TEXT,
        is_external BOOLEAN,
        FOREIGN KEY (article_id) REFERENCES articles (id)
      );

      CREATE INDEX IF NOT EXISTS idx_articles_date ON articles (date);
      CREATE INDEX IF NOT EXISTS idx_articles_title ON articles (title);
      CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
        title, content, summary, categories, content=articles
      );
    `);
  }

  async saveArticles(articles: Article[]): Promise<void> {
    if (!this.db) await this.initialize();
    
    const insertArticle = await this.db!.prepare(`
      INSERT OR REPLACE INTO articles 
      (id, title, url, date, categories, summary, content, word_count, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    `);

    const insertImage = await this.db!.prepare(`
      INSERT INTO article_images (article_id, url, alt, title)
      VALUES (?, ?, ?, ?)
    `);

    const insertLink = await this.db!.prepare(`
      INSERT INTO article_links (article_id, url, text, is_external)
      VALUES (?, ?, ?, ?)
    `);

    try {
      await this.db!.exec('BEGIN TRANSACTION');

      for (const article of articles) {
        // Save article
        await insertArticle.run(
          article.id,
          article.title,
          article.url,
          article.date,
          JSON.stringify(article.categories),
          article.summary,
          article.content || '',
          article.wordCount
        );

        // Clear existing images and links
        await this.db!.run('DELETE FROM article_images WHERE article_id = ?', article.id);
        await this.db!.run('DELETE FROM article_links WHERE article_id = ?', article.id);

        // Save images
        for (const image of article.images) {
          await insertImage.run(article.id, image.url, image.alt, image.title);
        }

        // Save links
        for (const link of article.links) {
          await insertLink.run(article.id, link.url, link.text, link.isExternal);
        }

        // Update FTS index
        await this.db!.run(`
          INSERT OR REPLACE INTO articles_fts 
          (rowid, title, content, summary, categories)
          SELECT rowid, title, content, summary, categories 
          FROM articles WHERE id = ?
        `, article.id);
      }

      await this.db!.exec('COMMIT');
    } catch (error) {
      await this.db!.exec('ROLLBACK');
      throw error;
    } finally {
      await insertArticle.finalize();
      await insertImage.finalize();
      await insertLink.finalize();
    }
  }

  async searchArticles(options: SearchOptions): Promise<Article[]> {
    if (!this.db) await this.initialize();

    let query = `
      SELECT DISTINCT a.*, 
        GROUP_CONCAT(DISTINCT ai.url || '|' || ai.alt || '|' || ai.title, ';;;') as images_data,
        GROUP_CONCAT(DISTINCT al.url || '|' || al.text || '|' || al.is_external, ';;;') as links_data
      FROM articles a
      LEFT JOIN article_images ai ON a.id = ai.article_id
      LEFT JOIN article_links al ON a.id = al.article_id
    `;

    const conditions: string[] = [];
    const params: any[] = [];

    if (options.query) {
      query = `
        SELECT DISTINCT a.*, 
          GROUP_CONCAT(DISTINCT ai.url || '|' || ai.alt || '|' || ai.title, ';;;') as images_data,
          GROUP_CONCAT(DISTINCT al.url || '|' || al.text || '|' || al.is_external, ';;;') as links_data
        FROM articles_fts fts
        JOIN articles a ON a.rowid = fts.rowid
        LEFT JOIN article_images ai ON a.id = ai.article_id
        LEFT JOIN article_links al ON a.id = al.article_id
        WHERE articles_fts MATCH ?
      `;
      params.push(options.query);
    }

    if (options.tags && options.tags.length > 0) {
      const tagConditions = options.tags.map(() => 'categories LIKE ?').join(' OR ');
      conditions.push(`(${tagConditions})`);
      options.tags.forEach(tag => params.push(`%"${tag}"%`));
    }

    if (options.dateFrom) {
      conditions.push('date >= ?');
      params.push(options.dateFrom);
    }

    if (options.dateTo) {
      conditions.push('date <= ?');
      params.push(options.dateTo);
    }

    if (conditions.length > 0) {
      if (options.query) {
        query += ' AND ' + conditions.join(' AND ');
      } else {
        query += ' WHERE ' + conditions.join(' AND ');
      }
    }

    query += ' GROUP BY a.id ORDER BY a.date DESC';

    if (options.limit) {
      query += ' LIMIT ?';
      params.push(options.limit);
    }

    const rows = await this.db!.all(query, params);
    return rows.map(row => this.rowToArticle(row));
  }

  async getArticleById(articleId: string): Promise<Article | null> {
    if (!this.db) await this.initialize();

    const query = `
      SELECT a.*, 
        GROUP_CONCAT(DISTINCT ai.url || '|' || ai.alt || '|' || ai.title, ';;;') as images_data,
        GROUP_CONCAT(DISTINCT al.url || '|' || al.text || '|' || al.is_external, ';;;') as links_data
      FROM articles a
      LEFT JOIN article_images ai ON a.id = ai.article_id
      LEFT JOIN article_links al ON a.id = al.article_id
      WHERE a.id = ? OR a.url = ?
      GROUP BY a.id
    `;

    const row = await this.db!.get(query, [articleId, articleId]);
    return row ? this.rowToArticle(row) : null;
  }

  async getAllArticles(): Promise<Article[]> {
    if (!this.db) await this.initialize();

    const query = `
      SELECT a.*, 
        GROUP_CONCAT(DISTINCT ai.url || '|' || ai.alt || '|' || ai.title, ';;;') as images_data,
        GROUP_CONCAT(DISTINCT al.url || '|' || al.text || '|' || al.is_external, ';;;') as links_data
      FROM articles a
      LEFT JOIN article_images ai ON a.id = ai.article_id
      LEFT JOIN article_links al ON a.id = al.article_id
      GROUP BY a.id
      ORDER BY a.date DESC
    `;

    const rows = await this.db!.all(query);
    return rows.map(row => this.rowToArticle(row));
  }

  private rowToArticle(row: any): Article {
    const images = row.images_data ? 
      row.images_data.split(';;;')
        .filter((item: string) => item.trim())
        .map((item: string) => {
          const [url, alt, title] = item.split('|');
          return { url: url || '', alt: alt || '', title: title || '' };
        }) : [];

    const links = row.links_data ?
      row.links_data.split(';;;')
        .filter((item: string) => item.trim())
        .map((item: string) => {
          const [url, text, isExternal] = item.split('|');
          return { 
            url: url || '', 
            text: text || '', 
            isExternal: isExternal === 'true' || isExternal === '1'
          };
        }) : [];

    return {
      id: row.id,
      title: row.title,
      url: row.url,
      date: row.date,
      categories: row.categories ? JSON.parse(row.categories) : [],
      summary: row.summary || '',
      content: row.content || '',
      images,
      links,
      wordCount: row.word_count || 0
    };
  }

  async close(): Promise<void> {
    if (this.db) {
      await this.db.close();
      this.db = null;
    }
  }
}