"""Enhanced Hatena Agent with Multi-Blog Support and Article Migration"""

import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Import our multi-blog manager
from multi_blog_manager import multi_blog_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EnhancedHatenaAgent:
    """Enhanced Hatena Agent with multi-blog support and migration features"""
    
    def __init__(self):
        self.manager = multi_blog_manager
        logger.info("Enhanced Hatena Agent initialized")
    
    def list_blogs(self) -> Dict:
        """List all configured blogs"""
        try:
            blogs = self.manager.list_blogs()
            return {
                "status": "success",
                "blogs": blogs,
                "count": len(blogs)
            }
        except Exception as e:
            logger.error(f"Error listing blogs: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_blog_authentication(self, blog_name: str = None) -> Dict:
        """Test authentication for one or all blogs"""
        try:
            if blog_name:
                return self.manager.test_authentication(blog_name)
            else:
                # Test all blogs
                results = {}
                for blog_name in self.manager.blogs.keys():
                    results[blog_name] = self.manager.test_authentication(blog_name)
                return {
                    "status": "success",
                    "results": results
                }
        except Exception as e:
            logger.error(f"Error testing authentication: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_articles(self, blog_name: str, limit: int = 10) -> Dict:
        """Get articles from a specific blog"""
        try:
            result = self.manager.get_articles(blog_name)
            if result["status"] == "success" and limit:
                result["articles"] = result["articles"][:limit]
            return result
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            return {"status": "error", "message": str(e)}
    
    def post_article(self, blog_name: str, title: str, content: str, 
                    is_draft: bool = True, categories: List[str] = None) -> Dict:
        """Post article to a specific blog"""
        try:
            if not title or not content:
                return {"status": "error", "message": "Title and content are required"}
            
            return self.manager.post_article(blog_name, title, content, is_draft, categories)
        except Exception as e:
            logger.error(f"Error posting article: {e}")
            return {"status": "error", "message": str(e)}
    
    def migrate_article(self, source_blog: str, target_blog: str, article_id: str,
                       copy_mode: bool = True) -> Dict:
        """Migrate article from one blog to another"""
        try:
            if source_blog == target_blog:
                return {"status": "error", "message": "Source and target blogs cannot be the same"}
            
            return self.manager.migrate_article(source_blog, target_blog, article_id, copy_mode)
        except Exception as e:
            logger.error(f"Error migrating article: {e}")
            return {"status": "error", "message": str(e)}
    
    def search_articles_by_title(self, blog_name: str, search_term: str) -> Dict:
        """Search articles by title in a specific blog"""
        try:
            result = self.manager.get_articles(blog_name)
            if result["status"] != "success":
                return result
            
            matching_articles = [
                article for article in result["articles"]
                if search_term.lower() in article["title"].lower()
            ]
            
            return {
                "status": "success",
                "blog_name": blog_name,
                "search_term": search_term,
                "articles": matching_articles,
                "found_count": len(matching_articles)
            }
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_migration_candidates(self, source_blog: str, category_filter: str = None) -> Dict:
        """Get articles that are candidates for migration"""
        try:
            result = self.manager.get_articles(source_blog)
            if result["status"] != "success":
                return result
            
            candidates = result["articles"]
            
            # Filter by category if specified
            if category_filter:
                candidates = [
                    article for article in candidates
                    if category_filter.lower() in [cat.lower() for cat in article.get("categories", [])]
                ]
            
            return {
                "status": "success",
                "source_blog": source_blog,
                "category_filter": category_filter,
                "candidates": candidates,
                "candidate_count": len(candidates)
            }
        except Exception as e:
            logger.error(f"Error getting migration candidates: {e}")
            return {"status": "error", "message": str(e)}
    
    def batch_migrate_articles(self, source_blog: str, target_blog: str, 
                             article_ids: List[str], copy_mode: bool = True) -> Dict:
        """Migrate multiple articles at once"""
        try:
            results = []
            success_count = 0
            error_count = 0
            
            for article_id in article_ids:
                result = self.migrate_article(source_blog, target_blog, article_id, copy_mode)
                results.append({
                    "article_id": article_id,
                    "result": result
                })
                
                if result["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1
            
            return {
                "status": "success",
                "source_blog": source_blog,
                "target_blog": target_blog,
                "total_attempted": len(article_ids),
                "successful": success_count,
                "failed": error_count,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error in batch migration: {e}")
            return {"status": "error", "message": str(e)}

# Tool functions for ADK integration
def list_blogs_tool() -> Dict:
    """Tool: List all configured blogs"""
    agent = EnhancedHatenaAgent()
    return agent.list_blogs()

def test_authentication_tool(blog_name: str = None) -> Dict:
    """Tool: Test blog authentication"""
    agent = EnhancedHatenaAgent()
    return agent.test_blog_authentication(blog_name)

def get_articles_tool(blog_name: str, limit: int = 10) -> Dict:
    """Tool: Get articles from a blog"""
    agent = EnhancedHatenaAgent()
    return agent.get_articles(blog_name, limit)

def post_article_tool(blog_name: str, title: str, content: str, 
                     is_draft: bool = True, categories: str = None) -> Dict:
    """Tool: Post article to a blog"""
    agent = EnhancedHatenaAgent()
    category_list = categories.split(",") if categories else None
    return agent.post_article(blog_name, title, content, is_draft, category_list)

def migrate_article_tool(source_blog: str, target_blog: str, article_id: str,
                        copy_mode: bool = True) -> Dict:
    """Tool: Migrate article between blogs"""
    agent = EnhancedHatenaAgent()
    return agent.migrate_article(source_blog, target_blog, article_id, copy_mode)

def search_articles_tool(blog_name: str, search_term: str) -> Dict:
    """Tool: Search articles by title"""
    agent = EnhancedHatenaAgent()
    return agent.search_articles_by_title(blog_name, search_term)

def get_migration_candidates_tool(source_blog: str, category_filter: str = None) -> Dict:
    """Tool: Get articles suitable for migration"""
    agent = EnhancedHatenaAgent()
    return agent.get_migration_candidates(source_blog, category_filter)

# Command line interface
def main():
    """Main CLI interface"""
    agent = EnhancedHatenaAgent()
    
    print("🎌 Enhanced Hatena Blog Agent")
    print("=" * 50)
    
    # Test authentication on startup
    print("\\n🔐 Testing authentication...")
    auth_results = agent.test_blog_authentication()
    if auth_results["status"] == "success":
        for blog_name, result in auth_results["results"].items():
            status = "✅" if result["status"] == "success" else "❌"
            print(f"{status} {blog_name}: {result.get('message', 'Unknown status')}")
    
    # List available blogs
    print("\\n📚 Available blogs:")
    blog_list = agent.list_blogs()
    if blog_list["status"] == "success":
        for blog in blog_list["blogs"]:
            print(f"  • {blog['name']}: {blog['description']} ({blog['blog_domain']})")
    
    print("\\n💡 Example commands:")
    print("  agent.get_articles('lifehack_blog', limit=5)")
    print("  agent.migrate_article('lifehack_blog', 'mountain_blog', 'article_id')")
    print("  agent.search_articles_by_title('lifehack_blog', 'キャンプ')")
    
    return agent

if __name__ == "__main__":
    main()