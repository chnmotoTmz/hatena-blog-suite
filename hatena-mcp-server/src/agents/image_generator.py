import os
import requests
from typing import List, Dict, Optional, Tuple
from PIL import Image
from io import BytesIO
from datetime import datetime
import json
import base64


class ImageGenerator:
    def __init__(self, bing_auth_cookie: str, output_dir: str = "./generated_images"):
        self.bing_auth_cookie = bing_auth_cookie
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Bing Image Creator初期化
        try:
            from bingart import BingArt
            self.bing_art = BingArt(auth_cookie_U=bing_auth_cookie)
        except ImportError:
            print("Warning: bingart not installed. Please install with: pip install bingart")
            self.bing_art = None
    
    def analyze_article_for_images(self, article_content: str) -> List[Dict]:
        """
        記事内容から画像提案を生成（簡易版）
        OpenAI依存を除去し、基本的な画像提案を返す
        """
        # 記事タイトルから基本的な画像提案を生成
        basic_suggestions = [
            {
                "section": "アイキャッチ画像",
                "description": f"Professional blog header image related to the article topic",
                "purpose": "アイキャッチ",
                "style": "modern minimalist"
            }
        ]
        
        # 記事の長さに応じて追加画像を提案
        if len(article_content) > 1000:
            basic_suggestions.append({
                "section": "本文画像",
                "description": "Complementary illustration for the article content",
                "purpose": "説明図",
                "style": "clean illustration"
            })
        
        return basic_suggestions
    
    def generate_image(self, 
                      description: str, 
                      timeout: int = 300) -> List[str]:
        """
        Bing Image Creatorを使用して画像を生成
        
        Args:
            description: 画像生成用のプロンプト
            timeout: タイムアウト時間（秒）
            
        Returns:
            生成された画像のURLリスト
        """
        if not self.bing_art:
            print("Error: Bing Image Creator not initialized")
            return []
        
        try:
            print(f"Generating image with Bing Image Creator: {description[:50]}...")
            results = self.bing_art.generate_images(description, timeout=timeout)
            
            if results and isinstance(results, list):
                print(f"Successfully generated {len(results)} images")
                return results
            else:
                print("No images generated")
                return []
                
        except Exception as e:
            print(f"Error generating image with Bing: {e}")
            return []
    
    def close_session(self):
        """Bing Image Creatorのセッションを閉じる"""
        if self.bing_art:
            try:
                self.bing_art.close_session()
            except Exception as e:
                print(f"Error closing Bing session: {e}")
    
    def download_and_save_image(self, image_url: str, filename: str) -> str:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            
            filepath = os.path.join(self.output_dir, filename)
            image.save(filepath)
            
            return filepath
        else:
            raise Exception(f"Failed to download image: {response.status_code}")
    
    def replace_article_images(self, 
                             article_html: str, 
                             image_suggestions: List[Dict]) -> Tuple[str, List[Dict]]:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(article_html, 'html.parser')
        existing_images = soup.find_all('img')
        
        generated_images = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, (img_tag, suggestion) in enumerate(zip(existing_images, image_suggestions)):
            description = suggestion['description']
            
            print(f"Generating image {i+1}/{len(image_suggestions)}: {suggestion['section']}")
            
            image_urls = self.generate_image(description)
            if image_urls and len(image_urls) > 0:
                # 最初の画像を使用
                image_url = image_urls[0]
                filename = f"generated_{timestamp}_{i+1}.png"
                local_path = self.download_and_save_image(image_url, filename)
                
                img_tag['src'] = local_path
                img_tag['alt'] = suggestion['purpose']
                
                generated_images.append({
                    'original_src': img_tag.get('src', ''),
                    'new_src': local_path,
                    'description': description,
                    'section': suggestion['section'],
                    'all_urls': image_urls  # 全ての生成画像URL
                })
        
        updated_html = str(soup)
        return updated_html, generated_images
    
    def create_featured_image(self, 
                            article_title: str, 
                            article_summary: str,
                            style_preference: str = "modern blog header") -> Optional[str]:
        prompt = f"""Create a featured header image for a blog article.
Title: {article_title}
Summary: {article_summary}
Style: {style_preference}

The image should be eye-catching, professional, and represent the article's theme."""
        
        image_urls = self.generate_image(prompt)
        
        if image_urls and len(image_urls) > 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"featured_{timestamp}.png"
            local_path = self.download_and_save_image(image_urls[0], filename)
            return local_path
        
        return None
    
    def optimize_image_for_web(self, image_path: str, max_width: int = 1200) -> str:
        image = Image.open(image_path)
        
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        optimized_path = image_path.replace('.png', '_optimized.jpg')
        image.convert('RGB').save(optimized_path, 'JPEG', quality=85, optimize=True)
        
        return optimized_path