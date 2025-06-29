from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypedDict
import logging

logger = logging.getLogger(__name__)

class ArticleMetadata(TypedDict, total=False):
    """
    Represents the metadata for an article used in performance analysis.
    Fields are optional as not all data sources may provide them.
    """
    id: str
    title: str
    url: str
    date_published: Optional[str]  # ISO 8601 format string (e.g., "2023-10-26T14:30:00Z")
    categories: Optional[List[str]]
    tags: Optional[List[str]]
    word_count: Optional[int]
    view_count: Optional[int]       # Example: if available from analytics
    comment_count: Optional[int]    # Example: if available
    social_shares: Optional[Dict[str, int]] # Example: {"twitter": 10, "facebook": 5}
    # Add other relevant metrics as needed

class ArticlePerformanceScorer:
    """
    Calculates a performance score for articles based on their metadata.
    The scoring logic can be customized by adjusting weights.
    """

    DEFAULT_SCORING_WEIGHTS = {
        "recency_days": { # Score based on how old the article is (days)
            30: 2,   # Articles older than 30 days get 2 points
            90: 5,   # Articles older than 90 days get 5 points
            180: 10, # Articles older than 180 days get 10 points
        },
        "category_count_bonus": 3, # Bonus if article has at least one category
        "tag_count_bonus": 1,      # Bonus if article has at least one tag
        "word_count_tiers": {
            300: 1,   # Word count > 300 gets 1 point
            800: 3,   # Word count > 800 gets 3 points (cumulative with previous)
            1500: 5,  # Word count > 1500 gets 5 points (cumulative)
        },
        "view_count_per_1000": 2,  # Points per 1000 views
        "comment_count_per_comment": 1, # Points per comment
        "social_share_per_10_shares": 1, # Points per 10 total social shares
    }

    def __init__(self, scoring_weights: Optional[Dict[str, Any]] = None):
        """
        Initializes the ArticlePerformanceScorer.

        Args:
            scoring_weights: Optional dictionary to override default scoring weights.
        """
        self.weights = scoring_weights if scoring_weights is not None else self.DEFAULT_SCORING_WEIGHTS

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Safely parses a date string into a datetime object."""
        if not date_str:
            return None
        try:
            # Attempt to parse ISO format, handling potential 'Z' for UTC
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Ensure it's offset-aware for correct comparison with datetime.now(timezone.utc)
            if dt.tzinfo is None:
                 # Naive datetime, assume UTC if no timezone info or make configurable
                 # For simplicity here, let's assume UTC if naive.
                 # dt = dt.replace(tzinfo=timezone.utc)
                 # Or, better, make it explicit that input should be TZ-aware or handle based on policy.
                 # For now, we'll compare with naive now() if input is naive.
                 pass # Keep it naive if input is naive
            return dt
        except ValueError:
            logger.warning(f"Could not parse date string: '{date_str}'. Supported format is ISO 8601.")
            # Try other common formats as a fallback if needed
            # Example: datetime.strptime(date_str, '%Y-%m-%d')
        return None

    def calculate_score(self, article_meta: ArticleMetadata) -> float:
        """
        Calculates the performance score for a single article.

        Args:
            article_meta: An ArticleMetadata dictionary.

        Returns:
            The calculated performance score (float).
        """
        score = 0.0

        # 1. Recency Score
        published_date_obj = self._parse_date(article_meta.get('date_published'))
        if published_date_obj:
            # Ensure comparison is between offset-aware and offset-naive datetimes consistently
            now = datetime.now(timezone.utc) if published_date_obj.tzinfo else datetime.now()
            days_old = (now - published_date_obj).days

            recency_tiers = self.weights.get("recency_days", {})
            for days_threshold, points in sorted(recency_tiers.items()): # Iterate sorted by days
                if days_old > days_threshold:
                    score += points

        # 2. Category Bonus
        if article_meta.get('categories'): # Checks for non-empty list
            score += self.weights.get("category_count_bonus", 0)

        # 3. Tag Bonus
        if article_meta.get('tags'): # Checks for non-empty list
            score += self.weights.get("tag_count_bonus", 0)

        # 4. Word Count Score
        word_count = article_meta.get('word_count', 0)
        if word_count:
            word_count_tiers = self.weights.get("word_count_tiers", {})
            current_tier_score = 0
            for wc_threshold, points in sorted(word_count_tiers.items()):
                if word_count > wc_threshold:
                    current_tier_score = points # Takes the highest applicable tier's points directly
            score += current_tier_score
            # If you want cumulative points for word count tiers, the logic would be different:
            # for wc_threshold, points in sorted(word_count_tiers.items()):
            #     if word_count > wc_threshold:
            #         score += points # This would add points for each tier passed

        # 5. View Count Score (Example - if available)
        view_count = article_meta.get('view_count', 0)
        if view_count and self.weights.get("view_count_per_1000", 0) > 0:
            score += (view_count / 1000) * self.weights.get("view_count_per_1000", 0)

        # 6. Comment Count Score (Example - if available)
        comment_count = article_meta.get('comment_count', 0)
        if comment_count:
            score += comment_count * self.weights.get("comment_count_per_comment", 0)

        # 7. Social Shares Score (Example - if available)
        social_shares_data = article_meta.get('social_shares', {})
        if social_shares_data and self.weights.get("social_share_per_10_shares", 0) > 0:
            total_shares = sum(social_shares_data.values())
            score += (total_shares / 10) * self.weights.get("social_share_per_10_shares", 0)

        return round(score, 2)

    def rank_articles(self, articles_metadata: List[ArticleMetadata]) -> List[Dict[str, Any]]:
        """
        Calculates scores for a list of articles and ranks them.

        Args:
            articles_metadata: A list of ArticleMetadata dictionaries.

        Returns:
            A list of dictionaries, each containing the original metadata
            and the calculated 'performance_score', sorted by score descending.
        """
        if not articles_metadata:
            return []

        scored_articles = []
        for meta in articles_metadata:
            score = self.calculate_score(meta)
            scored_article_info = {**meta, "performance_score": score} # Combine original meta with score
            scored_articles.append(scored_article_info)

        # Sort by performance_score descending, then perhaps by date descending as tie-breaker
        scored_articles.sort(
            key=lambda x: (
                x["performance_score"],
                self._parse_date(x.get("date_published")) or datetime.min.replace(tzinfo=timezone.utc) # Handle None dates
            ),
            reverse=True
        )
        return scored_articles


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("--- Testing ArticlePerformanceScorer ---")

    scorer = ArticlePerformanceScorer()

    sample_articles: List[ArticleMetadata] = [
        {
            "id": "art1", "title": "Old Popular Article",
            "date_published": "2022-01-15T10:00:00Z",
            "categories": ["Tech", "Python"], "tags": ["programming", "guide"],
            "word_count": 2000, "view_count": 50000, "comment_count": 25,
            "social_shares": {"twitter": 150, "facebook": 80}
        },
        {
            "id": "art2", "title": "Recent Short Article",
            "date_published": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(), # 15 days ago
            "categories": ["News"], "tags": [],
            "word_count": 400, "view_count": 1500, "comment_count": 2
        },
        {
            "id": "art3", "title": "Medium Article, Mid-Age",
            "date_published": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat(), # 100 days ago
            "categories": ["Lifestyle"], "tags": ["tips", "general"],
            "word_count": 900, "view_count": 8000, "comment_count": 5,
            "social_shares": {"pinterest": 30}
        },
        {
            "id": "art4", "title": "Article with No Date",
            "categories": ["Misc"], "word_count": 600
        },
         {
            "id": "art5", "title": "Very Recent, High Engagement",
            "date_published": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(), # 5 days ago
            "categories": ["Hot Topic"], "tags": ["breaking", "discussion"],
            "word_count": 1200, "view_count": 12000, "comment_count": 50,
            "social_shares": {"twitter": 200, "linkedin": 70}
        }
    ]

    print("\\n--- Calculating Scores for Individual Articles ---")
    for article_data in sample_articles:
        score = scorer.calculate_score(article_data)
        print(f"Article: '{article_data['title']}', Calculated Score: {score}")

    print("\\n--- Ranking Articles ---")
    ranked_articles_list = scorer.rank_articles(sample_articles)
    print("Ranked Articles (Top to Bottom):")
    for i, article_info in enumerate(ranked_articles_list):
        print(f"  {i+1}. '{article_info['title']}' - Score: {article_info['performance_score']} "
              f"(Date: {article_info.get('date_published', 'N/A')}, WC: {article_info.get('word_count',0)})")

    # Test with custom weights
    custom_weights = {
        "recency_days": {30: 1, 90: 2, 180: 3}, # Lower recency impact
        "category_count_bonus": 5,             # Higher category bonus
        "word_count_tiers": {500: 2, 1000: 5}, # Different word count tiers
        "view_count_per_1000": 5,              # Higher view count impact
        "comment_count_per_comment": 2,
    }
    print("\\n--- Testing with Custom Weights ---")
    custom_scorer = ArticlePerformanceScorer(scoring_weights=custom_weights)
    custom_ranked_list = custom_scorer.rank_articles(sample_articles)
    print("Ranked Articles (Custom Weights):")
    for i, article_info in enumerate(custom_ranked_list):
        print(f"  {i+1}. '{article_info['title']}' - Score: {article_info['performance_score']}")

    # Check if ranking changed (it likely will)
    if ranked_articles_list and custom_ranked_list and \
       ranked_articles_list[0]['id'] != custom_ranked_list[0]['id']:
        print("Note: Top ranked article changed with custom weights.")

    print("\\nArticlePerformanceScorer tests finished.")
