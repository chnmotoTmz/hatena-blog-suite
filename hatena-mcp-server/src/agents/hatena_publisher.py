"""Hatena Blog Publisher - API posting functionality"""

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

logger = logging.getLogger(__name__)


class HatenaPublisher:
    """Handles publishing articles to Hatena Blog via AtomPub API"""
    
    def __init__(self, hatena_id: str, blog_domain: str, api_key: Optional[str] = None):
        self.hatena_id = hatena_id
        self.blog_domain = blog_domain
        self.api_key = api_key or self._load_api_key()
        
    def _load_api_key(self) -> str:
        """Load API key from environment"""
        env_key = f"HATENA_BLOG_ATOMPUB_KEY_{self.hatena_id}"
        api_key = os.getenv(env_key)
        if not api_key:
            # Try fallback keys
            api_key = os.getenv("HATENA_BLOG_ATOMPUB_KEY_1") or os.getenv("HATENA_BLOG_ATOMPUB_KEY_motochan1969")
        if not api_key:
            raise ValueError(f"API key for {self.hatena_id} not found in environment")
        return api_key
    
    def _generate_wsse_header(self) -> str:
        """Generate WSSE authentication header"""
        nonce = hashlib.sha1(str(random.random()).encode()).digest()
        now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        password_digest = hashlib.sha1(nonce + now.encode() + self.api_key.encode()).digest()
        
        return f'UsernameToken Username="{self.hatena_id}", PasswordDigest="{base64.b64encode(password_digest).decode()}", Nonce="{base64.b64encode(nonce).decode()}", Created="{now}"'
    
    def _create_post_xml(self, title: str, content: str, is_draft: bool = False, categories: List[str] = None) -> bytes:
        """Create XML data for posting"""
        now = datetime.now()
        dtime = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Escape XML special characters in title and content
        escaped_title = escape(title)
        escaped_content = escape(content.strip())
        
        # Build category tags with escaped terms
        category_tags = ""
        if categories:
            category_tags = "\n    ".join([f'<category term="{escape(cat)}" />' for cat in categories])
        else:
            category_tags = '<category term="tech" />'
        
        draft_status = 'yes' if is_draft else 'no'
        
        template = f'''<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{escaped_title}</title>
    <author><name>{escape(self.hatena_id)}</name></author>
    <content type="text/html">{escaped_content}</content>
    <updated>{dtime}</updated>
    {category_tags}
    <app:control>
        <app:draft>{draft_status}</app:draft>
    </app:control>
</entry>'''
        return template.encode('utf-8')
    
    def post_article(self, title: str, content: str, is_draft: bool = False, categories: List[str] = None) -> Dict:
        """Post a new article to Hatena Blog"""
        data = self._create_post_xml(title, content, is_draft, categories)
        
        headers = {
            'X-WSSE': self._generate_wsse_header(),
            'Content-Type': 'application/x.atom+xml'
        }
        
        collection_uri = f'https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_domain}/atom/entry'
        
        try:
            response = requests.post(collection_uri, data=data, headers=headers)
            response.raise_for_status()
            
            # Parse response
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entry_id = root.find('.//atom:id', ns).text.split('-')[-1]
            entry_url = root.find(".//atom:link[@rel='alternate']", ns).get('href')
            
            logger.info(f"Successfully posted: {title}")
            return {
                "status": "success",
                "entry_id": entry_id,
                "url": entry_url,
                "title": title
            }
        except Exception as e:
            logger.error(f"Failed to post article: {e}")
            return {
                "status": "error",
                "message": str(e),
                "title": title
            }
    
    def update_article(self, entry_id: str, title: str, content: str, is_draft: bool = False, categories: List[str] = None) -> Dict:
        """Update an existing article"""
        data = self._create_post_xml(title, content, is_draft, categories)
        
        headers = {
            'X-WSSE': self._generate_wsse_header(),
            'Content-Type': 'application/x.atom+xml'
        }
        
        member_uri = f'https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_domain}/atom/entry/{entry_id}'
        
        try:
            response = requests.put(member_uri, data=data, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully updated entry: {entry_id}")
            return {
                "status": "success",
                "entry_id": entry_id,
                "title": title
            }
        except Exception as e:
            logger.error(f"Failed to update article: {e}")
            return {
                "status": "error",
                "message": str(e),
                "entry_id": entry_id
            }
    
    def get_entries(self, page_url: Optional[str] = None) -> Dict:
        """Get list of blog entries"""
        if not page_url:
            page_url = f'https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_domain}/atom/entry'
        
        headers = {'X-WSSE': self._generate_wsse_header()}
        
        try:
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries_data = []
            for entry in root.findall('.//atom:entry', ns):
                entry_id = entry.find('atom:id', ns).text.split('-')[-1]
                title = entry.find('atom:title', ns).text
                content = entry.find('atom:content', ns).text or ""
                published = entry.find('atom:published', ns).text
                updated = entry.find('atom:updated', ns).text
                
                link_elem = entry.find(".//atom:link[@rel='alternate']", ns)
                url = link_elem.get('href') if link_elem is not None else ""
                
                categories = [cat.get('term') for cat in entry.findall('atom:category', ns)]
                
                entries_data.append({
                    'id': entry_id,
                    'title': title,
                    'content': content[:200] + "..." if len(content) > 200 else content,
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
                "entries": entries_data,
                "next_page_url": next_page_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get entries: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def publish_repost(self, repost_content: Dict, is_draft: bool = True) -> Dict:
        """Publish a repost based on repost_content dictionary"""
        title = repost_content.get('title', '')
        content = repost_content.get('content', '')
        categories = repost_content.get('categories', [])
        
        # Log content details for debugging
        logger.debug(f"Publishing repost - Title: {title}")
        logger.debug(f"Content length: {len(content)} characters")
        logger.debug(f"Content preview: {content[:200]}..." if content else "No content")
        
        # Validate content
        if not content or not content.strip():
            logger.error("No content provided for repost")
            return {
                "status": "error",
                "message": "No content provided for repost",
                "title": title
            }
        
        # Always add '再掲載' category if not present
        if '再掲載' not in categories:
            categories.append('再掲載')
        
        return self.post_article(title, content, is_draft, categories)