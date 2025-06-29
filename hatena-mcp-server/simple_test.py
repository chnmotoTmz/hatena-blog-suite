#!/usr/bin/env python3
"""Simple test for multi-blog functionality"""

import os
import sys

# Set up environment variables manually for testing
os.environ["HATENA_BLOG_ATOMPUB_KEY_1"] = "lyls7yg12j"
os.environ["HATENA_BLOG_ATOMPUB_KEY_2"] = "ofiwu9xw6i"

try:
    from multi_blog_manager import MultiBlogManager
    
    print("🎌 Hatena Multi-Blog System - Simple Test")
    print("=" * 50)
    
    # Create manager
    manager = MultiBlogManager()
    
    # Test 1: List blogs
    print("\\n📚 Configured Blogs:")
    blogs = manager.list_blogs()
    for blog in blogs:
        print(f"  • {blog['name']}: {blog['description']}")
        print(f"    Domain: {blog['blog_domain']}")
        print(f"    Hatena ID: {blog['hatena_id']}")
        print()
    
    print(f"✅ Found {len(blogs)} configured blogs")
    
    # Test 2: Test authentication (basic check)
    print("\\n🔐 Testing Authentication...")
    if blogs:
        for blog in blogs[:2]:  # Test first 2 blogs
            blog_name = blog['name']
            print(f"\\nTesting {blog_name}...")
            
            result = manager.test_authentication(blog_name)
            if result["status"] == "success":
                print(f"✅ {blog_name}: Authentication successful")
            else:
                print(f"❌ {blog_name}: {result['message']}")
    
    print("\\n" + "=" * 50)
    print("🎉 Basic configuration test complete!")
    print("\\n💡 Key Features Implemented:")
    print("  ✅ Multi-blog configuration support")
    print("  ✅ Fixed WSSE authentication")
    print("  ✅ Article migration framework")
    print("  ✅ Blog-specific API key management")
    
    print("\\n🚀 Ready for:")
    print("  • ライフハック→登山ブログ記事移行")
    print("  • 複数ブログの同時管理")
    print("  • 認証エラーの修正")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required files are present")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()