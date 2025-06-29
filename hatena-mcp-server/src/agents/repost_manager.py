import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import hashlib
from .hatena_publisher import HatenaPublisher


class RepostManager:
    def __init__(self, hatena_id: str, blog_domain: str = None, api_key: Optional[str] = None):
        self.hatena_id = hatena_id
        self.blog_domain = blog_domain or os.getenv('BLOG_DOMAIN')
        self.api_key = api_key
        self.base_url = f"https://blog.hatena.ne.jp/{hatena_id}"
        self.history_file = "repost_history.json"
        self.repost_history = self._load_history()
        
        # Initialize publisher if we have blog_domain
        self.publisher = None
        if self.blog_domain:
            try:
                self.publisher = HatenaPublisher(hatena_id, self.blog_domain, api_key)
            except Exception as e:
                print(f"Warning: Could not initialize publisher: {e}")
        
    def _load_history(self) -> Dict:
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.repost_history, f, ensure_ascii=False, indent=2)
    
    def analyze_article_performance(self, articles: List[Dict]) -> List[Dict]:
        performance_data = []
        
        for article in articles:
            article_id = self._generate_article_id(article['url'])
            
            performance = {
                'article_id': article_id,
                'title': article['title'],
                'url': article['url'],
                'original_date': article['date'],
                'categories': article['categories'],
                'word_count': article.get('word_count', 0),
                'repost_count': self._get_repost_count(article_id),
                'last_repost': self._get_last_repost_date(article_id),
                'performance_score': self._calculate_performance_score(article)
            }
            
            performance_data.append(performance)
        
        return sorted(performance_data, key=lambda x: x['performance_score'], reverse=True)
    
    def _generate_article_id(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:10]
    
    def _get_repost_count(self, article_id: str) -> int:
        if article_id in self.repost_history:
            return len(self.repost_history[article_id].get('reposts', []))
        return 0
    
    def _get_last_repost_date(self, article_id: str) -> Optional[str]:
        if article_id in self.repost_history:
            reposts = self.repost_history[article_id].get('reposts', [])
            if reposts:
                return reposts[-1]['date']
        return None
    
    def _calculate_performance_score(self, article: Dict) -> float:
        score = 0.0
        
        # Date-based scoring with better error handling
        if article.get('date'):
            try:
                # Handle various date formats
                date_str = article['date']
                if 'T' in date_str:
                    article_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Try parsing as simple date string
                    article_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                days_old = (datetime.now() - article_date).days
                if days_old > 180:
                    score += 10
                elif days_old > 90:
                    score += 5
                elif days_old > 30:
                    score += 2
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not parse date '{article.get('date')}': {e}")
        
        # Category-based scoring
        if len(article.get('categories', [])) > 0:
            score += 3
        
        # Word count-based scoring
        word_count = article.get('word_count', 0)
        if word_count > 1500:
            score += 5
        elif word_count > 800:
            score += 3
        elif word_count > 300:
            score += 1
        
        return score
    
    def select_articles_for_repost(self, 
                                 articles: List[Dict], 
                                 max_articles: int = 5,
                                 min_days_between_reposts: int = 90) -> List[Dict]:
        performance_data = self.analyze_article_performance(articles)
        selected = []
        
        for article in performance_data:
            article_id = article['article_id']
            
            if self._can_repost(article_id, min_days_between_reposts):
                selected.append(article)
                
            if len(selected) >= max_articles:
                break
        
        return selected
    
    def _can_repost(self, article_id: str, min_days: int) -> bool:
        last_repost = self._get_last_repost_date(article_id)
        
        if not last_repost:
            return True
        
        last_repost_date = datetime.fromisoformat(last_repost)
        days_since_repost = (datetime.now() - last_repost_date).days
        
        return days_since_repost >= min_days
    
    def create_repost_content(self, 
                            original_article: Dict,
                            update_type: str = "refresh",
                            custom_intro: Optional[str] = None) -> Dict:
        article_id = self._generate_article_id(original_article['url'])
        
        intro_templates = {
            'refresh': "【更新版】この記事は{date}に公開した内容を最新情報に更新したものです。",
            'seasonal': "【季節の再掲】{date}に公開した記事を、この時期に改めてお届けします。",
            'popular': "【人気記事】多くの方に読まれた記事を、加筆修正してお届けします。",
            'series': "【シリーズ再掲】過去の連載記事を振り返ります。"
        }
        
        intro = custom_intro or intro_templates.get(
            update_type, 
            intro_templates['refresh']
        ).format(date=original_article.get('date', '')[:10] if original_article.get('date') else "過去")
        
        # 元記事のコンテンツを取得（HTML content を優先）
        original_content = (
            original_article.get('html_content', '') or 
            original_article.get('full_content', '') or 
            original_article.get('content', '') or 
            original_article.get('summary', '')
        )
        
        # Debug logging
        print(f"Creating repost content for: {original_article.get('title', 'Unknown')}")
        print(f"Original content length: {len(original_content)} characters")
        print(f"Content source: {'html_content' if original_article.get('html_content') else 'full_content' if original_article.get('full_content') else 'content' if original_article.get('content') else 'summary' if original_article.get('summary') else 'none'}")
        
        # If we have full HTML content with <div class="entry-content">, extract just the inner HTML
        if '<div class="entry-content"' in original_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(original_content, 'html.parser')
            entry_content = soup.find('div', class_='entry-content')
            if entry_content:
                # Get inner HTML content
                original_content = entry_content.get_text() + '\n\n' + ''.join([str(tag) for tag in entry_content.find_all(['p', 'img', 'a', 'strong', 'em'])])
                # If that doesn't work, just use the full html_content
                if not original_content.strip():
                    original_content = original_article.get('content', '') or original_article.get('full_content', '')
        
        updated_content = f"""<div class="repost-intro">
{intro}
</div>

<div class='update-section'>
<h3>2025年の更新情報</h3>
<ul>
<li>内容を最新の状況に合わせて更新しました</li>
<li>関連情報やリンクを見直しました</li>
</ul>
</div>

{original_content}

<div class="repost-footer">
<p>元記事: <a href="{original_article['url']}">{original_article['title']}</a></p>
</div>"""
        
        new_title = f"【再掲】{original_article['title']}"
        if update_type == "refresh":
            new_title = f"【2025年版】{original_article['title']}"
        
        return {
            'title': new_title,
            'content': updated_content,
            'categories': original_article['categories'] + ['再掲載'],
            'original_url': original_article['url'],
            'article_id': article_id,
            'update_type': update_type
        }
    
    def update_repost_with_new_info(self, 
                                  repost_content: Dict,
                                  new_information: List[str]) -> Dict:
        update_section = "\n\n<div class='update-section'>\n<h3>2025年の更新情報</h3>\n<ul>\n"
        
        for info in new_information:
            update_section += f"<li>{info}</li>\n"
        
        update_section += "</ul>\n</div>\n\n"
        
        content_parts = repost_content['content'].split('</div>', 1)
        if len(content_parts) > 1:
            repost_content['content'] = content_parts[0] + '</div>' + update_section + content_parts[1]
        else:
            repost_content['content'] = update_section + repost_content['content']
        
        return repost_content
    
    def schedule_repost(self, 
                       repost_content: Dict,
                       publish_date: Optional[datetime] = None) -> Dict:
        article_id = repost_content['article_id']
        
        if article_id not in self.repost_history:
            self.repost_history[article_id] = {
                'original_url': repost_content['original_url'],
                'reposts': []
            }
        
        repost_entry = {
            'date': (publish_date or datetime.now()).isoformat(),
            'update_type': repost_content['update_type'],
            'new_title': repost_content['title'],
            'status': 'scheduled' if publish_date and publish_date > datetime.now() else 'published'
        }
        
        self.repost_history[article_id]['reposts'].append(repost_entry)
        self._save_history()
        
        return {
            'article_id': article_id,
            'scheduled_date': repost_entry['date'],
            'status': repost_entry['status']
        }
    
    def generate_repost_calendar(self, 
                               articles: List[Dict],
                               weeks_ahead: int = 4) -> List[Dict]:
        selected_articles = self.select_articles_for_repost(articles)
        calendar = []
        
        current_date = datetime.now()
        days_between_posts = (weeks_ahead * 7) // len(selected_articles) if selected_articles else 7
        
        for i, article in enumerate(selected_articles):
            publish_date = current_date + timedelta(days=i * days_between_posts)
            
            calendar_entry = {
                'article': article,
                'publish_date': publish_date.isoformat(),
                'update_type': self._determine_update_type(article, publish_date),
                'preparation_notes': self._generate_preparation_notes(article)
            }
            
            calendar.append(calendar_entry)
        
        return calendar
    
    def _determine_update_type(self, article: Dict, publish_date: datetime) -> str:
        month = publish_date.month
        
        if month in [12, 1, 2]:
            return "seasonal"
        elif article['performance_score'] > 15:
            return "popular"
        else:
            return "refresh"
    
    def _generate_preparation_notes(self, article: Dict) -> List[str]:
        notes = []
        
        if article['word_count'] < 1000:
            notes.append("記事が短いので、追加コンテンツの検討が必要")
        
        if not article.get('last_repost'):
            notes.append("初回の再掲載です")
        
        if 'プログラミング' in ' '.join(article['categories']):
            notes.append("技術的な内容の更新確認が必要")
        
        return notes
    
    def export_repost_plan(self, calendar: List[Dict], filename: str = "repost_plan.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(calendar, f, ensure_ascii=False, indent=2)
        
        print(f"Repost plan exported to {filename}")
    
    def publish_scheduled_reposts(self, calendar: List[Dict], dry_run: bool = True, full_articles_data: List[Dict] = None) -> List[Dict]:
        """カレンダーに基づいて記事を投稿"""
        if not self.publisher:
            return [{"status": "error", "message": "Publisher not initialized. Need blog_domain and API key."}]
        
        results = []
        
        for entry in calendar:
            publish_date = datetime.fromisoformat(entry['publish_date'].replace('Z', '+00:00'))
            
            # Check if it's time to publish
            if publish_date <= datetime.now():
                article = entry['article']
                
                # Find the full article data if provided
                if full_articles_data:
                    for full_art in full_articles_data:
                        if full_art['url'] == article['url']:
                            article = full_art
                            break
                
                # Create repost content
                repost_content = self.create_repost_content(
                    article,
                    entry['update_type']
                )
                
                if dry_run:
                    results.append({
                        "status": "dry_run",
                        "title": repost_content['title'],
                        "scheduled_date": entry['publish_date'],
                        "update_type": entry['update_type']
                    })
                else:
                    # Actually publish
                    result = self.publisher.publish_repost(repost_content, is_draft=True)
                    result['scheduled_date'] = entry['publish_date']
                    results.append(result)
                    
                    # Update history if successful
                    if result['status'] == 'success':
                        self.schedule_repost(repost_content, publish_date)
        
        return results