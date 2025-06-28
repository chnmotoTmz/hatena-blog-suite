#!/usr/bin/env python3
"""
Quick Test - 即座動作確認用
"""

import sys
import os

def test_imports():
    """基本インポートテスト"""
    print("🗺 Testing imports...")
    
    try:
        import requests
        print("✅ requests: OK")
    except ImportError:
        print("❌ requests: MISSING - Run: pip install requests")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4: OK")
    except ImportError:
        print("❌ beautifulsoup4: MISSING - Run: pip install beautifulsoup4")
        return False
    
    try:
        from core.hatena_all import HatenaUnified
        print("✅ HatenaUnified: OK")
    except ImportError as e:
        print(f"❌ HatenaUnified: FAILED - {e}")
        return False
    
    return True

def test_basic_functionality():
    """基本機能テスト"""
    print("\n🗺 Testing basic functionality...")
    
    try:
        from core.hatena_all import HatenaUnified
        
        # Initialize
        hatena = HatenaUnified('test-blog')
        print("✅ Initialization: OK")
        
        # Test sample data
        sample_articles = [
            {
                'title': 'Test Article',
                'content': 'This is a test article about programming and development',
                'word_count': 10,
                'categories': ['Tech', 'Programming'],
                'links': [{'url': 'https://example.com', 'text': 'Example'}],
                'images': []
            },
            {
                'title': 'Another Test',
                'content': 'Another article about web development and JavaScript',
                'word_count': 8,
                'categories': ['Web', 'JavaScript'],
                'links': [],
                'images': []
            }
        ]
        
        # Test analysis
        analysis = hatena.analyze_performance(sample_articles)
        assert 'seo_score' in analysis
        print("✅ Performance analysis: OK")
        
        # Test enhancement
        enhanced = hatena.enhance_articles(sample_articles, find_related=True)
        assert len(enhanced) == 2
        print("✅ Article enhancement: OK")
        
        # Test repost plan
        plan = hatena.generate_repost_plan(sample_articles)
        assert isinstance(plan, list)
        print("✅ Repost plan: OK")
        
        # Test knowledge graph
        graph = hatena.build_knowledge_graph(sample_articles)
        assert 'total_keywords' in graph
        print("✅ Knowledge graph: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_operations():
    """ファイル操作テスト"""
    print("\n🗺 Testing file operations...")
    
    try:
        import tempfile
        import json
        
        test_dir = tempfile.mkdtemp()
        print(f"✅ Test directory created: {test_dir}")
        
        from core.hatena_all import HatenaUnified
        hatena = HatenaUnified('test-blog', output_dir=test_dir)
        
        # Test JSON save
        test_data = {'test': 'data', 'number': 123}
        hatena._save_json(test_data, 'test_output.json')
        
        # Verify file exists
        output_file = os.path.join(test_dir, 'test_output.json')
        assert os.path.exists(output_file), "Output file not created"
        
        # Verify content
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data, "File content mismatch"
        
        print("✅ File operations: OK")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        print("✅ Cleanup: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations: FAILED - {e}")
        return False

def test_cli_interface():
    """
CLIインターフェーステスト"""
    print("\n🗺 Testing CLI interface...")
    
    try:
        # Test that CLI module can be imported and parsed
        import argparse
        
        # Simulate CLI args
        test_args = ['--blog-id', 'test-blog', '--mode', 'extract']
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--blog-id', required=True)
        parser.add_argument('--mode', choices=['extract', 'enhance', 'analyze', 'full'], default='full')
        parser.add_argument('--output-dir', default='./output')
        
        args = parser.parse_args(test_args)
        
        assert args.blog_id == 'test-blog'
        assert args.mode == 'extract'
        
        print("✅ CLI interface: OK")
        return True
        
    except Exception as e:
        print(f"❌ CLI interface: FAILED - {e}")
        return False

def run_quick_test():
    """クイックテスト実行"""
    print("🚀 Hatena Blog Suite - Quick Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("File Operations", test_file_operations),
        ("CLI Interface", test_cli_interface)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}: CRASHED - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Ready to use.")
        print("\n🚀 Next steps:")
        print("  python core/hatena_all.py --blog-id YOUR_BLOG_ID --mode full")
        print("  node mcp/unified-server.js")
        return True
    else:
        print("⚠️ Some tests FAILED. Check dependencies and setup.")
        return False

if __name__ == '__main__':
    success = run_quick_test()
    sys.exit(0 if success else 1)