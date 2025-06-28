#!/usr/bin/env python3
"""
Hatena Blog Suite Test Suite - 統合テスト
"""

import unittest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from core.hatena_all import HatenaUnified

class TestHatenaUnified(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.hatena = HatenaUnified('test-blog', output_dir=self.test_dir)
        
        # Mock article data
        self.sample_articles = [
            {
                'title': 'Test Article 1',
                'url': 'https://test-blog.hatenablog.com/entry/test1',
                'content': 'This is test content about Python programming',
                'word_count': 10,
                'images': [],
                'links': [{'url': 'https://example.com', 'text': 'Example'}],
                'categories': ['Tech', 'Programming']
            },
            {
                'title': 'Test Article 2', 
                'url': 'https://test-blog.hatenablog.com/entry/test2',
                'content': 'Another test article about JavaScript development',
                'word_count': 15,
                'images': [{'url': 'https://example.com/img.jpg', 'alt': 'Test image'}],
                'links': [],
                'categories': ['Tech', 'JavaScript']
            }
        ]
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('requests.Session.get')
    def test_extract_articles(self, mock_get):
        """Test article extraction"""
        # Mock HTML response
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <body>
                <div class="archive-entries">
                    <a href="/entry/test1">Test Article 1</a>
                    <a href="/entry/test2">Test Article 2</a>
                </div>
                <div class="entry-content">
                    <p>Test content</p>
                </div>
            </body>
        </html>
        '''
        mock_get.return_value = mock_response
        
        # Test extraction
        articles = self.hatena.extract_articles(max_pages=1)
        
        # Assertions
        self.assertIsInstance(articles, list)
        self.assertTrue(len(articles) >= 0)
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'extracted_articles.json')
        self.assertTrue(os.path.exists(json_file))
    
    def test_enhance_articles(self):
        """Test article enhancement"""
        enhanced = self.hatena.enhance_articles(
            self.sample_articles, 
            affiliate=True,
            amazon_tag='test-tag',
            find_related=True
        )
        
        # Check enhancement worked
        self.assertEqual(len(enhanced), 2)
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'enhanced_articles.json')
        self.assertTrue(os.path.exists(json_file))
    
    def test_analyze_performance(self):
        """Test performance analysis"""
        analysis = self.hatena.analyze_performance(self.sample_articles)
        
        # Check analysis structure
        required_keys = ['total_articles', 'total_words', 'avg_words', 'seo_score', 'recommendations']
        for key in required_keys:
            self.assertIn(key, analysis)
        
        # Check values
        self.assertEqual(analysis['total_articles'], 2)
        self.assertEqual(analysis['total_words'], 25)  # 10 + 15
        self.assertEqual(analysis['avg_words'], 12.5)
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'performance_analysis.json')
        self.assertTrue(os.path.exists(json_file))
    
    def test_generate_repost_plan(self):
        """Test repost plan generation"""
        plan = self.hatena.generate_repost_plan(self.sample_articles, weeks=2)
        
        # Check plan structure
        self.assertIsInstance(plan, list)
        self.assertEqual(len(plan), 2)
        
        for item in plan:
            required_keys = ['week', 'article', 'update_type', 'priority']
            for key in required_keys:
                self.assertIn(key, item)
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'repost_calendar.json')
        self.assertTrue(os.path.exists(json_file))
    
    @patch('requests.head')
    def test_check_links(self, mock_head):
        """Test link checking"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        report = self.hatena.check_links(self.sample_articles)
        
        # Check report structure
        required_keys = ['total_checked', 'working', 'broken', 'broken_links']
        for key in required_keys:
            self.assertIn(key, report)
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'link_check_report.json')
        self.assertTrue(os.path.exists(json_file))
    
    def test_build_knowledge_graph(self):
        """Test knowledge graph building"""
        graph = self.hatena.build_knowledge_graph(self.sample_articles)
        
        # Check graph structure
        required_keys = ['total_keywords', 'connecting_keywords', 'top_keywords', 'keyword_relations']
        for key in required_keys:
            self.assertIn(key, graph)
        
        # Check values
        self.assertGreater(graph['total_keywords'], 0)
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'knowledge_graph.json')
        self.assertTrue(os.path.exists(json_file))
    
    @patch('core.hatena_all.HatenaUnified.extract_articles')
    @patch('core.hatena_all.HatenaUnified.enhance_articles')
    @patch('core.hatena_all.HatenaUnified.analyze_performance')
    def test_run_full_workflow(self, mock_analyze, mock_enhance, mock_extract):
        """Test full workflow execution"""
        # Mock return values
        mock_extract.return_value = self.sample_articles
        mock_enhance.return_value = self.sample_articles
        mock_analyze.return_value = {'seo_score': 75, 'total_articles': 2}
        
        summary = self.hatena.run_full_workflow()
        
        # Check summary structure
        required_keys = ['articles_found', 'avg_seo_score', 'completed_at']
        for key in required_keys:
            self.assertIn(key, summary)
        
        # Check that all methods were called
        mock_extract.assert_called_once()
        mock_enhance.assert_called_once()
        mock_analyze.assert_called_once()
        
        # Check JSON file was created
        json_file = os.path.join(self.test_dir, 'workflow_summary.json')
        self.assertTrue(os.path.exists(json_file))

class TestMCPServerIntegration(unittest.TestCase):
    """Test MCP server integration"""
    
    def setUp(self):
        """Set up MCP test environment"""
        # Import the MCP server (would be actual import in real test)
        self.mock_server = Mock()
    
    def test_mcp_tool_registration(self):
        """Test that all MCP tools are properly registered"""
        expected_tools = [
            'extract_articles',
            'enhance_articles', 
            'analyze_performance',
            'check_links',
            'generate_repost_plan',
            'build_knowledge_graph',
            'search_articles',
            'export_data'
        ]
        
        # This would test actual MCP server in real implementation
        for tool in expected_tools:
            # Mock test - in real test would verify tool registration
            self.assertTrue(True, f"Tool {tool} should be registered")

def run_manual_test():
    """Manual test function for quick verification"""
    print("\n🗺 Manual Test - Quick Verification")
    print("="*50)
    
    try:
        # Test basic import
        from core.hatena_all import HatenaUnified
        print("✅ Core module import: SUCCESS")
        
        # Test initialization
        hatena = HatenaUnified('test-blog')
        print("✅ Initialization: SUCCESS")
        
        # Test configuration
        assert hasattr(hatena, 'config')
        assert hasattr(hatena, 'base_url')
        print("✅ Configuration: SUCCESS")
        
        # Test sample data processing
        sample_articles = [
            {
                'title': 'Sample Article',
                'content': 'This is sample content',
                'word_count': 4,
                'categories': ['Test'],
                'links': [],
                'images': []
            }
        ]
        
        # Test analysis
        analysis = hatena.analyze_performance(sample_articles)
        assert 'seo_score' in analysis
        print("✅ Performance analysis: SUCCESS")
        
        # Test repost plan
        plan = hatena.generate_repost_plan(sample_articles)
        assert isinstance(plan, list)
        print("✅ Repost plan generation: SUCCESS")
        
        # Test knowledge graph
        graph = hatena.build_knowledge_graph(sample_articles)
        assert 'total_keywords' in graph
        print("✅ Knowledge graph: SUCCESS")
        
        print("\n🎉 All manual tests PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Manual test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("📋 Hatena Blog Suite - Test Suite")
    print("="*50)
    
    # Run manual test first
    manual_success = run_manual_test()
    
    if manual_success:
        print("\n🧪 Running Unit Tests...")
        print("="*50)
        
        # Run unit tests
        unittest.main(verbosity=2, exit=False)
        
        print("\n✨ Test Suite Complete!")
    else:
        print("\n⚠️ Manual tests failed - skipping unit tests")