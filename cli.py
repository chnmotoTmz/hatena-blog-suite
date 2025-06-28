#!/usr/bin/env python3
"""
Hatena Blog Suite - Minimal CLI
軽量版コマンドラインツール
"""

import argparse
import os
from core.hatena_client import HatenaClient


def main():
    parser = argparse.ArgumentParser(description='Hatena Blog Suite - Minimal')
    parser.add_argument('--blog-id', required=True, help='Hatena Blog ID')
    parser.add_argument('--count', type=int, default=5, help='Max articles')
    parser.add_argument('--output', default='articles.json', help='Output file')
    
    args = parser.parse_args()
    
    print(f"Extracting from {args.blog_id}...")
    
    # 記事抽出
    client = HatenaClient(args.blog_id)
    articles = client.get_articles(args.count)
    
    # 詳細取得
    for article in articles:
        print(f"Getting: {article['title']}")
        article['content'] = client.get_content(article['url'])
    
    # 保存
    client.save_json(articles, args.output)
    print(f"Saved {len(articles)} articles to {args.output}")


if __name__ == '__main__':
    main()