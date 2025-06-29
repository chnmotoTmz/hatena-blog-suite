import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import json
import re
from urllib.parse import urljoin, urlparse


class HatenaArticleExtractor:
    def __init__(self, hatena_id: str, blog_domain: Optional[str] = None):
        self.hatena_id = hatena_id
        self.blog_domain = blog_domain or f"{hatena_id}.hatenablog.com"
        self.base_url = f"https://{self.blog_domain}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_all_articles(self, max_pages: Optional[int] = None) -> List[Dict]:
        articles = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            page_articles = self._extract_page_articles(page)
            if not page_articles:
                break
                
            articles.extend(page_articles)
            page += 1
            
        return articles
    
    def _extract_page_articles(self, page: int) -> List[Dict]:
        url = f"{self.base_url}/archive?page={page}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        for article_elem in soup.find_all('article', class_='archive-entry'):
            article_data = self._parse_article_element(article_elem)
            if article_data:
                articles.append(article_data)
        
        return articles
    
    def _parse_article_element(self, article_elem) -> Optional[Dict]:
        try:
            title_elem = article_elem.find('h1', class_='entry-title')
            if not title_elem or not title_elem.find('a'):
                return None
                
            title = title_elem.get_text(strip=True)
            url = title_elem.find('a')['href']
            
            date_elem = article_elem.find('time')
            date = date_elem['datetime'] if date_elem else None
            
            categories = []
            category_elems = article_elem.find_all('a', class_='archive-category-link')
            for cat_elem in category_elems:
                categories.append(cat_elem.get_text(strip=True))
            
            summary_elem = article_elem.find('p', class_='entry-description')
            summary = summary_elem.get_text(strip=True) if summary_elem else ''
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'categories': categories,
                'summary': summary,
                'full_content': None
            }
        except Exception as e:
            print(f"Error parsing article element: {e}")
            return None
    
    def extract_article_content(self, article_url: str) -> Dict:
        try:
            response = self.session.get(article_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article: {e}")
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_elem = soup.find('div', class_='entry-content')
        if not content_elem:
            return {}
        
        text_content = content_elem.get_text(separator='\n', strip=True)
        
        images = []
        for img in content_elem.find_all('img'):
            img_url = img.get('src', '')
            if img_url:
                images.append({
                    'url': urljoin(article_url, img_url),
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        
        links = []
        for link in content_elem.find_all('a'):
            href = link.get('href', '')
            if href and not href.startswith('#'):
                links.append({
                    'url': urljoin(article_url, href),
                    'text': link.get_text(strip=True),
                    'is_external': not urlparse(href).netloc.endswith('hatena.ne.jp')
                })
        
        return {
            'content': text_content,
            'images': images,
            'links': links,
            'word_count': len(text_content.split())
        }
    
    def save_articles_to_json(self, articles: List[Dict], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    
    def load_articles_from_json(self, filename: str) -> List[Dict]:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)