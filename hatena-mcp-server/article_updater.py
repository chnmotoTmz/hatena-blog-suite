# article_updater.py

from api_utils import generate_summary_cohere as generate_summary
from api_utils import extract_keywords_cohere as extract_keywords
from rakuten_api import search_products, generate_affiliate_link
from image_creator import generate_image_from_prompt
from utils import find_internal_links
import os 
import logging

# New function signature for the tool
def enhance_article_content_operations(content: str, keywords_prompt: str, internal_links_url: str, image_prompt: str, article_title: str) -> str:
    """
    Enhances article HTML content using AI rewrite, keyword-based affiliate/internal links, and a generated image.
    (This is a placeholder body)
    """
    logging.info(f"Starting content enhancement for article: {article_title}")
    
    # 1. AIによる記事リライト
    try:
        updated_content = generate_summary(content, length="long")
        logging.info("Content summarization/rewrite successful.")
    except Exception as e:
        logging.error(f"Error during content summarization/rewrite: {e}")
        updated_content = content # Fallback to original content

    # 2. 主要語句の抽出とアフィリエイトリンク生成
    current_processing_content = updated_content
    try:
        keywords = extract_keywords(keywords_prompt, num_keywords=10)
        logging.info(f"Extracted keywords: {keywords}")
        for keyword in keywords:
            products = search_products(keyword) # Expects RAKUTEN_API_KEY to be available via os.getenv
            if products and isinstance(products, list) and len(products) > 0:
                product = products[0]
                if isinstance(product, dict) and "itemCode" in product:
                    affiliate_link = generate_affiliate_link(product["itemCode"]) # Expects RAKUTEN_API_KEY
                    current_processing_content = current_processing_content.replace(
                        keyword, f'<a href="{affiliate_link}">{keyword}</a>'
                    )
                    logging.info(f"Added affiliate link for keyword: {keyword}")
                else:
                    logging.warning(f"No itemCode found or product is not a dict for keyword '{keyword}'. Product: {product}")
            else:
                logging.info(f"No products found for keyword: {keyword}")
    except Exception as e:
        logging.error(f"Error during keyword extraction or affiliate linking: {e}")

    # 3. 同サイト内の類似テーマ記事へのリンク挿入
    try:
        internal_links = find_internal_links(current_processing_content, internal_links_url) # from utils.py
        if internal_links: # Assuming find_internal_links returns a list of (text, url) tuples or similar
            links_html = "\n".join([f'<p>関連:<a href="{link_url}">{link_text}</a></p>' for link_text, link_url in internal_links])
            current_processing_content += "\n" + links_html
            logging.info(f"Added {len(internal_links)} internal links.")
    except Exception as e:
        logging.error(f"Error during internal link insertion: {e}")

    # 4. 画像プロンプトに基づく画像の挿入
    try:
        logging.info(f"Generating image with prompt: {image_prompt}")
        image_url = generate_image_from_prompt(image_prompt) # from image_creator.py
        if image_url:
            current_processing_content += f'<img src="{image_url}" alt="{article_title}">'
            logging.info(f"Successfully added generated image: {image_url}")
        else:
            logging.warning("Image generation returned no URL.")
    except Exception as e:
        logging.error(f"Error generating or inserting image: {e}")

    logging.info(f"Content enhancement finished for article: {article_title}")
    return current_processing_content

# Original update_article function commented out
# def update_article(entry):
#     # 1. AIによる記事リライト (2000文字以上)
#     updated_content = generate_summary(entry["content"], length="long")

    # 2. 主要語句の抽出とアフィリエイトリンク生成
    keywords = extract_keywords(updated_content, num_keywords=10)
    for keyword in keywords:
        products = search_products(keyword)
        if products:
            affiliate_link = generate_affiliate_link(products[0]["itemCode"])
            updated_content = updated_content.replace(
                keyword, f'<a href="{affiliate_link}">{keyword}</a>'
            )

    # 3. 同サイト内の類似テーマ記事へのリンク挿入
    internal_links = find_internal_links(updated_content, entry["url"])
    for link in internal_links:
        updated_content += f'<a href="{link}">{link}</a>'

    # 4. 画像プロンプトに基づく画像の挿入
    image_url = generate_image_from_prompt(entry["image_prompt"])
    updated_content += f'<img src="{image_url}" alt="{entry["title"]}">'

#     # 5. 記事情報の更新
#     entry["content"] = updated_content
#
#     return entry