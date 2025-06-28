#!/usr/bin/env python3
"""
Minimal Hatena Blog Client - 軽量版
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict


class HatenaClient:
    def __init__(self, blog_id: str):
        self.blog_id = blog_id
        self.base_url = f"https://{blog_id}.hatenablog.com"
        self.session = requests.Session()
    
    def get_articles(self, max_count: int = 10) -> List[Dict]:
        """記事一覧を取得（軽量版）"""
        url = f"{self.base_url}/archive"
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        links = soup.find_all('a', href=lambda x: x and '/entry/' in x)[:max_count]
        
        for link in links:
            articles.append({
                'title': link.get_text(strip=True),
                'url': link['href']
            })
        
        return articles
    
    def get_content(self, url: str) -> str:
        """記事内容を取得"""
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', class_='entry-content')
        return content.get_text(strip=True) if content else ""
    
    def save_json(self, data: List[Dict], filename: str):
        """JSON保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)