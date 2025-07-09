import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.hatena_service import HatenaService

class TestHatenaService(unittest.TestCase):

    @patch('src.services.hatena_service.Config')
    def setUp(self, mock_config):
        """Set up a test instance of HatenaService with mocked dependencies."""
        mock_config.HATENA_ID = 'test_user'
        mock_config.HATENA_BLOG_ID = 'test_blog.hatena.ne.jp'
        mock_config.HATENA_API_KEY = 'test_api_key'
        self.service = HatenaService()

    # --- Tests for _clean_content ---

    def test_clean_content_simple_case(self):
        """Test simple title removal from content."""
        title = "My Test Title"
        content = "My Test Title\n\nThis is the content."
        expected = "This is the content."
        self.assertEqual(self.service._clean_content(title, content).strip(), expected)

    def test_clean_content_with_html_h1(self):
        """Test title removal when it's inside an <h1> tag."""
        title = "HTML Title"
        content = "<h1>HTML Title</h1><p>Some text.</p>"
        expected = "<p>Some text.</p>"
        self.assertEqual(self.service._clean_content(title, content).strip(), expected)
        
    def test_clean_content_with_markdown_header(self):
        """Test title removal for markdown headers."""
        title = "Markdown Title"
        content = f"# {title}\n\nContent here."
        expected = "Content here."
        self.assertEqual(self.service._clean_content(title, content).strip(), expected)

    def test_clean_content_no_title_present(self):
        """Test content remains unchanged if title is not present."""
        title = "A Title"
        content = "This content does not contain the title."
        self.assertEqual(self.service._clean_content(title, content).strip(), content)

    def test_clean_content_title_with_special_chars(self):
        """Test title with special regex characters."""
        title = "Title with (parentheses) and [brackets]"
        content = f"<h1>{title}</h1>\nSome content."
        expected = "Some content."
        self.assertEqual(self.service._clean_content(title, content).strip(), expected)

    # --- Tests for _create_entry_xml ---

    def test_create_entry_xml_basic(self):
        """Test basic XML entry creation."""
        title = "Test Title"
        content = "Test Content"
        tags = ["tag1", "tag2"]
        
        xml_string = self.service._create_entry_xml(title, content, tags=tags)
        
        self.assertIn(f"<title>{title}</title>", xml_string)
        self.assertIn(f'<content type="text/x-markdown">{content}</content>', xml_string)
        self.assertIn('<category term="tag1"', xml_string)
        self.assertIn('<category term="tag2"', xml_string)
        self.assertIn('<app:draft>no</app:draft>', xml_string)

    def test_create_entry_xml_draft(self):
        """Test XML creation for a draft entry."""
        xml_string = self.service._create_entry_xml("Draft", "Content", draft=True)
        self.assertIn('<app:draft>yes</app:draft>', xml_string)

    # --- Tests for public methods ---

    @patch('src.services.hatena_service.requests.post')
    def test_publish_article_success(self, mock_post):
        """Test successful article publication."""
        # Mock the response from Hatena API
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = """<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom">
   <id>tag:blog.hatena.ne.jp,2013:blog-test_user-12345-67890</id>
   <link rel="alternate" type="text/html" href="http://test_blog.hatena.ne.jp/entry/2024/07/10/123456"/>
</entry>"""
        mock_post.return_value = mock_response

        title = "My New Post"
        content = "Hello World!"
        result = self.service.publish_article(title, content, tags=["test"])

        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'published')
        self.assertEqual(result['title'], title)
        self.assertEqual(result['id'], '67890')
        self.assertEqual(result['url'], 'http://test_blog.hatena.ne.jp/entry/2024/07/10/123456')
        
        # Check if requests.post was called correctly
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        self.assertIn(title, call_kwargs['data'].decode('utf-8'))

    @patch('src.services.hatena_service.requests.post')
    def test_publish_article_failure(self, mock_post):
        """Test article publication failure."""
        # Mock a server error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.service.publish_article("Fail Title", "Fail Content")
        
        self.assertIn("Publication failed", str(cm.exception))
        self.assertIn("HTTP 500", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
