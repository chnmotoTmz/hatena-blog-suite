/**
 * Multi-Blog Service - Integration with Python multi-blog manager
 * Bridges TypeScript MCP server with Python multi-blog functionality
 */

import { spawn } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export interface BlogConfig {
  name: string;
  hatena_id: string;
  blog_domain: string;
  description: string;
}

export interface Article {
  id: string;
  title: string;
  content: string;
  published: string;
  updated: string;
  url: string;
  categories: string[];
}

export interface ApiResponse<T = any> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
}

export class MultiBlogService {
  private pythonPath: string;

  constructor() {
    // Path to Python scripts (adjust as needed)
    this.pythonPath = join(__dirname, '../../');
  }

  /**
   * Execute Python command and return parsed result
   */
  private async executePythonCommand(command: string, args: string[] = []): Promise<any> {
    return new Promise((resolve, reject) => {
      const pythonScript = `
import sys
import os
import json
sys.path.append('${this.pythonPath}')

try:
    from enhanced_hatena_agent import EnhancedHatenaAgent
    agent = EnhancedHatenaAgent()
    
    command = '${command}'
    args = ${JSON.stringify(args)}
    
    if command == 'list_blogs':
        result = agent.list_blogs()
    elif command == 'test_authentication':
        blog_name = args[0] if args else None
        result = agent.test_blog_authentication(blog_name)
    elif command == 'get_articles':
        blog_name = args[0]
        limit = int(args[1]) if len(args) > 1 else 10
        result = agent.get_articles(blog_name, limit)
    elif command == 'search_articles':
        blog_name = args[0]
        search_term = args[1]
        result = agent.search_articles_by_title(blog_name, search_term)
    elif command == 'migrate_article':
        source_blog = args[0]
        target_blog = args[1] 
        article_id = args[2]
        copy_mode = args[3].lower() == 'true' if len(args) > 3 else True
        result = agent.migrate_article(source_blog, target_blog, article_id, copy_mode)
    else:
        result = {"status": "error", "message": f"Unknown command: {command}"}
    
    print(json.dumps(result, ensure_ascii=False))
    
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
`;

      const python = spawn('python3', ['-c', pythonScript], {
        cwd: this.pythonPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}: ${stderr}`));
          return;
        }

        try {
          const result = JSON.parse(stdout.trim());
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${stdout}`));
        }
      });

      python.on('error', (error) => {
        reject(new Error(`Failed to spawn Python process: ${error.message}`));
      });
    });
  }

  /**
   * List all configured blogs
   */
  async listBlogs(): Promise<ApiResponse<BlogConfig[]>> {
    try {
      const result = await this.executePythonCommand('list_blogs');
      return {
        status: 'success',
        data: result.status === 'success' ? result.blogs : []
      };
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Test authentication for blogs
   */
  async testAuthentication(blogName?: string): Promise<ApiResponse> {
    try {
      const result = await this.executePythonCommand('test_authentication', blogName ? [blogName] : []);
      return result;
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get articles from a specific blog
   */
  async getArticles(blogName: string, limit: number = 10): Promise<ApiResponse<Article[]>> {
    try {
      const result = await this.executePythonCommand('get_articles', [blogName, limit.toString()]);
      return {
        status: result.status === 'success' ? 'success' : 'error',
        message: result.message,
        data: result.status === 'success' ? result.articles : []
      };
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Search articles by title
   */
  async searchArticles(blogName: string, searchTerm: string): Promise<ApiResponse<Article[]>> {
    try {
      const result = await this.executePythonCommand('search_articles', [blogName, searchTerm]);
      return {
        status: result.status === 'success' ? 'success' : 'error',
        message: result.message,
        data: result.status === 'success' ? result.articles : []
      };
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Migrate article between blogs
   */
  async migrateArticle(
    sourceBlog: string,
    targetBlog: string,
    articleId: string,
    copyMode: boolean = true
  ): Promise<ApiResponse> {
    try {
      const result = await this.executePythonCommand('migrate_article', [
        sourceBlog,
        targetBlog,
        articleId,
        copyMode.toString()
      ]);
      return result;
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get migration candidates (articles suitable for migration)
   */
  async getMigrationCandidates(sourceBlog: string, categoryFilter?: string): Promise<ApiResponse<Article[]>> {
    try {
      // This would need to be implemented in the Python side
      const result = await this.getArticles(sourceBlog, 50);
      
      if (result.status === 'success' && result.data) {
        let candidates = result.data;
        
        // Filter by category if specified
        if (categoryFilter) {
          candidates = candidates.filter(article => 
            article.categories.some(cat => 
              cat.toLowerCase().includes(categoryFilter.toLowerCase())
            )
          );
        }
        
        // Filter by keywords that suggest outdoor/mountain content
        const outdoorKeywords = ['登山', '山', 'キャンプ', 'アウトドア', 'ハイキング', '釣り', '自然'];
        const outdoorCandidates = candidates.filter(article =>
          outdoorKeywords.some(keyword => 
            article.title.toLowerCase().includes(keyword.toLowerCase())
          )
        );
        
        return {
          status: 'success',
          data: outdoorCandidates
        };
      }
      
      return result;
    } catch (error) {
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}