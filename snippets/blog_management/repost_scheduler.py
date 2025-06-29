import os
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, TypedDict
import hashlib
import logging

# Assuming performance_analyzer is in the same directory or accessible
try:
    from .performance_analyzer import ArticlePerformanceScorer, ArticleMetadata
except ImportError:
    # Fallback for direct execution or different structure
    logging.warning("Using placeholder for ArticlePerformanceScorer. Ensure correct import for full functionality.")
    class ArticleMetadata(TypedDict, total=False): id: str; title: str; url: str; date_published: Optional[str]; performance_score: Optional[float] # Simplified
    class ArticlePerformanceScorer:
        def __init__(self, **kwargs): pass
        def rank_articles(self, articles: List[ArticleMetadata]) -> List[ArticleMetadata]:
            # Simple sort by date if score not present, or dummy score
            for art in articles: art['performance_score'] = art.get('performance_score', 0)
            return sorted(articles, key=lambda x: (x.get('performance_score',0), x.get('date_published', '')), reverse=True)

logger = logging.getLogger(__name__)

class RepostHistoryEntry(TypedDict):
    repost_date: str # ISO format datetime string
    reposted_title: str
    repost_url: Optional[str] # URL of the new reposted article
    update_type: str

class ArticleRepostInfo(TypedDict):
    original_url: str
    original_title: str # Added for easier reference
    original_date: Optional[str] # Added
    reposts: List[RepostHistoryEntry]

class RepostCandidate(TypedDict):
    article_metadata: ArticleMetadata # Original article's metadata including its performance score
    suggested_publish_date: str # ISO format
    suggested_update_type: str
    preparation_notes: List[str]

class RepostContent(TypedDict):
    title: str # Title for the repost
    content: str # HTML content for the repost
    categories: List[str]
    original_article_url: str
    original_article_id: str # A unique ID for the original article
    update_type: str


