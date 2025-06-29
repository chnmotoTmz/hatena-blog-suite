import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import json


class AffiliateManager:
    def __init__(self, config_file: Optional[str] = None):
        self.affiliate_configs = {
            'rakuten': {
                'tag_param': 'mafRakutenWidgetParam',
                'default_tag': '',
                'domains': ['hb.afl.rakuten.co.jp', 'affiliate.rakuten.co.jp'],
                'pattern': r'https?://(?:hb\.afl|affiliate)\.rakuten\.co\.jp/.*'
            }
        }
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        for service, settings in config.items():
            if service in self.affiliate_configs:
                self.affiliate_configs[service].update(settings)
    
    def set_affiliate_tag(self, service: str, tag: str):
        if service in self.affiliate_configs:
            self.affiliate_configs[service]['default_tag'] = tag
    
    def detect_affiliate_service(self, url: str) -> Optional[str]:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for service, config in self.affiliate_configs.items():
            if any(affiliate_domain in domain for affiliate_domain in config['domains']):
                return service
        
        return None
    
    def add_affiliate_tag(self, url: str, tag: Optional[str] = None) -> str:
        service = self.detect_affiliate_service(url)
        if not service:
            return url
        
        config = self.affiliate_configs[service]
        affiliate_tag = tag or config['default_tag']
        
        if not affiliate_tag:
            return url
        
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        query_params[config['tag_param']] = [affiliate_tag]
        
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        return new_url
    
    def process_article_content(self, content: str, auto_detect: bool = True) -> Tuple[str, List[Dict]]:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:[.,;:!?](?=\s|$))?'
        urls_found = re.findall(url_pattern, content)
        
        processed_urls = []
        modified_content = content
        
        for url in urls_found:
            clean_url = url.rstrip('.,;:!?')
            
            if auto_detect and self.detect_affiliate_service(clean_url):
                new_url = self.add_affiliate_tag(clean_url)
                if new_url != clean_url:
                    modified_content = modified_content.replace(clean_url, new_url)
                    processed_urls.append({
                        'original': clean_url,
                        'modified': new_url,
                        'service': self.detect_affiliate_service(clean_url)
                    })
        
        return modified_content, processed_urls
    
    def create_product_link(self, 
                           product_name: str,
                           product_url: str,
                           price: Optional[str] = None,
                           image_url: Optional[str] = None,
                           description: Optional[str] = None) -> str:
        affiliate_url = self.add_affiliate_tag(product_url)
        
        html_template = f'''<div class="affiliate-product">
    {'<img src="' + image_url + '" alt="' + product_name + '" class="product-image">' if image_url else ''}
    <h4 class="product-name"><a href="{affiliate_url}" target="_blank" rel="noopener">{product_name}</a></h4>
    {'<p class="product-price">' + price + '</p>' if price else ''}
    {'<p class="product-description">' + description + '</p>' if description else ''}
    <a href="{affiliate_url}" class="product-button" target="_blank" rel="noopener">詳細を見る</a>
</div>'''
        
        return html_template
    
    def suggest_products(self, article_content: str, category: Optional[str] = None) -> List[Dict]:
        keywords = self._extract_keywords(article_content)
        
        suggestions = []
        
        product_database = {
            'tech': [
                {'name': 'ワイヤレスマウス', 'category': 'PC周辺機器', 'keywords': ['マウス', 'PC', 'パソコン']},
                {'name': 'USB-Cハブ', 'category': 'PC周辺機器', 'keywords': ['USB', 'ハブ', 'Mac', 'パソコン']},
            ],
            'book': [
                {'name': 'Python実践入門', 'category': '技術書', 'keywords': ['Python', 'プログラミング', '開発']},
                {'name': 'リーダブルコード', 'category': '技術書', 'keywords': ['コード', 'プログラミング', '設計']},
            ]
        }
        
        relevant_products = []
        for cat, products in product_database.items():
            if not category or category == cat:
                for product in products:
                    if any(kw in keywords for kw in product['keywords']):
                        relevant_products.append(product)
        
        return relevant_products[:5]
    
    def _extract_keywords(self, text: str) -> List[str]:
        try:
            import MeCab
            
            mecab = MeCab.Tagger()
            node = mecab.parseToNode(text)
            
            keywords = []
            while node:
                features = node.feature.split(',')
                if features[0] in ['名詞'] and features[1] not in ['非自立', '代名詞', '数']:
                    if len(node.surface) > 1:
                        keywords.append(node.surface)
                node = node.next
            
            return list(set(keywords))
        except ImportError:
            # MeCabが利用できない場合は簡易的なキーワード抽出
            import re
            words = re.findall(r'[ァ-ヴー]+|[ぁ-ん]+|[A-Za-z]+', text)
            return [word for word in words if len(word) > 2]
    
    def generate_affiliate_report(self, processed_urls: List[Dict]) -> str:
        report = "## アフィリエイトリンク処理レポート\n\n"
        
        service_counts = {}
        for url_info in processed_urls:
            service = url_info['service']
            service_counts[service] = service_counts.get(service, 0) + 1
        
        report += "### 処理されたリンク数\n"
        for service, count in service_counts.items():
            report += f"- {service}: {count}件\n"
        
        report += "\n### 処理詳細\n"
        for i, url_info in enumerate(processed_urls, 1):
            report += f"{i}. {url_info['service']}\n"
            report += f"   - 元URL: {url_info['original']}\n"
            report += f"   - 変更後: {url_info['modified']}\n\n"
        
        return report
    
    def auto_detect_and_insert_affiliate_products(self, content: str) -> str:
        """記事内容から関連商品を自動検出してアフィリエイトリンクを挿入"""
        keywords = self._extract_keywords(content)
        
        # 商品データベース（実際の実装では外部APIや設定ファイルから取得）
        products_db = {
            'amazon': [
                {
                    'name': 'プログラミング入門書',
                    'url': 'https://www.amazon.co.jp/dp/example',
                    'keywords': ['プログラミング', 'Python', 'JavaScript', '入門', '初心者'],
                    'price': '¥2,500',
                    'category': '書籍'
                },
                {
                    'name': 'ワイヤレスマウス',
                    'url': 'https://www.amazon.co.jp/dp/example2', 
                    'keywords': ['マウス', 'PC', 'パソコン', 'ワイヤレス'],
                    'price': '¥3,000',
                    'category': 'PC周辺機器'
                }
            ],
            'rakuten': [
                {
                    'name': 'コーヒーメーカー',
                    'url': 'https://item.rakuten.co.jp/example',
                    'keywords': ['コーヒー', 'カフェ', 'ドリップ', 'メーカー'],
                    'price': '¥15,000',
                    'category': 'キッチン家電'
                }
            ]
        }
        
        matched_products = []
        
        # キーワードマッチングで商品を検出
        for service, products in products_db.items():
            for product in products:
                product_score = 0
                for keyword in keywords:
                    if keyword in product['keywords']:
                        product_score += 1
                
                if product_score >= 2:  # 2つ以上のキーワードが一致
                    matched_products.append({
                        'product': product,
                        'service': service,
                        'score': product_score
                    })
        
        # スコア順にソート
        matched_products.sort(key=lambda x: x['score'], reverse=True)
        
        # 上位3商品をコンテンツに挿入
        enhanced_content = content
        for match in matched_products[:3]:
            product = match['product']
            affiliate_url = self.add_affiliate_tag(product['url'])
            
            product_html = f'''
<div class="recommended-product">
    <h4>おすすめ商品</h4>
    <p><strong>{product['name']}</strong></p>
    <p>価格: {product['price']}</p>
    <p><a href="{affiliate_url}" target="_blank" rel="noopener">詳細を見る</a></p>
</div>
'''
            
            # 適切な位置に挿入（段落の間）
            paragraphs = enhanced_content.split('\n\n')
            if len(paragraphs) > 2:
                insert_pos = len(paragraphs) // 2
                paragraphs.insert(insert_pos, product_html)
                enhanced_content = '\n\n'.join(paragraphs)
            else:
                enhanced_content += product_html
        
        return enhanced_content
    
    def analyze_affiliate_performance(self, articles: List[Dict]) -> Dict:
        """アフィリエイトリンクのパフォーマンス分析"""
        performance_data = {
            'total_articles': len(articles),
            'articles_with_affiliate': 0,
            'service_distribution': {},
            'category_performance': {},
            'recommendations': []
        }
        
        for article in articles:
            content = article.get('full_content', '') or article.get('content', '')
            if not content:
                continue
            
            # アフィリエイトリンクの検出
            _, processed_urls = self.process_article_content(content, auto_detect=True)
            
            if processed_urls:
                performance_data['articles_with_affiliate'] += 1
                
                for url_info in processed_urls:
                    service = url_info['service']
                    performance_data['service_distribution'][service] = \
                        performance_data['service_distribution'].get(service, 0) + 1
        
        # 推奨事項の生成
        coverage_rate = performance_data['articles_with_affiliate'] / performance_data['total_articles']
        
        if coverage_rate < 0.3:
            performance_data['recommendations'].append(
                "アフィリエイトリンクの導入率が低いです。より多くの記事に関連商品を追加することを検討してください。"
            )
        
        if 'rakuten' not in performance_data['service_distribution']:
            performance_data['recommendations'].append(
                "楽天アフィリエイトの活用を検討してください。幅広い商品カテゴリをカバーできます。"
            )
        
        return performance_data