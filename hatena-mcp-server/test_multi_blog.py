#!/usr/bin/env python3
"""Test script for multi-blog functionality and authentication fixes"""

import sys
import os
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_hatena_agent import EnhancedHatenaAgent

def test_authentication():
    """Test authentication for all configured blogs"""
    print("🔐 Testing Authentication")
    print("=" * 50)
    
    agent = EnhancedHatenaAgent()
    result = agent.test_blog_authentication()
    
    if result["status"] == "success":
        for blog_name, auth_result in result["results"].items():
            status = "✅ SUCCESS" if auth_result["status"] == "success" else "❌ FAILED"
            print(f"{blog_name}: {status}")
            if auth_result["status"] == "error":
                print(f"  Error: {auth_result['message']}")
    else:
        print(f"❌ Test failed: {result['message']}")
    
    return result

def test_list_blogs():
    """Test listing all configured blogs"""
    print("\\n📚 Listing Configured Blogs")
    print("=" * 50)
    
    agent = EnhancedHatenaAgent()
    result = agent.list_blogs()
    
    if result["status"] == "success":
        print(f"Found {result['count']} configured blogs:")
        for blog in result["blogs"]:
            print(f"  • {blog['name']}: {blog['description']}")
            print(f"    Domain: {blog['blog_domain']}")
            print(f"    Hatena ID: {blog['hatena_id']}")
            print()
    else:
        print(f"❌ Failed to list blogs: {result['message']}")
    
    return result

def test_get_articles():
    """Test getting articles from each blog"""
    print("\\n📄 Testing Article Retrieval")
    print("=" * 50)
    
    agent = EnhancedHatenaAgent()
    blogs = agent.list_blogs()
    
    if blogs["status"] != "success":
        print("❌ Cannot test articles - failed to get blog list")
        return
    
    for blog in blogs["blogs"]:
        blog_name = blog["name"]
        print(f"\\nTesting {blog_name}...")
        
        result = agent.get_articles(blog_name, limit=3)
        if result["status"] == "success":
            print(f"✅ Found {result['total_found']} articles")
            for i, article in enumerate(result["articles"][:3], 1):
                print(f"  {i}. {article['title'][:50]}...")
                print(f"     ID: {article['id']}")
                print(f"     Categories: {', '.join(article['categories'])}")
        else:
            print(f"❌ Failed: {result['message']}")

def test_search_functionality():
    """Test article search functionality"""
    print("\\n🔍 Testing Search Functionality")
    print("=" * 50)
    
    agent = EnhancedHatenaAgent()
    
    # Test search in lifehack_blog for articles containing "登山" or "キャンプ"
    search_terms = ["登山", "キャンプ", "アウトドア"]
    
    for term in search_terms:
        print(f"\\nSearching for '{term}' in lifehack_blog...")
        result = agent.search_articles_by_title("lifehack_blog", term)
        
        if result["status"] == "success":
            print(f"✅ Found {result['found_count']} articles")
            for article in result["articles"][:2]:  # Show first 2
                print(f"  • {article['title']}")
                print(f"    ID: {article['id']}")
        else:
            print(f"❌ Search failed: {result['message']}")

def test_migration_candidates():
    """Test getting migration candidates"""
    print("\\n🚛 Testing Migration Candidate Detection")
    print("=" * 50)
    
    agent = EnhancedHatenaAgent()
    
    # Look for articles in lifehack_blog that might be suitable for mountain_blog
    result = agent.get_migration_candidates("lifehack_blog")
    
    if result["status"] == "success":
        print(f"✅ Found {result['candidate_count']} potential candidates")
        
        # Look for outdoor/mountain related articles
        outdoor_articles = []
        for article in result["candidates"]:
            title_lower = article["title"].lower()
            if any(keyword in title_lower for keyword in ["登山", "山", "キャンプ", "アウトドア", "ハイキング"]):
                outdoor_articles.append(article)
        
        if outdoor_articles:
            print(f"\\n🏔️ Found {len(outdoor_articles)} mountain/outdoor related articles:")
            for article in outdoor_articles[:5]:  # Show first 5
                print(f"  • {article['title']}")
                print(f"    ID: {article['id']}")
                print(f"    Categories: {', '.join(article['categories'])}")
                print()
        else:
            print("\\n📝 No obvious mountain/outdoor articles found by keyword search")
    else:
        print(f"❌ Failed to get candidates: {result['message']}")

def demo_migration():
    """Demo article migration (dry run)"""
    print("\\n🔄 Demo: Article Migration Process")
    print("=" * 50)
    
    print("This would migrate articles from ライフハックブログ to 登山ブログ")
    print("\\nStep 1: Identify articles about outdoor activities")
    print("Step 2: Copy article content with migration note")
    print("Step 3: Post to target blog as draft")
    print("Step 4: Verify successful migration")
    print("\\n💡 Use copy_mode=True for safe migration (keeps original)")
    print("💡 All migrated articles are posted as drafts for review")

def main():
    """Run all tests"""
    print("🎌 Hatena Multi-Blog System Test Suite")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    try:
        # Test 1: Authentication
        auth_result = test_authentication()
        
        # Test 2: List blogs
        blogs_result = test_list_blogs()
        
        # Test 3: Get articles
        test_get_articles()
        
        # Test 4: Search functionality
        test_search_functionality()
        
        # Test 5: Migration candidates
        test_migration_candidates()
        
        # Test 6: Demo migration
        demo_migration()
        
        print("\\n" + "=" * 60)
        print("🎉 Test Suite Complete!")
        
        # Summary
        auth_success = auth_result.get("status") == "success"
        blogs_success = blogs_result.get("status") == "success"
        
        if auth_success and blogs_success:
            print("✅ System is ready for multi-blog operations!")
            print("\\n💡 Next steps:")
            print("  1. Review authentication results")
            print("  2. Use enhanced_hatena_agent.py for operations")
            print("  3. Test article migration with copy_mode=True")
        else:
            print("⚠️  Some issues detected - review authentication setup")
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()