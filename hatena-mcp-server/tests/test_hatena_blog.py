import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
import os
import sys
import re
from datetime import datetime
import base64 # For wsse PasswordDigest and Nonce
import requests # For simulating requests.exceptions.HTTPError

# Add project root to sys.path to allow importing from hatena_agent and article_updater
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hatena_agent import get_blog_entries, post_blog_entry, edit_blog_entry, wsse, create_post_data
from article_updater import enhance_article_content_operations 
# from hatena_agent import agent as hatena_blog_agent_instance # If testing via agent.run()

# Sample XML data for mocking Hatena AtomPub response (remains unchanged)
SAMPLE_ATOM_XML_PAGE1 = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:app="http://www.w3.org/2007/app">
  <link rel="next" href="https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry?page=1377632614" />
  <title>Test Blog</title>
  <entry>
    <id>tag:blog.hatena.ne.jp,2013:blog-test_user-12345678901234567890</id>
    <link rel="edit" href="https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry/12345678901234567890" />
    <link rel="alternate" type="text/html" href="http://test.hatenablog.com/entry/2023/01/01/000000" />
    <title>First Post</title>
    <author><name>test_user</name></author>
    <summary type="text">This is the first post.</summary>
    <content type="text/html">&lt;p&gt;This is the first post.&lt;/p&gt;</content>
    <updated>2023-01-01T00:00:00+09:00</updated>
    <published>2023-01-01T00:00:00+09:00</published>
    <app:control>
      <app:draft>no</app:draft>
    </app:control>
    <category term="Tech" />
  </entry>
  <entry>
    <id>tag:blog.hatena.ne.jp,2013:blog-test_user-09876543210987654321</id>
    <link rel="edit" href="https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry/09876543210987654321" />
    <link rel="alternate" type="text/html" href="http://test.hatenablog.com/entry/2023/01/02/000000" />
    <title>Second Post - Draft</title>
    <author><name>test_user</name></author>
    <summary type="text">This is a draft post.</summary>
    <content type="text/plain">This is a draft post.</content>
    <updated>2023-01-02T00:00:00+09:00</updated>
    <published>2023-01-02T00:00:00+09:00</published>
    <app:control>
      <app:draft>yes</app:draft>
    </app:control>
    <category term="Drafts" />
  </entry>
</feed>
"""

SAMPLE_ATOM_XML_PAGE2 = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:app="http://www.w3.org/2007/app">
  <title>Test Blog</title>
  <entry>
    <id>tag:blog.hatena.ne.jp,2013:blog-test_user-11111111111111111111</id>
    <link rel="edit" href="https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry/11111111111111111111" />
    <link rel="alternate" type="text/html" href="http://test.hatenablog.com/entry/2022/12/31/000000" />
    <title>Third Post</title>
    <author><name>test_user</name></author>
    <summary type="text">This is the third post from previous page.</summary>
    <content type="text/html">&lt;p&gt;This is the third post.&lt;/p&gt;</content>
    <updated>2022-12-31T00:00:00+09:00</updated>
    <published>2022-12-31T00:00:00+09:00</published>
    <app:control>
      <app:draft>no</app:draft>
    </app:control>
  </entry>
</feed>
"""

SAMPLE_ENTRY_RESPONSE_XML = """<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
  <id>tag:blog.hatena.ne.jp,2013:blog-test_user-12345678901234567890</id>
  <link rel="edit" href="https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry/12345678901234567890"/>
  <link rel="alternate" type="text/html" href="http://test.hatenablog.com/entry/2023/01/01/000000"/>
  <title>Test Title</title>
  <author><name>test_user</name></author>
  <content type="text/html">&lt;p&gt;Test Content&lt;/p&gt;</content>
  <updated>2023-01-01T10:00:00+09:00</updated>
  <published>2023-01-01T10:00:00+09:00</published>
  <app:control>
    <app:draft>no</app:draft>
  </app:control>
</entry>
"""

