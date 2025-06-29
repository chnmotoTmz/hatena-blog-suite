#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from src.agents.article_extractor import HatenaArticleExtractor
from src.agents.retrieval_agent import RetrievalAgent
from src.agents.image_generator import ImageGenerator
from src.agents.affiliate_manager import AffiliateManager
from src.agents.repost_manager import RepostManager
from src.agents.link_checker import LinkChecker
from src.agents.personalization_agent import PersonalizationAgent
from src.agents.knowledge_network import KnowledgeNetworkManager


def get_blog_config():
    target_blog = os.getenv('TARGET_BLOG', 'blog1')
    
    if target_blog not in ['blog1', 'blog2', 'blog3']:
        print(f"Error: Invalid TARGET_BLOG '{target_blog}'. Must be blog1, blog2, or blog3.")
        return None
    
    hatena_id = os.getenv(f'{target_blog.upper()}_HATENA_ID')
    blog_domain = os.getenv(f'{target_blog.upper()}_DOMAIN')
    atompub_key = os.getenv(f'{target_blog.upper()}_ATOMPUB_KEY')
    
    if not hatena_id or not blog_domain:
        print(f"Error: {target_blog.upper()}_HATENA_ID and {target_blog.upper()}_DOMAIN are required.")
        return None
    
    return {
        'target_blog': target_blog,
        'hatena_id': hatena_id,
        'blog_domain': blog_domain,
        'atompub_key': atompub_key
    }


