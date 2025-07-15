"""
Search Service - Web検索機能
Google Custom Search APIを使用して関連情報を検索
"""

import logging
import requests
from typing import List, Dict, Optional
from src.config import Config

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        # Google Custom Search API設定
        self.api_key = Config.GOOGLE_SEARCH_API_KEY if hasattr(Config, 'GOOGLE_SEARCH_API_KEY') else None
        self.cse_id = Config.GOOGLE_CSE_ID if hasattr(Config, 'GOOGLE_CSE_ID') else None
        self.enabled = bool(self.api_key and self.cse_id)
        
        if not self.enabled:
            logger.warning("Google Search APIが設定されていません。Web検索機能は無効です。")
    
    def search_web(self, query: str, num_results: int = 3) -> List[Dict]:
        """Web検索を実行
        
        Args:
            query: 検索クエリ
            num_results: 結果数（最大10）
        
        Returns:
            List[Dict]: 検索結果
        """
        if not self.enabled:
            logger.warning("Google Search APIが無効のため、検索をスキップします")
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': min(num_results, 10)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayLink', '')
                })
            
            logger.info(f"Web検索完了: {len(results)}件の結果")
            return results
            
        except Exception as e:
            logger.error(f"Web検索エラー: {e}")
            return []
    
    def search_related_info(self, topic: str) -> Optional[str]:
        """トピックに関連する情報を検索して要約
        
        Args:
            topic: 検索トピック
        
        Returns:
            str: 関連情報の要約
        """
        if not self.enabled:
            return None
        
        try:
            # 検索実行
            results = self.search_web(topic, num_results=3)
            
            if not results:
                return None
            
            # 結果を要約形式で整理
            summary_parts = []
            summary_parts.append(f"## 📚 {topic}に関する関連情報")
            
            for i, result in enumerate(results, 1):
                summary_parts.append(f"### {i}. [{result['title']}]({result['link']})")
                summary_parts.append(f"{result['snippet']}")
                summary_parts.append("")  # 空行
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"関連情報検索エラー: {e}")
            return None
    
    def enhance_content_with_search(self, content: str, search_queries: List[str]) -> str:
        """コンテンツに検索情報を追加
        
        Args:
            content: 元のコンテンツ
            search_queries: 検索クエリリスト
        
        Returns:
            str: 検索情報が追加されたコンテンツ
        """
        if not self.enabled or not search_queries:
            return content
        
        try:
            enhanced_content = content
            search_info = []
            
            for query in search_queries:
                info = self.search_related_info(query)
                if info:
                    search_info.append(info)
            
            if search_info:
                enhanced_content += "\n\n---\n\n"
                enhanced_content += "## 🔍 関連情報\n\n"
                enhanced_content += "\n\n".join(search_info)
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"コンテンツ拡張エラー: {e}")
            return content
