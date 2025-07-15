import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import time

# Add the project root to the Python path to allow imports from 'src'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.gemini_service import GeminiService
from src.database import Message, Article

class TestGeminiService(unittest.TestCase):

    @patch('src.services.gemini_service.genai')
    @patch('src.services.gemini_service.Config')
    def setUp(self, mock_config, mock_genai):
        """Set up a test instance of GeminiService with mocked dependencies."""
        # Mock config attributes
        mock_config.GEMINI_API_KEY = "test_api_key"
        mock_config.GEMINI_MODEL = "test_model"

        # Mock genai classes and methods
        self.mock_model = MagicMock()
        self.mock_vision_model = MagicMock()
        mock_genai.GenerativeModel.side_effect = [self.mock_model, self.mock_vision_model]

        # Instantiate the service
        self.service = GeminiService()

        # Verify that configure was called
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")

    def test_parse_article_response_full(self):
        """Test parsing a full, well-formed API response."""
        response_text = """タイトル: テストタイトル
要約: これはテストの要約です。
タグ: タグ1, タグ2, テスト
本文:
<p>これは本文です。</p>
<strong>重要</strong>
"""
        expected = {
            'title': 'テストタイトル',
            'summary': 'これはテストの要約です。',
            'tags': ['タグ1', 'タグ2', 'テスト'],
            'content': '<p>これは本文です。</p>\n<strong>重要</strong>'
        }
        result = self.service._parse_article_response(response_text)
        self.assertEqual(result, expected)

    def test_parse_article_response_minimal(self):
        """Test parsing a response with only the title and body."""
        response_text = """タイトル: 最小限のタイトル
本文:
コンテンツのみ。
"""
        expected = {
            'title': '最小限のタイトル',
            'summary': 'コンテンツのみ。',
            'tags': ["AI生成", "ブログ", "記事"],
            'content': 'コンテンツのみ。'
        }
        result = self.service._parse_article_response(response_text)
        self.assertEqual(result, expected)

    def test_parse_article_response_no_labels(self):
        """Test parsing a response with no labels (e.g., 'タイトル:')."""
        response_text = "ラベルのないコンテンツ。\nこれが本文になるはずです。"
        
        result = self.service._parse_article_response(response_text)
        
        self.assertEqual(result['title'], 'ラベルのないコンテンツ。')
        self.assertEqual(result['content'], 'ラベルのないコンテンツ。\nこれが本文になるはずです。')
        self.assertTrue(len(result['summary']) > 0)
        self.assertEqual(result['tags'], ["AI生成", "ブログ", "記事"])

    def test_generate_content_success(self):
        """Test successful content generation."""
        mock_response = MagicMock()
        mock_response.text = "タイトル: 成功\n\n本文:\n成功しました。"
        self.mock_model.generate_content.return_value = mock_response

        result = self.service.generate_content("テスト入力")
        
        self.assertIn("タイトル: 成功", result)
        self.mock_model.generate_content.assert_called_once()

    @patch('time.sleep', return_value=None)
    def test_generate_content_fallback_on_api_error(self, mock_sleep):
        """Test fallback mechanism when the API call fails repeatedly."""
        self.mock_model.generate_content.side_effect = Exception("API Error")

        result = self.service.generate_content("フォールバックテスト")
        
        self.assertIn("タイトル: フォールバックテスト", result)
        self.assertIn("※ AI生成サービスが一時的に利用できないため、シンプルな形式で投稿しています。", result)
        self.assertEqual(self.mock_model.generate_content.call_count, 3)

    @patch('src.services.gemini_service.Image.open')
    def test_analyze_image_for_blog_success(self, mock_image_open):
        """Test successful image analysis."""
        mock_image_open.return_value = MagicMock() # Mock the image object
        
        mock_response = MagicMock()
        mock_response.text = "タイトル: 画像分析\n\n本文:\n画像は美しいです。"
        self.mock_vision_model.generate_content.return_value = mock_response

        result = self.service.analyze_image_for_blog("dummy_path.jpg", "説明してください")
        
        self.assertIn("タイトル: 画像分析", result)
        self.mock_vision_model.generate_content.assert_called_once()
        mock_image_open.assert_called_once_with("dummy_path.jpg")

if __name__ == '__main__':
    unittest.main()