def main():
    load_dotenv()
    
    blog_config = get_blog_config()
    if not blog_config:
        return
    
    hatena_id = blog_config['hatena_id']
    blog_domain = blog_config['blog_domain']
    target_blog = blog_config['target_blog']
    
    output_dir = f'./output_{target_blog}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Target Blog: {target_blog} ({blog_domain})")
    print("Step 1: Extracting articles from Hatena Blog...")
    extractor = HatenaArticleExtractor(hatena_id, blog_domain)
    articles = extractor.extract_all_articles(max_pages=5)
    
    print(f"Found {len(articles)} articles")
    
    for i, article in enumerate(articles[:10]):
        print(f"Extracting full content for article {i+1}/{min(10, len(articles))}")
        full_content = extractor.extract_article_content(article['url'])
        article.update(full_content)
    
    extractor.save_articles_to_json(
        articles, 
        os.path.join(output_dir, 'extracted_articles.json')
    )
    print("Articles saved to extracted_articles.json")
    
    print("\nStep 2: Setting up enhancement features...")
    
    print("\nStep 3: Setting up affiliate manager...")
    affiliate_manager = AffiliateManager()
    rakuten_tag = os.getenv('RAKUTEN_AFFILIATE_TAG')
    if rakuten_tag:
        affiliate_manager.set_affiliate_tag('rakuten', rakuten_tag)
    
    print("\nStep 4: Processing sample article with enhancements...")
    if articles and articles[0].get('full_content'):
        sample_article = articles[0]
        
        enhanced_content = sample_article['full_content']
        enhanced_content, processed_urls = affiliate_manager.process_article_content(
            enhanced_content,
            auto_detect=True
        )
        
        print("\nStep 5: Generating images for article...")
        bing_cookie = os.getenv('BING_AUTH_COOKIE')
        if bing_cookie:
            image_generator = ImageGenerator(
                bing_auth_cookie=bing_cookie,
                output_dir=os.path.join(output_dir, 'images')
            )
            
            featured_image = image_generator.create_featured_image(
                sample_article['title'],
                sample_article.get('summary', sample_article['title']),
                style_preference="modern minimalist blog header"
            )
            if featured_image:
                print(f"Featured image created: {featured_image}")
            
            image_generator.close_session()
        else:
            print("Bing cookie not found, skipping image generation")
            featured_image = None
        
        with open(os.path.join(output_dir, 'enhanced_sample.html'), 'w', encoding='utf-8') as f:
            f.write(f"<h1>{sample_article['title']}</h1>\n")
            if featured_image:
                f.write(f"<img src='{featured_image}' alt='Featured Image'>\n")
            f.write(enhanced_content)
        
        print("Enhanced sample saved to enhanced_sample.html")
        
        if processed_urls:
            affiliate_report = affiliate_manager.generate_affiliate_report(processed_urls)
            with open(os.path.join(output_dir, 'affiliate_report.md'), 'w', encoding='utf-8') as f:
                f.write(affiliate_report)
            print("Affiliate report saved to affiliate_report.md")
    
    print("\nStep 6: Setting up repost manager...")
    
    repost_manager = RepostManager(hatena_id, blog_domain)
    
    print("Analyzing article performance...")
    performance_data = repost_manager.analyze_article_performance(articles)
    
    print("\nTop 5 articles by performance score:")
    for i, article in enumerate(performance_data[:5]):
        print(f"{i+1}. {article['title']} (Score: {article['performance_score']})")
    
    print("\nGenerating repost calendar...")
    calendar = repost_manager.generate_repost_calendar(articles, weeks_ahead=4)
    repost_manager.export_repost_plan(
        calendar, 
        os.path.join(output_dir, 'repost_calendar.json')
    )
    
    print(f"Repost calendar created with {len(calendar)} articles")
    
    # リポストの実行
    print("\n=== Publishing Scheduled Reposts ===")
    publish_results = repost_manager.publish_scheduled_reposts(
        calendar, 
        dry_run=False,  # 実際に実行
        full_articles_data=articles  # 元記事の完全データを渡す
    )
    
    for result in publish_results:
        if result['status'] == 'success':
            print(f"✓ Published: {result['title']} -> {result['url']}")
        elif result['status'] == 'dry_run':
            print(f"[DRY RUN] Would publish: {result['title']}")
        else:
            print(f"✗ Failed: {result.get('title', 'Unknown')} - {result.get('message', 'Unknown error')}")
    
    if calendar:
        first_repost = calendar[0]
        repost_content = repost_manager.create_repost_content(
            first_repost['article'],
            update_type=first_repost['update_type']
        )
        
        repost_content = repost_manager.update_repost_with_new_info(
            repost_content,
            ["最新の情報を追加しました", "関連リンクを更新しました"]
        )
        
        with open(os.path.join(output_dir, 'sample_repost.html'), 'w', encoding='utf-8') as f:
            f.write(f"<h1>{repost_content['title']}</h1>\n")
            f.write(repost_content['content'])
        
        print("Sample repost saved to sample_repost.html")
    
    print("\n=== Link Checking ===")
    link_checker = LinkChecker()
    
    if articles:
        print("Checking links in articles...")
        link_results = []
        for article in articles[:5]:
            result = link_checker.check_article_links(article)
            link_results.append(result)
            print(f"Checked: {article.get('title', 'Unknown')}")
        
        report = link_checker.generate_link_report(
            link_results, 
            os.path.join(output_dir, 'link_check_report.md')
        )
        print("Link check report saved to link_check_report.md")
    
    print("\n=== Personalization ===")
    personalizer = PersonalizationAgent(
        os.path.join(output_dir, 'user_profile.json')
    )
    
    if articles:
        print("Analyzing writing style...")
        personalizer.analyze_writing_samples(articles)
        
        if articles[0].get('full_content'):
            personalized_content = personalizer.personalize_content(
                articles[0]['full_content']
            )
            
            with open(os.path.join(output_dir, 'personalized_sample.html'), 'w', encoding='utf-8') as f:
                f.write(f"<h1>{articles[0]['title']}</h1>\n")
                f.write(personalized_content)
            
            print("Personalized sample saved to personalized_sample.html")
    
    print("\n=== Knowledge Network ===")
    knowledge_manager = KnowledgeNetworkManager(
        os.path.join(output_dir, 'knowledge_network')
    )
    
    if articles:
        print("Building knowledge graph...")
        network_stats = knowledge_manager.build_knowledge_graph(articles)
        
        map_file = knowledge_manager.generate_knowledge_map_visualization()
        print(f"Knowledge map saved to: {map_file}")
        
        export_file = knowledge_manager.export_for_notebook_lm()
        print(f"NotebookLM export saved to: {export_file}")
        
        report = knowledge_manager.generate_knowledge_report()
        with open(os.path.join(output_dir, 'knowledge_network_report.md'), 'w', encoding='utf-8') as f:
            f.write(report)
        print("Knowledge network report saved to knowledge_network_report.md")

    print("\nAll operations completed successfully!")
    print(f"Output files are in: {output_dir}")


if __name__ == "__main__":
    main()