class RepostScheduler:
    """
    Manages selection of articles for reposting, content generation for reposts,
    and scheduling them into a calendar.
    """
    DEFAULT_REPOST_HISTORY_FILE = "repost_history.json"

    def __init__(
        self,
        performance_scorer: ArticlePerformanceScorer,
        repost_history_filepath: Optional[str] = None,
        min_days_between_reposts: int = 90,
        default_repost_categories: Optional[List[str]] = None
    ):
        """
        Initializes the RepostScheduler.

        Args:
            performance_scorer: An instance of ArticlePerformanceScorer.
            repost_history_filepath: Path to the JSON file for storing repost history.
            min_days_between_reposts: Minimum number of days before an article can be reposted.
            default_repost_categories: Categories to add to all reposts (e.g., ["再掲載"]).
        """
        self.scorer = performance_scorer
        self.history_file = repost_history_filepath or self.DEFAULT_REPOST_HISTORY_FILE
        self.repost_history: Dict[str, ArticleRepostInfo] = self._load_repost_history()
        self.min_days_between_reposts = min_days_between_reposts
        self.default_repost_categories = default_repost_categories or ["再掲載"]

    def _generate_article_id(self, article_url: str) -> str:
        """Generates a consistent ID for an article based on its URL."""
        if not article_url: return "invalid_url_id"
        return hashlib.md5(article_url.encode('utf-8')).hexdigest()[:12]

    def _load_repost_history(self) -> Dict[str, ArticleRepostInfo]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error loading repost history from {self.history_file}: {e}")
        return {}

    def _save_repost_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.repost_history, f, ensure_ascii=False, indent=2)
            logger.info(f"Repost history saved to {self.history_file}")
        except IOError as e:
            logger.error(f"Error saving repost history to {self.history_file}: {e}")

    def _can_repost_article(self, article_id: str) -> bool:
        """Checks if an article can be reposted based on history and min_days."""
        if article_id not in self.repost_history:
            return True # Never reposted

        last_repost_entry = self.repost_history[article_id]['reposts'][-1] if self.repost_history[article_id]['reposts'] else None
        if not last_repost_entry:
            return True

        try:
            last_repost_date = datetime.fromisoformat(last_repost_entry['repost_date'].replace('Z', '+00:00'))
            days_since_last_repost = (datetime.now(timezone.utc) - last_repost_date).days
            return days_since_last_repost >= self.min_days_between_reposts
        except ValueError:
            logger.warning(f"Could not parse last repost date for article ID {article_id}. Assuming it can be reposted.")
            return True # Err on the side of allowing repost if date is malformed

    def select_articles_for_reposting(
        self,
        all_articles_metadata: List[ArticleMetadata],
        max_candidates: int = 10
    ) -> List[ArticleMetadata]:
        """
        Selects articles suitable for reposting from a list of all articles.

        Args:
            all_articles_metadata: List of ArticleMetadata for all available articles.
            max_candidates: Maximum number of repost candidates to return.

        Returns:
            A list of ArticleMetadata for articles selected for reposting,
            ordered by performance and suitability.
        """
        if not all_articles_metadata:
            return []

        # Ensure articles have performance scores (scorer might add it if not present)
        ranked_articles = self.scorer.rank_articles(all_articles_metadata)

        candidates = []
        for article_meta in ranked_articles:
            article_id = self._generate_article_id(article_meta.get('url', ''))
            if not article_id or article_id == "invalid_url_id":
                logger.warning(f"Skipping article with invalid URL: {article_meta.get('title', 'Unknown title')}")
                continue

            if self._can_repost_article(article_id):
                candidates.append(article_meta)
                if len(candidates) >= max_candidates:
                    break

        logger.info(f"Selected {len(candidates)} articles for potential reposting out of {len(all_articles_metadata)}.")
        return candidates

    def _determine_repost_update_type(self, article_meta: ArticleMetadata, proposed_publish_date: datetime) -> str:
        """Determines a suitable update type for the repost (e.g., seasonal, refresh)."""
        # Example logic:
        month = proposed_publish_date.month
        if month in [12, 1, 2] and any(cat in (article_meta.get('categories') or []) for cat in ["イベント", "年末年始"]):
            return "seasonal_event"
        if article_meta.get('performance_score', 0) > 15: # Assuming score indicates popularity
            return "popular_refresh"
        return "content_refresh" # Default

    def _generate_repost_preparation_notes(self, article_meta: ArticleMetadata) -> List[str]:
        """Generates notes for preparing the repost (e.g., check for outdated info)."""
        notes = []
        if article_meta.get('word_count', 0) < 800:
            notes.append("Consider expanding content or combining with related short articles.")

        article_id = self._generate_article_id(article_meta.get('url',''))
        if article_id not in self.repost_history or not self.repost_history[article_id]['reposts']:
            notes.append("This is the first repost for this article.")

        # Add more specific notes based on categories, tags, or content analysis if available
        if "技術" in (article_meta.get('categories') or []) or "Tech" in (article_meta.get('categories') or []):
            notes.append("Verify all technical information, code samples, and links are up-to-date.")
        return notes

    def create_repost_calendar(
        self,
        candidate_articles: List[ArticleMetadata], # Should be pre-selected candidates
        weeks_ahead_to_schedule: int = 4,
        posts_per_week: int = 2
    ) -> List[RepostCandidate]:
        """
        Creates a repost calendar/schedule for the upcoming weeks.

        Args:
            candidate_articles: A list of ArticleMetadata for articles already selected as candidates.
            weeks_ahead_to_schedule: How many weeks into the future to schedule.
            posts_per_week: How many reposts to schedule per week.

        Returns:
            A list of RepostCandidate dictionaries, ordered by suggested publish date.
        """
        if not candidate_articles:
            return []

        calendar: List[RepostCandidate] = []
        total_slots = weeks_ahead_to_schedule * posts_per_week

        # Candidates are already ranked by performance/suitability
        articles_to_schedule = candidate_articles[:total_slots]

        current_schedule_date = datetime.now(timezone.utc)
        # Find next preferred posting day (e.g., next Monday)
        while current_schedule_date.weekday() not in [0, 2]: # Example: Mon or Wed
            current_schedule_date += timedelta(days=1)
        current_schedule_date = current_schedule_date.replace(hour=10, minute=0, second=0, microsecond=0) # e.g. 10 AM UTC

        day_increment = 7 / posts_per_week if posts_per_week > 0 else 7 # Spread posts across the week

        for i, article_meta in enumerate(articles_to_schedule):
            # Simple scheduling: distribute evenly
            if i > 0 and i % posts_per_week == 0: # Start of a new week
                current_schedule_date += timedelta(days= (7 - (day_increment * (posts_per_week-1))) ) # Jump to next week's first slot
                while current_schedule_date.weekday() not in [0,2]: current_schedule_date+=timedelta(days=1) # Ensure it's a posting day
            elif i > 0 :
                 current_schedule_date += timedelta(days=day_increment)


            update_type = self._determine_repost_update_type(article_meta, current_schedule_date)
            prep_notes = self._generate_repost_preparation_notes(article_meta)

            calendar_entry: RepostCandidate = {
                "article_metadata": article_meta,
                "suggested_publish_date": current_schedule_date.isoformat(),
                "suggested_update_type": update_type,
                "preparation_notes": prep_notes,
            }
            calendar.append(calendar_entry)

        logger.info(f"Generated repost calendar with {len(calendar)} entries for the next {weeks_ahead_to_schedule} weeks.")
        return calendar

    def generate_repost_content_from_candidate(
        self,
        candidate: RepostCandidate,
        original_article_full_content: str, # HTML content of original article
        additional_updates: Optional[List[str]] = None
    ) -> RepostContent:
        """
        Generates the actual title, content, and categories for a repost.

        Args:
            candidate: A RepostCandidate dictionary from the calendar.
            original_article_full_content: The full HTML content of the original article.
            additional_updates: List of strings describing new updates to include.

        Returns:
            A RepostContent dictionary ready for publishing.
        """
        original_meta = candidate['article_metadata']
        update_type = candidate['suggested_update_type']

        original_title = original_meta.get('title', 'Untitled Article')
        original_url = original_meta.get('url', '#')
        article_id = self._generate_article_id(original_url)

        # Create intro based on update type
        intro_prefix = "【再掲】"
        if update_type == "popular_refresh":
            intro_prefix = f"【人気記事 {datetime.now().year}年版】"
        elif update_type == "content_refresh":
            intro_prefix = f"【{datetime.now().year}年 更新版】"
        elif update_type == "seasonal_event":
            intro_prefix = "【季節のオススメ】"

        new_title = f"{intro_prefix} {original_title}"

        # Construct repost content
        intro_html = f'<div class="repost-intro"><p>{intro_prefix}この記事は、過去に公開した「<a href="{original_url}">{original_title}</a>」を加筆・修正したものです。</p></div>'

        updates_html = ""
        if additional_updates:
            updates_list_html = "".join([f"<li>{update}</li>" for update in additional_updates])
            updates_html = f'<div class="repost-updates"><h3>主な更新点：</h3><ul>{updates_list_html}</ul></div>'

        # Basic footer
        footer_html = f'<div class="repost-footer"><p>元記事：<a href="{original_url}" rel="noopener" target="_blank">{original_title}</a> ({original_meta.get("date_published", "過去の投稿")[:10]})</p></div>'

        # Combine parts. Ensure original content is not overly nested or escaped.
        # Assuming original_article_full_content is the main body HTML.
        final_content = f"{intro_html}\n{updates_html}\n<hr>\n{original_article_full_content}\n<hr>\n{footer_html}"

        # Categories
        final_categories = list(set((original_meta.get('categories') or []) + self.default_repost_categories))

        return {
            "title": new_title,
            "content": final_content,
            "categories": final_categories,
            "original_article_url": original_url,
            "original_article_id": article_id,
            "update_type": update_type
        }

    def record_repost_in_history(
        self,
        original_article_id: str,
        original_article_url: str,
        original_article_title: str, # Added for better history readability
        original_article_date: Optional[str], # Added
        reposted_title: str,
        repost_url: Optional[str], # The URL of the new repost
        update_type: str
    ):
        """Records a successful repost in the history."""
        if original_article_id not in self.repost_history:
            self.repost_history[original_article_id] = {
                "original_url": original_article_url,
                "original_title": original_article_title,
                "original_date": original_article_date,
                "reposts": []
            }

        repost_entry: RepostHistoryEntry = {
            "repost_date": datetime.now(timezone.utc).isoformat(),
            "reposted_title": reposted_title,
            "repost_url": repost_url,
            "update_type": update_type
        }
        self.repost_history[original_article_id]['reposts'].append(repost_entry)
        self._save_repost_history()
        logger.info(f"Recorded repost for original article ID {original_article_id} (URL: {repost_url})")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("--- Testing RepostScheduler ---")

    # Dummy performance scorer for testing
    class DummyScorer(ArticlePerformanceScorer):
        def rank_articles(self, articles_meta: List[ArticleMetadata]) -> List[ArticleMetadata]:
            # Assign dummy scores and sort by date as a simple ranking for test
            for i, meta in enumerate(articles_meta):
                meta['performance_score'] = 10 - i # Higher score for earlier in list
            return sorted(articles_meta, key=lambda x: x.get('date_published', '0'), reverse=True)

    test_scorer = DummyScorer() # Use the actual scorer if you have its definition

    # Sample articles (ensure 'date_published' is in ISO format)
    now_dt = datetime.now(timezone.utc)
    sample_articles_for_repost: List[ArticleMetadata] = [
        {"id": "artA", "title": "Evergreen Content A", "url": "http://example.com/a",
         "date_published": (now_dt - timedelta(days=300)).isoformat(), "word_count": 1500, "categories": ["Guide"]},
        {"id": "artB", "title": "Outdated Tech Post B", "url": "http://example.com/b",
         "date_published": (now_dt - timedelta(days=700)).isoformat(), "word_count": 1200, "categories": ["Tech"]},
        {"id": "artC", "title": "Recent Gem C", "url": "http://example.com/c",
         "date_published": (now_dt - timedelta(days=100)).isoformat(), "word_count": 800, "categories": ["Tips"]},
        {"id": "artD", "title": "Already Reposted D", "url": "http://example.com/d",
         "date_published": (now_dt - timedelta(days=400)).isoformat()},
        {"id": "artE", "title": "Very Old but Gold E", "url": "http://example.com/e",
         "date_published": (now_dt - timedelta(days=1000)).isoformat(), "word_count": 2000, "categories": ["Deep Dive"]},
    ]

    # Create a scheduler instance
    test_history_file = "test_repost_history.json"
    if os.path.exists(test_history_file): os.remove(test_history_file) # Clean start for test

    scheduler = RepostScheduler(performance_scorer=test_scorer, repost_history_filepath=test_history_file)

    # Simulate that article D was reposted 20 days ago
    artD_id = scheduler._generate_article_id("http://example.com/d")
    scheduler.repost_history[artD_id] = {
        "original_url": "http://example.com/d", "original_title": "Already Reposted D", "original_date": (now_dt - timedelta(days=400)).isoformat(),
        "reposts": [{
            "repost_date": (now_dt - timedelta(days=20)).isoformat(),
            "reposted_title": "[RE] Reposted D", "repost_url": "http://example.com/d-repost1", "update_type": "minor_update"
        }]
    }
    scheduler._save_repost_history()


    print("\\n--- Selecting Articles for Reposting ---")
    candidates_meta = scheduler.select_articles_for_reposting(sample_articles_for_repost, max_candidates=3)
    print(f"Selected {len(candidates_meta)} candidates:")
    for cand_meta in candidates_meta:
        print(f"  - {cand_meta['title']} (Score: {cand_meta.get('performance_score', 'N/A')})")
    # Expected: artD should be excluded due to recent repost. Others selected based on scorer's ranking.


    print("\\n--- Creating Repost Calendar ---")
    # We need scores from the scorer for candidate_articles
    ranked_sample_articles = test_scorer.rank_articles(sample_articles_for_repost)
    # Filter out already reposted for calendar generation (select_articles_for_reposting does this)
    # For this test, let's use the `candidates_meta` which is already filtered

    calendar = scheduler.create_repost_calendar(candidates_meta, weeks_ahead_to_schedule=2, posts_per_week=1)
    print(f"Generated calendar with {len(calendar)} entries:")
    for entry in calendar:
        print(f"  - Date: {entry['suggested_publish_date'][:10]}, Title: {entry['article_metadata']['title']}, Update: {entry['suggested_update_type']}")
        print(f"    Notes: {'; '.join(entry['preparation_notes'])}")


    print("\\n--- Generating Repost Content for first candidate ---")
    if calendar:
        first_candidate_for_content = calendar[0]
        # Simulate having original content
        original_html_content = f"<p>This is the original amazing content of the article titled '{first_candidate_for_content['article_metadata']['title']}'.</p><p>It has several paragraphs.</p>"
        updates_for_repost = ["Added latest 2024 statistics.", "Updated examples for new Python version."]

        repost_data = scheduler.generate_repost_content_from_candidate(
            first_candidate_for_content,
            original_article_full_content=original_html_content,
            additional_updates=updates_for_repost
        )
        print(f"Generated Repost Title: {repost_data['title']}")
        print(f"Generated Repost Categories: {repost_data['categories']}")
        # print(f"Generated Repost Content Snippet:\n{repost_data['content'][:300]}...")

        print("\\n--- Recording Repost in History (Simulated) ---")
        scheduler.record_repost_in_history(
            original_article_id=repost_data['original_article_id'],
            original_article_url=repost_data['original_article_url'],
            original_article_title=first_candidate_for_content['article_metadata']['title'], # Get original title
            original_article_date=first_candidate_for_content['article_metadata'].get('date_published'),
            reposted_title=repost_data['title'],
            repost_url=f"{repost_data['original_article_url']}-repost2", # Simulated new URL
            update_type=repost_data['update_type']
        )
        # Verify artD is still not repostable, and the newly recorded one is also not immediately repostable
        can_repost_artD_again = scheduler._can_repost_article(artD_id)
        can_repost_newly_recorded_again = scheduler._can_repost_article(repost_data['original_article_id'])
        print(f"Can repost ArtD again immediately: {can_repost_artD_again}")
        print(f"Can repost '{first_candidate_for_content['article_metadata']['title']}' again immediately: {can_repost_newly_recorded_again}")
        assert not can_repost_artD_again
        assert not can_repost_newly_recorded_again

    else:
        print("Calendar is empty, skipping content generation test.")

    if os.path.exists(test_history_file): os.remove(test_history_file) # Clean up
    print("\\nRepostScheduler tests finished.")