class TestHatenaBlogAgentTools(unittest.TestCase):

    def setUp(self):
        self.hatena_id = "test_user"
        self.blog_domain = "test.hatenablog.com"
        self.api_key = "dummy_api_key"
        
        os.environ["HATENA_ID"] = self.hatena_id
        os.environ["BLOG_DOMAIN"] = self.blog_domain
        os.environ[f"HATENA_BLOG_ATOMPUB_KEY_{self.hatena_id}"] = self.api_key
        # For enhance_article_content_operations, RAKUTEN_APP_ID and RAKUTEN_AFFILIATE_ID are needed for affiliate links
        os.environ["RAKUTEN_APP_ID"] = "dummy_rakuten_app_id"
        os.environ["RAKUTEN_AFFILIATE_ID"] = "dummy_rakuten_affiliate_id"


    def tearDown(self):
        if "HATENA_ID" in os.environ: del os.environ["HATENA_ID"]
        if "BLOG_DOMAIN" in os.environ: del os.environ["BLOG_DOMAIN"]
        if f"HATENA_BLOG_ATOMPUB_KEY_{self.hatena_id}" in os.environ:
             del os.environ[f"HATENA_BLOG_ATOMPUB_KEY_{self.hatena_id}"]
        if "RAKUTEN_APP_ID" in os.environ: del os.environ["RAKUTEN_APP_ID"]
        if "RAKUTEN_AFFILIATE_ID" in os.environ: del os.environ["RAKUTEN_AFFILIATE_ID"]


    # --- Tests for get_blog_entries ---
    @patch('requests.get')
    def test_get_blog_entries_success_first_page_with_next(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = SAMPLE_ATOM_XML_PAGE1
        mock_get.return_value = mock_response
        result = get_blog_entries()
        self.assertIsInstance(result, dict)
        self.assertIn("entries", result)
        self.assertEqual(len(result["entries"]), 2)
        self.assertEqual(result["next_page_url"], "https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry?page=1377632614")
        expected_url = f"https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_domain}/atom/entry"
        mock_get.assert_called_once_with(expected_url, auth=(self.hatena_id, self.api_key))

    # ... (other get_blog_entries tests remain the same) ...
    @patch('requests.get')
    def test_get_blog_entries_success_specified_page_no_next(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = SAMPLE_ATOM_XML_PAGE2
        mock_get.return_value = mock_response
        page1_next_url = "https://blog.hatena.ne.jp/test_user/test.hatenablog.com/atom/entry?page=1377632614"
        result = get_blog_entries(page_url=page1_next_url)
        self.assertIsInstance(result, dict)
        self.assertIn("entries", result)
        self.assertIsNone(result.get("next_page_url"))
        self.assertEqual(len(result["entries"]), 1)
        mock_get.assert_called_once_with(page1_next_url, auth=(self.hatena_id, self.api_key))

    @patch('requests.get')
    def test_get_blog_entries_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_get.return_value = mock_response
        result = get_blog_entries()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "error")
        self.assertIn("Error fetching entries", result["message"])
        self.assertEqual(result["status_code"], 500)
        
    def test_get_blog_entries_missing_env_vars(self):
        original_hatena_id = os.environ.pop("HATENA_ID", None)
        result = get_blog_entries()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "HATENA_ID or BLOG_DOMAIN environment variables not set.")
        if original_hatena_id: os.environ["HATENA_ID"] = original_hatena_id
        
    # --- Tests for Helper Functions ---
    def test_wsse_header_generation(self):
        username = "test_user"
        api_key = "test_api_key"
        header = wsse(username, api_key)
        self.assertIn(f'Username="{username}"', header)
        self.assertIn('PasswordDigest="', header)
        self.assertIn('Nonce="', header)
        self.assertIn('Created="', header)

    def test_create_post_xml_data(self):
        title = "Test XML Title"
        body = "<p>Test XML Body</p>"
        username = "test_xml_user"
        xml_data_bytes = create_post_data(title, body, username, draft='no')
        xml_data_str = xml_data_bytes.decode('utf-8')
        self.assertIn(f"<title>{title}</title>", xml_data_str)
        self.assertIn(f"<author><name>{username}</name></author>", xml_data_str)
        self.assertIn(f"<content type=\"text/html\">{body}</content>", xml_data_str)
        self.assertIn(f"<app:draft>no</app:draft>", xml_data_str)
        self.assertIn("<category term=\"tech\" />", xml_data_str)
        category = "Diary"
        xml_data_draft_bytes = create_post_data(title, body, username, draft='yes', category=category)
        xml_data_draft_str = xml_data_draft_bytes.decode('utf-8')
        self.assertIn(f"<app:draft>yes</app:draft>", xml_data_draft_str)
        self.assertIn(f"<category term=\"{category}\" />", xml_data_draft_str)

    # --- Tests for post_blog_entry ---
    @patch('requests.post')
    def test_post_blog_entry_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"Location": f"https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_domain}/atom/entry/1234567890"}
        mock_response.text = SAMPLE_ENTRY_RESPONSE_XML
        mock_post.return_value = mock_response
        result = post_blog_entry("Test Title", "<p>Test Content</p>", is_draft=False, category="TestCat")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["entry_id"], "1234567890")
        self.assertEqual(result["url"], mock_response.headers["Location"])
        self.assertEqual(result["public_link"], "http://test.hatenablog.com/entry/2023/01/01/000000")
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_post_blog_entry_api_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_post.return_value = mock_response
        result = post_blog_entry("Error Title", "<p>Error Content</p>")
        self.assertEqual(result["status"], "error")
        self.assertIn("API Error", result["message"])
        self.assertEqual(result["status_code"], 400)

    def test_post_blog_entry_missing_env_vars(self):
        original_hatena_id = os.environ.pop("HATENA_ID")
        result = post_blog_entry("Title", "Content")
        self.assertEqual(result["status"], "error")
        os.environ["HATENA_ID"] = original_hatena_id

    # --- Tests for edit_blog_entry ---
    @patch('requests.put')
    def test_edit_blog_entry_success(self, mock_put):
        entry_id_to_edit = "1234567890"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_ENTRY_RESPONSE_XML
        mock_put.return_value = mock_response
        result = edit_blog_entry(entry_id_to_edit, "Updated Title", "<p>Updated Content</p>", is_draft=True, category="UpdatedCat")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["entry_id"], entry_id_to_edit)
        self.assertEqual(result["public_link"], "http://test.hatenablog.com/entry/2023/01/01/000000")
        mock_put.assert_called_once()

    @patch('requests.put')
    def test_edit_blog_entry_api_error(self, mock_put):
        entry_id_to_edit = "1234567890"
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_put.return_value = mock_response
        result = edit_blog_entry(entry_id_to_edit, "Error Title", "<p>Error Content</p>")
        self.assertEqual(result["status"], "error")
        self.assertIn("API Error", result["message"])
        self.assertEqual(result["status_code"], 503)

    def test_edit_blog_entry_missing_env_vars(self):
        original_blog_domain = os.environ.pop("BLOG_DOMAIN")
        result = edit_blog_entry("123", "Title", "Content")
        self.assertEqual(result["status"], "error")
        os.environ["BLOG_DOMAIN"] = original_blog_domain

    # --- Tests for enhance_article_content_operations ---
    @patch('article_updater.generate_image_from_prompt')
    @patch('article_updater.find_internal_links')
    @patch('article_updater.generate_affiliate_link')
    @patch('article_updater.search_products')
    @patch('article_updater.extract_keywords')
    @patch('article_updater.generate_summary')
    def test_enhance_article_content_success_all_steps(
        self, mock_generate_summary, mock_extract_keywords, 
        mock_search_products, mock_generate_affiliate_link,
        mock_find_internal_links, mock_generate_image_from_prompt
    ):
        # Configure mock return values
        mock_generate_summary.return_value = "Processed [summary] of original content. keyword1 and keyword2 mentioned."
        mock_extract_keywords.return_value = ["keyword1", "keyword2", "unmatched_keyword"]
        
        # Simulate finding products for some keywords
        def search_side_effect(keyword, applicationId=None): # applicationId added to match rakuten_api.py
            if keyword == "keyword1": return [{"itemCode": "code_for_keyword1", "itemName": "Product For Keyword1", "itemUrl": "http://example.com/product1"}]
            if keyword == "keyword2": return [{"itemCode": "code_for_keyword2", "itemName": "Product For Keyword2", "itemUrl": "http://example.com/product2"}]
            return []
        mock_search_products.side_effect = search_side_effect
        
        # Simulate affiliate link generation
        mock_generate_affiliate_link.side_effect = lambda item_url, item_price, affiliate_id, product_name: f"http://affiliate.link/{product_name.replace(' ', '_')}"

        mock_find_internal_links.return_value = [{"title": "Related Article 1", "url": "http://internal.link/1"}]
        mock_generate_image_from_prompt.return_value = "http://image.url/generated_image.jpg"

        original_content = "<p>This is the original content about keyword1.</p>"
        keywords_for_prompt = "keyword1, keyword2, topic" # This is the prompt for extract_keywords
        
        enhanced_html = enhance_article_content_operations(
            content=original_content,
            keywords_prompt=keywords_for_prompt, 
            internal_links_url="http://my.blog.com",
            image_prompt="A cool image about keyword1",
            article_title="My Article on Keyword1"
        )

        # Assertions
        self.assertIn("Processed [summary] of original content.", enhanced_html)
        self.assertIn('<a href="http://affiliate.link/Product_For_Keyword1" target="_blank" rel="noopener noreferrer sponsored">keyword1</a>', enhanced_html)
        self.assertIn('<a href="http://affiliate.link/Product_For_Keyword2" target="_blank" rel="noopener noreferrer sponsored">keyword2</a>', enhanced_html)
        self.assertNotIn("unmatched_keyword</a>", enhanced_html) # ensure only linked keywords are modified this way
        self.assertIn('<li><a href="http://internal.link/1">Related Article 1</a></li>', enhanced_html)
        self.assertIn('<img src="http://image.url/generated_image.jpg" alt="My Article on Keyword1"', enhanced_html)

        # Assert calls
        mock_generate_summary.assert_called_once_with(original_content, length="long")
        mock_extract_keywords.assert_called_once_with(keywords_for_prompt, num_keywords=10)
        # search_products is called for each keyword from mock_extract_keywords
        self.assertEqual(mock_search_products.call_count, 3)
        mock_search_products.assert_any_call(keyword="keyword1", applicationId="dummy_rakuten_app_id")
        mock_search_products.assert_any_call(keyword="keyword2", applicationId="dummy_rakuten_app_id")
        mock_search_products.assert_any_call(keyword="unmatched_keyword", applicationId="dummy_rakuten_app_id")
        # generate_affiliate_link is called for keywords that had products
        self.assertEqual(mock_generate_affiliate_link.call_count, 2)
        mock_find_internal_links.assert_called_once() # Check specific args if necessary
        mock_generate_image_from_prompt.assert_called_once_with("A cool image about keyword1", "My Article on Keyword1")

    @patch('article_updater.generate_image_from_prompt', return_value="Error: Image generation failed")
    @patch('article_updater.extract_keywords', return_value=["keyword1"])
    @patch('article_updater.generate_summary', return_value="Error: Summary failed")
    def test_enhance_article_content_api_failures(
        self, mock_generate_summary, mock_extract_keywords, mock_generate_image_from_prompt
    ):
        original_content = "<p>Original content.</p>"
        # Keep other mocks minimal or default if they are not the focus of this failure test
        with patch('article_updater.search_products', return_value=[]), \
             patch('article_updater.find_internal_links', return_value=[]):
            
            enhanced_html = enhance_article_content_operations(
                content=original_content,
                keywords_prompt="keywords", 
                internal_links_url="http://my.blog.com",
                image_prompt="image_prompt",
                article_title="Test Title"
            )
            # Check if original content is used when summary fails
            self.assertIn("Original content.", enhanced_html) 
            self.assertNotIn("Error: Summary failed", enhanced_html) # Error message should not be in content
            # Check if image tag is not added when image generation fails
            self.assertNotIn("<img src", enhanced_html)
            # Check that keyword was still attempted for processing (even if no links made)
            mock_extract_keywords.assert_called_once()


    @patch('article_updater.search_products') # We need to mock this so it doesn't try to make real calls
    @patch('article_updater.extract_keywords', return_value=[]) # No keywords found
    def test_enhance_article_content_no_keywords_found(self, mock_extract_keywords, mock_search_products):
        with patch('article_updater.generate_summary', return_value="Summary.") as mock_gen_sum, \
             patch('article_updater.find_internal_links', return_value=[]) as mock_find_int, \
             patch('article_updater.generate_image_from_prompt', return_value="img_url") as mock_gen_img, \
             patch('article_updater.generate_affiliate_link') as mock_gen_aff_link:

            enhanced_html = enhance_article_content_operations(
                content="Original", keywords_prompt="any", internal_links_url="any", image_prompt="any", article_title="any"
            )
            self.assertIn("Summary.", enhanced_html)
            mock_extract_keywords.assert_called_once()
            mock_search_products.assert_not_called() # No keywords, so no product search
            mock_gen_aff_link.assert_not_called() # No products, so no affiliate links
            self.assertIn("img_url", enhanced_html) # Other parts should still work

    @patch('article_updater.generate_affiliate_link') # To check it's not called
    @patch('article_updater.search_products', return_value=[]) # No products found
    @patch('article_updater.extract_keywords', return_value=["keyword1", "keyword2"])
    def test_enhance_article_content_no_products_found(
        self, mock_extract_keywords, mock_search_products, mock_generate_affiliate_link
    ):
        with patch('article_updater.generate_summary', return_value="Summary.") as mock_gen_sum, \
             patch('article_updater.find_internal_links', return_value=[]) as mock_find_int, \
             patch('article_updater.generate_image_from_prompt', return_value="img_url") as mock_gen_img:
            
            original_content = "Original content with keyword1 and keyword2"
            enhanced_html = enhance_article_content_operations(
                content=original_content, keywords_prompt="keyword1, keyword2", 
                internal_links_url="any", image_prompt="any", article_title="any"
            )
            self.assertIn("Summary.", enhanced_html) # Summary should be there
            self.assertIn("keyword1", enhanced_html) # Keywords should be in the content (but not as links)
            self.assertIn("keyword2", enhanced_html)
            self.assertNotIn("href=", enhanced_html) # No affiliate links should be added
            
            mock_extract_keywords.assert_called_once()
            self.assertEqual(mock_search_products.call_count, 2) # Called for each keyword
            mock_generate_affiliate_link.assert_not_called() # Not called as no products were found
            self.assertIn("img_url", enhanced_html) # Image should still be there


if __name__ == '__main__':
    unittest.main()
