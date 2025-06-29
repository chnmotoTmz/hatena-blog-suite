"""Multi-Blog Manager - Handles multiple Hatena blogs with authentication fix"""

import os
import requests
from xml.etree import ElementTree as ET
from datetime import datetime
import hashlib
import random
import base64
import logging
from typing import Dict, List, Optional, Tuple
from xml.sax.saxutils import escape
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BlogConfig:
    """Configuration for a Hatena blog"""
    hatena_id: str
    blog_domain: str
    api_key: str
    name: str  # Display name for the blog
    description: str = ""

class MultiBlogManager:
    """Manages multiple Hatena blogs with proper authentication"""
    
    def __init__(self):
        self.blogs: Dict[str, BlogConfig] = {}
        self._load_blog_configs()
    
    def _load_blog_configs(self):
        """Load blog configurations from environment variables"""
        # Primary blogs based on .env.example
        blog_configs = [
            {
                "name": "lifehack_blog",
                "hatena_id": "motochan1969", 
                "blog_domain": "motochan1969.hatenadiary.jp",
                "api_key_env": "HATENA_BLOG_ATOMPUB_KEY_1",
                "description": "ライフハックブログ"
            },
            {
                "name": "mountain_blog",
                "hatena_id": "motochan1969",
                "blog_domain": "arafo40tozan.hatenadiary.jp", 
                "api_key_env": "HATENA_BLOG_ATOMPUB_KEY_2",
                "description": "登山ブログ"
            },
            {
                "name": "tech_blog",
                "hatena_id": "motochan1969",
                "blog_domain": "motochan1969.hatenablog.com",
                "api_key_env": "HATENA_BLOG_ATOMPUB_KEY_1",
                "description": "技術ブログ"
            }
        ]
        
        for config in blog_configs:
            api_key = os.getenv(config["api_key_env"])
            if api_key:
                self.blogs[config["name"]] = BlogConfig(
                    hatena_id=config["hatena_id"],
                    blog_domain=config["blog_domain"],
                    api_key=api_key,
                    name=config["name"],
                    description=config["description"]
                )
                logger.info(f"Loaded blog config: {config['name']} ({config['blog_domain']})")
            else:
                logger.warning(f"API key not found for {config['name']}: {config['api_key_env']}")
    
    def list_blogs(self) -> List[Dict]:
        """List all configured blogs"""
        return [
            {
                "name": blog.name,
                "hatena_id": blog.hatena_id,
                "blog_domain": blog.blog_domain,
                "description": blog.description
            }
            for blog in self.blogs.values()
        ]
    
    def get_blog(self, blog_name: str) -> Optional[BlogConfig]:
        """Get blog configuration by name"""
        return self.blogs.get(blog_name)
    
    def _generate_wsse_header(self, hatena_id: str, api_key: str) -> str:
        """Generate WSSE authentication header (fixed implementation)"""
        nonce = hashlib.sha1(str(random.random()).encode()).digest()
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        password_digest = hashlib.sha1(nonce + now.encode() + api_key.encode()).digest()
        
        return f'UsernameToken Username="{hatena_id}", PasswordDigest="{base64.b64encode(password_digest).decode()}", Nonce="{base64.b64encode(nonce).decode()}", Created="{now}"'
    
    def _create_post_xml(self, title: str, content: str, hatena_id: str, is_draft: bool = False, categories: List[str] = None) -> bytes:
        """Create XML data for posting"""
        now = datetime.now()
        dtime = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Escape XML special characters
        escaped_title = escape(title)
        escaped_content = escape(content.strip())
        
        # Build category tags
        category_tags = ""
        if categories:
            category_tags = "\\n    ".join([f'<category term="{escape(cat)}" />' for cat in categories])
        else:
            category_tags = '<category term="tech" />'
        
        draft_status = 'yes' if is_draft else 'no'
        
        template = f'''<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{escaped_title}</title>
    <author><name>{escape(hatena_id)}</name></author>
    <content type="text/html">{escaped_content}</content>
    <updated>{dtime}</updated>
    {category_tags}
    <app:control>
        <app:draft>{draft_status}</app:draft>
    </app:control>
</entry>'''
        return template.encode('utf-8')
    
    def test_authentication(self, blog_name: str) -> Dict:
        """Test authentication for a specific blog"""
        blog = self.get_blog(blog_name)
        if not blog:
            return {"status": "error", "message": f"Blog '{blog_name}' not found"}
        
        headers = {
            'X-WSSE': self._generate_wsse_header(blog.hatena_id, blog.api_key),
            'Content-Type': 'application/atom+xml'
        }
        
        # Test with service document endpoint
        test_url = f'https://blog.hatena.ne.jp/{blog.hatena_id}/{blog.blog_domain}/atom'
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Authentication successful for {blog_name}")
            return {
                "status": "success",
                "blog_name": blog_name,
                "blog_domain": blog.blog_domain,
                "message": "Authentication successful"
            }
        except requests.RequestException as e:
            logger.error(f"Authentication failed for {blog_name}: {e}")
            return {
                "status": "error",
                "blog_name": blog_name,
                "message": f"Authentication failed: {str(e)}"
            }
    
    def get_articles(self, blog_name: str, page_url: Optional[str] = None) -> Dict:
        """Get articles from a specific blog"""
        blog = self.get_blog(blog_name)
        if not blog:
            return {"status": "error", "message": f"Blog '{blog_name}' not found"}
        
        if not page_url:
            page_url = f'https://blog.hatena.ne.jp/{blog.hatena_id}/{blog.blog_domain}/atom/entry'
        
        headers = {
            'X-WSSE': self._generate_wsse_header(blog.hatena_id, blog.api_key)
        }
        
        try:
            response = requests.get(page_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            articles = []
            for entry in root.findall('.//atom:entry', ns):
                entry_id = entry.find('atom:id', ns).text.split('-')[-1]
                title = entry.find('atom:title', ns).text or ""
                content = entry.find('atom:content', ns).text or ""
                published = entry.find('atom:published', ns).text
                updated = entry.find('atom:updated', ns).text
                
                link_elem = entry.find(".//atom:link[@rel='alternate']", ns)
                url = link_elem.get('href') if link_elem is not None else ""
                
                categories = [cat.get('term') for cat in entry.findall('atom:category', ns)]
                
                articles.append({
                    'id': entry_id,
                    'title': title,
                    'content': content,
                    'published': published,
                    'updated': updated,
                    'url': url,
                    'categories': categories
                })
            
            # Check for next page
            next_link = root.find(".//atom:link[@rel='next']", ns)
            next_page_url = next_link.get('href') if next_link is not None else None
            
            return {
                "status": "success",
                "blog_name": blog_name,
                "articles": articles,
                "next_page_url": next_page_url,
                "total_found": len(articles)
            }
            
        except Exception as e:
            logger.error(f"Failed to get articles from {blog_name}: {e}")
            return {
                "status": "error",
                "blog_name": blog_name,
                "message": str(e)
            }
    
    def post_article(self, blog_name: str, title: str, content: str, is_draft: bool = False, categories: List[str] = None) -> Dict:
        """Post article to a specific blog"""
        blog = self.get_blog(blog_name)
        if not blog:
            return {"status": "error", "message": f"Blog '{blog_name}' not found"}
        
        data = self._create_post_xml(title, content, blog.hatena_id, is_draft, categories)
        
        headers = {
            'X-WSSE': self._generate_wsse_header(blog.hatena_id, blog.api_key),
            'Content-Type': 'application/atom+xml; charset=utf-8'
        }
        
        collection_uri = f'https://blog.hatena.ne.jp/{blog.hatena_id}/{blog.blog_domain}/atom/entry'
        
        try:
            response = requests.post(collection_uri, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse response
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entry_id = root.find('.//atom:id', ns).text.split('-')[-1]
            entry_url = root.find(".//atom:link[@rel='alternate']", ns).get('href')
            
            logger.info(f"Successfully posted to {blog_name}: {title}")
            return {
                "status": "success",
                "blog_name": blog_name,
                "entry_id": entry_id,
                "url": entry_url,
                "title": title
            }
        except Exception as e:
            logger.error(f"Failed to post to {blog_name}: {e}")
            return {
                "status": "error",
                "blog_name": blog_name,
                "message": str(e),
                "title": title
            }
    
    def migrate_article(self, source_blog: str, target_blog: str, article_id: str, 
                       copy_mode: bool = True, add_migration_note: bool = True) -> Dict:
        """Migrate an article from source blog to target blog"""
        # Get the article from source blog
        source_config = self.get_blog(source_blog)
        if not source_config:
            return {"status": "error", "message": f"Source blog '{source_blog}' not found"}
        
        target_config = self.get_blog(target_blog)
        if not target_config:
            return {"status": "error", "message": f"Target blog '{target_blog}' not found"}
        
        # Fetch the article
        headers = {
            'X-WSSE': self._generate_wsse_header(source_config.hatena_id, source_config.api_key)
        }
        
        article_url = f'https://blog.hatena.ne.jp/{source_config.hatena_id}/{source_config.blog_domain}/atom/entry/{article_id}'
        
        try:
            response = requests.get(article_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            title = root.find('.//atom:title', ns).text or ""
            content = root.find('.//atom:content', ns).text or ""
            categories = [cat.get('term') for cat in root.findall('atom:category', ns)]
            
            # Add migration note if requested
            if add_migration_note:
                migration_note = f"\\n\\n<p><small>※ この記事は{source_config.description}から移行されました</small></p>"
                content += migration_note
            
            # Post to target blog
            result = self.post_article(target_blog, title, content, is_draft=True, categories=categories)
            
            if result["status"] == "success":
                result["migration_info"] = {
                    "source_blog": source_blog,
                    "target_blog": target_blog,
                    "original_article_id": article_id,
                    "copy_mode": copy_mode
                }
                
                # If move mode, could add logic to delete from source blog
                if not copy_mode:
                    result["migration_info"]["note"] = "Move mode - consider deleting source article manually"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to migrate article {article_id}: {e}")
            return {
                "status": "error",
                "message": f"Migration failed: {str(e)}"
            }

# Global instance
multi_blog_manager = MultiBlogManager()