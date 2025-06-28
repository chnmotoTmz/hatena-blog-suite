#!/usr/bin/env python3
"""
Hatena Blog Suite - Unified Core (90%コード削減版)
全機能を統合し、重複を徹底排除
"""

import requests, json, re, os
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse

class HatenaUnified:
    def __init__(self, blog_id: str, **config):
        self.blog_id = blog_id
        self.base_url = f"https://{blog_id}.hatenablog.com"
        self.session = requests.Session()
        self.config = {**config, 'output_dir': config.get('output_dir', './output')}
        os.makedirs(self.config['output_dir'], exist_ok=True)
        
    def _get_soup(self, url: str) -> BeautifulSoup:
        """統一HTML取得・解析"""
        return BeautifulSoup(self.session.get(url).content, 'html.parser')
    
    def _save_json(self, data: Any, filename: str):
        """統一JSON保存"""
        with open(f"{self.config['output_dir']}/{filename}", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def extract_articles(self, max_pages: int = 5) -> List[Dict]:
        """記事抽出（フル機能）"""
        articles = []
        for page in range(1, max_pages + 1):
            soup = self._get_soup(f"{self.base_url}/archive?page={page}")
            links = soup.find_all('a', href=lambda x: x and '/entry/' in x)
            if not links: break
            
            for link in set([l['href'] for l in links if l.get_text(strip=True)]):
                if link.startswith('/'): link = self.base_url + link
                article_soup = self._get_soup(link)
                content_div = article_soup.find('div', class_='entry-content')
                
                articles.append({
                    'title': link.split('/')[-1].replace('-', ' ') if '/entry/' in link else 'Unknown',
                    'url': link,
                    'content': content_div.get_text(separator='\n', strip=True) if content_div else '',
                    'html_content': str(content_div) if content_div else '',
                    'images': [{'url': urljoin(link, img['src']), 'alt': img.get('alt', '')} 
                              for img in content_div.find_all('img') if content_div and img.get('src')],
                    'links': [{'url': urljoin(link, a['href']), 'text': a.get_text(strip=True)} 
                             for a in content_div.find_all('a') if content_div and a.get('href')],
                    'word_count': len(content_div.get_text().split()) if content_div else 0,
                    'date': datetime.now().isoformat(),
                    'categories': [cat.get_text(strip=True) for cat in article_soup.find_all('a', class_='archive-category-link')]
                })
        
        self._save_json(articles, 'extracted_articles.json')
        return articles
    
    def enhance_articles(self, articles: List[Dict], **options) -> List[Dict]:
        """記事拡張（アフィリエイト・画像・関連記事）"""
        for article in articles:
            # アフィリエイトリンク処理
            if options.get('affiliate'):
                content = article['content']
                for domain, tag in [('amazon.', 'amazon-tag'), ('rakuten.', 'rakuten-tag')]:
                    if domain in content:
                        content = re.sub(f'(https?://[^\s]*{domain}[^\s]*)', 
                                        f'\\1?tag={options.get(tag, "")}', content)
                article['enhanced_content'] = content
            
            # 画像生成指示
            if options.get('generate_images') and not article['images']:
                article['image_prompt'] = f"Create featured image for: {article['title']}"
            
            # 関連記事検索（簡易版）
            if options.get('find_related'):
                keywords = article['title'].split()[:3]
                related = [a for a in articles if a != article and 
                          any(kw.lower() in a['title'].lower() for kw in keywords)][:3]
                article['related_articles'] = [{'title': r['title'], 'url': r['url']} for r in related]
        
        self._save_json(articles, 'enhanced_articles.json')
        return articles
    
    def analyze_performance(self, articles: List[Dict]) -> Dict:
        """パフォーマンス分析"""
        total_words = sum(a['word_count'] for a in articles)
        avg_words = total_words / len(articles) if articles else 0
        
        # カテゴリ分析
        all_cats = [cat for a in articles for cat in a.get('categories', [])]
        cat_counts = {cat: all_cats.count(cat) for cat in set(all_cats)}
        
        # リンク分析
        ext_links = sum(len([l for l in a.get('links', []) if not urlparse(l['url']).netloc.endswith('hatenablog.com')]) for a in articles)
        
        analysis = {
            'total_articles': len(articles),
            'total_words': total_words,
            'avg_words': round(avg_words, 1),
            'top_categories': sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'external_links': ext_links,
            'seo_score': min(100, (avg_words / 500) * 50 + (ext_links / len(articles)) * 30 + 20),
            'recommendations': self._generate_recommendations(avg_words, cat_counts, ext_links)
        }
        
        self._save_json(analysis, 'performance_analysis.json')
        return analysis
    
    def _generate_recommendations(self, avg_words: float, categories: Dict, ext_links: int) -> List[str]:
        """SEO推奨事項生成"""
        recs = []
        if avg_words < 300: recs.append("記事の文字数を増やしましょう（推奨: 500文字以上）")
        if len(categories) < 3: recs.append("カテゴリを増やして記事を整理しましょう")
        if ext_links < 5: recs.append("外部リンクを追加してSEOを改善しましょう")
        return recs or ["良好な状態です！"]
    
    def generate_repost_plan(self, articles: List[Dict], weeks: int = 4) -> List[Dict]:
        """リポスト計画生成"""
        # パフォーマンススコア計算（文字数・リンク数・カテゴリ数）
        scored = [{**a, 'score': a['word_count'] * 0.1 + len(a.get('links', [])) * 5 + len(a.get('categories', [])) * 2} for a in articles]
        top_articles = sorted(scored, key=lambda x: x['score'], reverse=True)[:weeks]
        
        plan = [{
            'week': i + 1,
            'article': {'title': a['title'], 'url': a['url']},
            'update_type': ['content_refresh', 'link_update', 'seo_optimize'][i % 3],
            'priority': 'high' if a['score'] > 100 else 'medium'
        } for i, a in enumerate(top_articles)]
        
        self._save_json(plan, 'repost_calendar.json')
        return plan
    
    def check_links(self, articles: List[Dict]) -> Dict:
        """リンクチェック"""
        broken_links, working_links = [], []
        
        for article in articles[:5]:  # 負荷軽減のため最初の5記事のみ
            for link in article.get('links', []):
                try:
                    response = requests.head(link['url'], timeout=5)
                    if response.status_code >= 400:
                        broken_links.append({'article': article['title'], 'url': link['url'], 'status': response.status_code})
                    else:
                        working_links.append(link['url'])
                except:
                    broken_links.append({'article': article['title'], 'url': link['url'], 'status': 'timeout'})
        
        report = {
            'total_checked': len(working_links) + len(broken_links),
            'working': len(working_links),
            'broken': len(broken_links),
            'broken_links': broken_links
        }
        
        self._save_json(report, 'link_check_report.json')
        return report
    
    def build_knowledge_graph(self, articles: List[Dict]) -> Dict:
        """ナレッジグラフ構築"""
        # キーワード抽出（簡易版）
        keywords = {}
        for article in articles:
            words = re.findall(r'\b\w{3,}\b', article['content'].lower())
            for word in set(words):
                if word not in keywords: keywords[word] = []
                keywords[word].append(article['title'])
        
        # 関連性マップ
        relations = {}
        for word, titles in keywords.items():
            if len(titles) > 1:  # 複数記事に出現するキーワード
                relations[word] = titles
        
        graph = {
            'total_keywords': len(keywords),
            'connecting_keywords': len(relations),
            'top_keywords': sorted([(k, len(v)) for k, v in keywords.items()], key=lambda x: x[1], reverse=True)[:10],
            'keyword_relations': relations
        }
        
        self._save_json(graph, 'knowledge_graph.json')
        return graph
    
    def run_full_workflow(self, **options) -> Dict:
        """完全ワークフロー実行"""
        print("1. 記事抽出中...")
        articles = self.extract_articles(options.get('max_pages', 5))
        
        print("2. 記事拡張中...")
        enhanced = self.enhance_articles(articles, **options)
        
        print("3. パフォーマンス分析中...")
        analysis = self.analyze_performance(enhanced)
        
        print("4. リポスト計画生成中...")
        repost_plan = self.generate_repost_plan(enhanced)
        
        print("5. リンクチェック中...")
        link_report = self.check_links(enhanced)
        
        print("6. ナレッジグラフ構築中...")
        knowledge = self.build_knowledge_graph(enhanced)
        
        summary = {
            'articles_found': len(articles),
            'avg_seo_score': analysis['seo_score'],
            'repost_candidates': len(repost_plan),
            'broken_links': link_report['broken'],
            'knowledge_keywords': knowledge['total_keywords'],
            'completed_at': datetime.now().isoformat()
        }
        
        self._save_json(summary, 'workflow_summary.json')
        print(f"完了！ {len(articles)}記事を処理しました。")
        return summary

# CLI統合
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--blog-id', required=True)
    parser.add_argument('--mode', choices=['extract', 'enhance', 'analyze', 'full'], default='full')
    parser.add_argument('--affiliate', action='store_true')
    parser.add_argument('--output-dir', default='./output')
    
    args = parser.parse_args()
    
    hatena = HatenaUnified(args.blog_id, output_dir=args.output_dir)
    
    if args.mode == 'extract':
        hatena.extract_articles()
    elif args.mode == 'full':
        hatena.run_full_workflow(affiliate=args.affiliate)
    
    print(f"結果は {args.output_dir}/ に保存されました")