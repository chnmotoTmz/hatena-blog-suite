import requests
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import time
from datetime import datetime
import json


class LinkChecker:
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.link_cache = {}
        
    def extract_links_from_content(self, content: str, base_url: str = None) -> List[Dict]:
        """記事コンテンツからリンクを抽出"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            url = link['href']
            text = link.get_text(strip=True)
            
            # 相対URLを絶対URLに変換
            if base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            # 内部リンクかどうかを判定
            is_internal = self._is_internal_link(url, base_url)
            
            links.append({
                'url': url,
                'text': text,
                'is_internal': is_internal,
                'element': str(link)
            })
        
        return links
    
    def _is_internal_link(self, url: str, base_url: str) -> bool:
        """内部リンクかどうかを判定"""
        if not base_url:
            return False
        
        try:
            base_domain = urlparse(base_url).netloc
            link_domain = urlparse(url).netloc
            return base_domain == link_domain
        except:
            return False
    
    def check_single_link(self, url: str) -> Dict:
        """単一のリンクをチェック"""
        if url in self.link_cache:
            return self.link_cache[url]
        
        result = {
            'url': url,
            'status': 'unknown',
            'status_code': None,
            'final_url': url,
            'redirects': [],
            'error': None,
            'response_time': None,
            'checked_at': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            response = self.session.get(
                url, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            result['status_code'] = response.status_code
            result['final_url'] = response.url
            result['response_time'] = time.time() - start_time
            
            # リダイレクトの履歴を記録
            if response.history:
                result['redirects'] = [r.url for r in response.history]
            
            if response.status_code == 200:
                result['status'] = 'valid'
            elif response.status_code in [301, 302, 303, 307, 308]:
                result['status'] = 'redirect'
            elif response.status_code == 404:
                result['status'] = 'not_found'
            elif response.status_code >= 400:
                result['status'] = 'error'
            else:
                result['status'] = 'warning'
                
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error'] = 'Request timeout'
        except requests.exceptions.ConnectionError:
            result['status'] = 'connection_error'
            result['error'] = 'Connection failed'
        except requests.exceptions.RequestException as e:
            result['status'] = 'error'
            result['error'] = str(e)
        except Exception as e:
            result['status'] = 'error'
            result['error'] = f'Unexpected error: {str(e)}'
        
        # キャッシュに保存
        self.link_cache[url] = result
        return result
    
    async def check_links_async(self, urls: List[str], max_concurrent: int = 10) -> List[Dict]:
        """非同期でリンクを一括チェック"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_single_async(session, url):
            async with semaphore:
                if url in self.link_cache:
                    return self.link_cache[url]
                
                result = {
                    'url': url,
                    'status': 'unknown',
                    'status_code': None,
                    'final_url': url,
                    'redirects': [],
                    'error': None,
                    'response_time': None,
                    'checked_at': datetime.now().isoformat()
                }
                
                start_time = time.time()
                
                try:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with session.get(url, timeout=timeout, allow_redirects=True) as response:
                        result['status_code'] = response.status
                        result['final_url'] = str(response.url)
                        result['response_time'] = time.time() - start_time
                        
                        if response.status == 200:
                            result['status'] = 'valid'
                        elif response.status in [301, 302, 303, 307, 308]:
                            result['status'] = 'redirect'
                        elif response.status == 404:
                            result['status'] = 'not_found'
                        elif response.status >= 400:
                            result['status'] = 'error'
                        else:
                            result['status'] = 'warning'
                            
                except asyncio.TimeoutError:
                    result['status'] = 'timeout'
                    result['error'] = 'Request timeout'
                except aiohttp.ClientError as e:
                    result['status'] = 'connection_error'
                    result['error'] = str(e)
                except Exception as e:
                    result['status'] = 'error'
                    result['error'] = f'Unexpected error: {str(e)}'
                
                self.link_cache[url] = result
                return result
        
        async with aiohttp.ClientSession(
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        ) as session:
            tasks = [check_single_async(session, url) for url in urls]
            return await asyncio.gather(*tasks)
    
    def check_article_links(self, article: Dict) -> Dict:
        """記事のリンクを全てチェック"""
        content = article.get('full_content', '') or article.get('content', '')
        base_url = article.get('url', '')
        
        # リンクを抽出
        links = self.extract_links_from_content(content, base_url)
        
        # 各リンクをチェック
        checked_links = []
        for link in links:
            check_result = self.check_single_link(link['url'])
            link.update(check_result)
            checked_links.append(link)
        
        # 統計情報を計算
        stats = self._calculate_link_stats(checked_links)
        
        return {
            'article_title': article.get('title', ''),
            'article_url': article.get('url', ''),
            'total_links': len(checked_links),
            'links': checked_links,
            'statistics': stats,
            'checked_at': datetime.now().isoformat()
        }
    
    def _calculate_link_stats(self, links: List[Dict]) -> Dict:
        """リンクの統計情報を計算"""
        stats = {
            'total': len(links),
            'valid': 0,
            'invalid': 0,
            'redirects': 0,
            'timeouts': 0,
            'errors': 0,
            'internal': 0,
            'external': 0
        }
        
        for link in links:
            if link.get('is_internal'):
                stats['internal'] += 1
            else:
                stats['external'] += 1
            
            status = link.get('status', 'unknown')
            if status == 'valid':
                stats['valid'] += 1
            elif status in ['not_found', 'error']:
                stats['invalid'] += 1
            elif status == 'redirect':
                stats['redirects'] += 1
            elif status == 'timeout':
                stats['timeouts'] += 1
            else:
                stats['errors'] += 1
        
        return stats
    
    def generate_link_report(self, results: List[Dict], output_file: str = None) -> str:
        """リンクチェック結果のレポートを生成"""
        report_lines = []
        report_lines.append("# リンクチェック報告書")
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 全体統計
        total_articles = len(results)
        total_links = sum(r['total_links'] for r in results)
        total_valid = sum(r['statistics']['valid'] for r in results)
        total_invalid = sum(r['statistics']['invalid'] for r in results)
        
        report_lines.append("## 全体統計")
        report_lines.append(f"- 対象記事数: {total_articles}")
        report_lines.append(f"- 総リンク数: {total_links}")
        report_lines.append(f"- 有効リンク: {total_valid} ({total_valid/total_links*100:.1f}%)" if total_links > 0 else "- 有効リンク: 0")
        report_lines.append(f"- 無効リンク: {total_invalid} ({total_invalid/total_links*100:.1f}%)" if total_links > 0 else "- 無効リンク: 0")
        report_lines.append("")
        
        # 問題のあるリンクの詳細
        report_lines.append("## 問題のあるリンク")
        for result in results:
            invalid_links = [link for link in result['links'] if link.get('status') not in ['valid', 'redirect']]
            if invalid_links:
                report_lines.append(f"### {result['article_title']}")
                report_lines.append(f"記事URL: {result['article_url']}")
                for link in invalid_links:
                    report_lines.append(f"- **{link.get('status', 'unknown')}**: {link['url']}")
                    if link.get('error'):
                        report_lines.append(f"  - エラー: {link['error']}")
                    report_lines.append(f"  - リンクテキスト: {link.get('text', 'N/A')}")
                report_lines.append("")
        
        # リダイレクトの詳細
        report_lines.append("## リダイレクトされたリンク")
        for result in results:
            redirect_links = [link for link in result['links'] if link.get('status') == 'redirect']
            if redirect_links:
                report_lines.append(f"### {result['article_title']}")
                for link in redirect_links:
                    report_lines.append(f"- {link['url']} → {link.get('final_url', 'N/A')}")
                report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
        
        return report_content
    
    def suggest_link_fixes(self, results: List[Dict]) -> List[Dict]:
        """リンク修正の提案を生成"""
        suggestions = []
        
        for result in results:
            article_suggestions = {
                'article_title': result['article_title'],
                'article_url': result['article_url'],
                'fixes': []
            }
            
            for link in result['links']:
                if link.get('status') == 'not_found':
                    article_suggestions['fixes'].append({
                        'type': 'remove_or_replace',
                        'original_url': link['url'],
                        'suggestion': 'リンクを削除するか、代替URLに置換してください',
                        'link_text': link.get('text', '')
                    })
                elif link.get('status') == 'redirect' and link.get('final_url') != link['url']:
                    article_suggestions['fixes'].append({
                        'type': 'update_url',
                        'original_url': link['url'],
                        'suggested_url': link.get('final_url'),
                        'suggestion': 'リダイレクト先のURLに直接リンクを更新',
                        'link_text': link.get('text', '')
                    })
            
            if article_suggestions['fixes']:
                suggestions.append(article_suggestions)
        
        return suggestions
    
    def save_cache(self, cache_file: str):
        """リンクキャッシュを保存"""
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.link_cache, f, ensure_ascii=False, indent=2)
    
    def load_cache(self, cache_file: str):
        """リンクキャッシュを読み込み"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.link_cache = json.load(f)
        except FileNotFoundError:
            self.link_cache = {}