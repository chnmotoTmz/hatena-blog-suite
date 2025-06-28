#!/usr/bin/env python3
import os
import argparse
from dotenv import load_dotenv
from src.agents.article_extractor import HatenaArticleExtractor
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.image_generator import ImageGenerator
from src.agents.affiliate_manager import AffiliateManager
from src.agents.repost_manager import RepostManager
from src.agents.link_checker import LinkChecker
from src.agents.personalization_agent import PersonalizationAgent
from src.agents.knowledge_network import KnowledgeNetworkManager


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='HATENA Agent - Blog Content Management System')
    parser.add_argument('--hatena-id', help='Your Hatena Blog ID (or set HATENA_BLOG_ID env var)')
    parser.add_argument('--mode', choices=['extract', 'enhance', 'repost', 'full', 'linkcheck', 'personalize', 'network'], 
                       default='full', help='Operation mode')
    parser.add_argument('--output-dir', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # はてなブログIDを環境変数または引数から取得
    hatena_id = args.hatena_id or os.getenv('HATENA_BLOG_ID')
    if not hatena_id:
        print("Error: Hatena Blog ID is required. Set HATENA_BLOG_ID environment variable or use --hatena-id option.")
        return
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    if args.mode in ['extract', 'full']:
        print("Step 1: Extracting articles from Hatena Blog...")
        blog_domain = os.getenv('BLOG_DOMAIN')
        extractor = HatenaArticleExtractor(hatena_id, blog_domain)
        articles = extractor.extract_all_articles(max_pages=5)
        
        print(f"Found {len(articles)} articles")
        
        for i, article in enumerate(articles[:10]):
            print(f"Extracting full content for article {i+1}/{min(10, len(articles))}")
            full_content = extractor.extract_article_content(article['url'])
            article.update(full_content)
        
        extractor.save_articles_to_json(
            articles, 
            os.path.join(args.output_dir, 'extracted_articles.json')
        )
        print("Articles saved to extracted_articles.json")
    
    print("\nAll operations completed successfully!")
    print(f"Output files are in: {args.output_dir}")


if __name__ == "__main__":
    main()