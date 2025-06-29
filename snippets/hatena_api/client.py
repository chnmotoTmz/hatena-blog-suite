import requests
from xml.etree import ElementTree as ET
from typing import Dict, List, Optional, Tuple

# Assuming authentication and xml_payload are in the same directory or accessible via PYTHONPATH
from .authentication import generate_wsse_header
from .xml_payload import create_hatena_blog_entry_xml

class HatenaBlogClient:
    """
    A client for interacting with the Hatena Blog AtomPub API.
    """
    BASE_URL_TEMPLATE = "https://blog.hatena.ne.jp/{username}/{blog_domain}/atom"

    def __init__(self, hatena_id: str, blog_domain: str, api_key: str):
        """
        Initializes the Hatena Blog API client.

        Args:
            hatena_id: Your Hatena ID.
            blog_domain: Your blog's domain (e.g., example.hatenablog.com).
            api_key: Your Hatena Blog API key (AtomPub key).
        """
        if not hatena_id:
            raise ValueError("Hatena ID cannot be empty.")
        if not blog_domain:
            raise ValueError("Blog domain cannot be empty.")
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.hatena_id = hatena_id
        self.blog_domain = blog_domain
        self.api_key = api_key
        self.base_url = self.BASE_URL_TEMPLATE.format(username=hatena_id, blog_domain=blog_domain)

    def _request(
        self,
        method: str,
        endpoint_path: str,
        data: Optional[bytes] = None,
        params: Optional[Dict] = None,
        extra_headers: Optional[Dict] = None
    ) -> requests.Response:
        """
        Makes an HTTP request to the Hatena Blog API.
        """
        url = f"{self.base_url}/{endpoint_path.lstrip('/')}"

        headers = {
            "X-WSSE": generate_wsse_header(self.hatena_id, self.api_key),
        }
        if data:
            # Common content type for AtomPub POST/PUT
            headers["Content-Type"] = "application/atom+xml; charset=utf-8"

        if extra_headers:
            headers.update(extra_headers)

        try:
            response = requests.request(method, url, headers=headers, data=data, params=params, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.RequestException as e:
            # Log error or handle it more gracefully
            error_message = f"API request failed: {e}"
            if e.response is not None:
                error_message += f" - Status: {e.response.status_code}, Body: {e.response.text[:200]}"
            # print(error_message) # Or use logging
            raise  # Re-raise the exception for the caller to handle

    def post_entry(
        self, title: str, content: str, is_draft: bool = False, categories: Optional[List[str]] = None
    ) -> Dict:
        """
        Posts a new entry to the blog.

        Args:
            title: Title of the entry.
            content: HTML content of the entry.
            is_draft: Whether the entry should be a draft.
            categories: List of categories.

        Returns:
            A dictionary containing the status, entry_id, and URL of the new post,
            or an error message.
        """
        xml_data = create_hatena_blog_entry_xml(
            title=title,
            content=content,
            author_name=self.hatena_id,
            is_draft=is_draft,
            categories=categories
        )
        try:
            response = self._request("POST", "entry", data=xml_data)

            # Parse response to get entry ID and URL
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            entry_id_tag = root.find('.//atom:id', ns)
            entry_id = entry_id_tag.text.split('-')[-1] if entry_id_tag is not None and entry_id_tag.text else None

            link_tag = root.find(".//atom:link[@rel='alternate'][@type='text/html']", ns)
            entry_url = link_tag.get('href') if link_tag is not None else None

            edit_link_tag = root.find(".//atom:link[@rel='edit']", ns)
            edit_url = edit_link_tag.get('href') if edit_link_tag is not None else None


            return {
                "status": "success",
                "entry_id": entry_id,
                "url": entry_url,
                "edit_url": edit_url, # URL to edit/delete the entry
                "title": title,
                "response_status_code": response.status_code
            }
        except requests.RequestException as e:
            return {"status": "error", "message": str(e), "title": title,
                    "status_code": e.response.status_code if e.response is not None else None}
        except ET.ParseError as e:
            return {"status": "error", "message": f"Failed to parse API response XML: {e}", "title": title}


    def update_entry(
        self, entry_id: str, title: str, content: str, is_draft: bool = False, categories: Optional[List[str]] = None
    ) -> Dict:
        """
        Updates an existing blog entry.

        Args:
            entry_id: The ID of the entry to update.
            title: The new title.
            content: The new HTML content.
            is_draft: The new draft status.
            categories: The new list of categories.

        Returns:
            A dictionary containing the status, or an error message.
        """
        xml_data = create_hatena_blog_entry_xml(
            title=title,
            content=content,
            author_name=self.hatena_id,
            is_draft=is_draft,
            categories=categories
        )
        try:
            response = self._request("PUT", f"entry/{entry_id}", data=xml_data)
            # Successful PUT usually returns 200 OK with the updated entry XML
            # Some APIs might return 204 No Content

            # Optionally parse response if needed, e.g. to get updated link
            public_link = None
            if response.text:
                try:
                    entry_root = ET.fromstring(response.text)
                    link_node = entry_root.find("{http://www.w3.org/2005/Atom}link[@rel='alternate'][@type='text/html']")
                    if link_node is not None:
                        public_link = link_node.get("href")
                except ET.ParseError:
                    pass # Ignore if parsing fails, not critical for update status

            return {
                "status": "success",
                "entry_id": entry_id,
                "title": title,
                "public_link": public_link,
                "response_status_code": response.status_code
            }
        except requests.RequestException as e:
            return {"status": "error", "message": str(e), "entry_id": entry_id,
                    "status_code": e.response.status_code if e.response is not None else None}

    def get_entries(self, page_url: Optional[str] = None) -> Dict:
        """
        Retrieves a list of blog entries. Supports pagination.

        Args:
            page_url: URL for a specific page of entries (for pagination).
                      If None, fetches the first page.

        Returns:
            A dictionary containing the list of entries, next page URL, or an error message.
        """
        endpoint = "entry"
        request_url = page_url # If page_url is provided, it's an absolute URL

        if not request_url: # If not paginating, use the standard endpoint
             request_url = f"{self.base_url}/{endpoint}"


        try:
            # For GET, we don't use _request directly if page_url can be different from base_url
            # However, _request can be adapted or a similar structure used.
            # For simplicity here, directly calling requests.get with WSSE header.

            headers = {"X-WSSE": generate_wsse_header(self.hatena_id, self.api_key)}
            response = requests.get(request_url, headers=headers, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            entries_data = []
            for entry_element in root.findall('.//atom:entry', ns):
                title_tag = entry_element.find('.//atom:title', ns)
                title = title_tag.text if title_tag is not None else "No Title"

                id_tag = entry_element.find('.//atom:id', ns)
                entry_id = id_tag.text.split('/')[-1] if id_tag is not None and id_tag.text else None # Atom ID is often a full URL

                # Try to get a cleaner entry ID if possible (Hatena specific part)
                # e.g. tag:blog.hatena.ne.jp,2013:blog-USER-ARTICLE_ID
                if entry_id and ':' in entry_id: # Basic check
                    parts = entry_id.split('-')
                    if len(parts) > 1: # Assuming USER-ARTICLE_ID form
                        potential_id = parts[-1]
                        if potential_id.isdigit(): # Hatena entry IDs are usually numbers
                             entry_id = potential_id


                published_tag = entry_element.find('.//atom:published', ns)
                published_date = published_tag.text if published_tag is not None else None

                updated_tag = entry_element.find('.//atom:updated', ns)
                updated_date = updated_tag.text if updated_tag is not None else None

                public_link_tag = entry_element.find(".//atom:link[@rel='alternate'][@type='text/html']", ns)
                public_link = public_link_tag.get("href") if public_link_tag is not None else None

                categories = [cat.get("term") for cat in entry_element.findall('.//atom:category', ns) if cat.get("term")]

                # Check draft status
                is_draft_status = False
                control_tag = entry_element.find('.//app:control', namespaces={'app': 'http://www.w3.org/2007/app'})
                if control_tag is not None:
                    draft_tag = control_tag.find('.//app:draft', namespaces={'app': 'http://www.w3.org/2007/app'})
                    if draft_tag is not None and draft_tag.text == 'yes':
                        is_draft_status = True

                entries_data.append({
                    "id": entry_id,
                    "title": title,
                    "public_link": public_link,
                    "is_draft": is_draft_status,
                    "published_date": published_date,
                    "updated_date": updated_date,
                    "categories": categories
                })

            next_page_link_tag = root.find(".//atom:link[@rel='next']", ns)
            next_page = next_page_link_tag.get('href') if next_page_link_tag is not None else None

            return {
                "status": "success",
                "entries": entries_data,
                "next_page_url": next_page,
                "response_status_code": response.status_code
            }
        except requests.RequestException as e:
            return {"status": "error", "message": str(e),
                    "status_code": e.response.status_code if e.response is not None else None}
        except ET.ParseError as e:
            return {"status": "error", "message": f"Failed to parse API response XML: {e}"}

    def delete_entry(self, entry_id: str) -> Dict:
        """
        Deletes a blog entry.

        Args:
            entry_id: The ID of the entry to delete.

        Returns:
            A dictionary containing the status, or an error message.
        """
        try:
            response = self._request("DELETE", f"entry/{entry_id}")
            # Successful DELETE usually returns 204 No Content or 200 OK
            return {
                "status": "success",
                "entry_id": entry_id,
                "message": "Entry deleted successfully.",
                "response_status_code": response.status_code
            }
        except requests.RequestException as e:
            return {"status": "error", "message": str(e), "entry_id": entry_id,
                    "status_code": e.response.status_code if e.response is not None else None}


if __name__ == '__main__':
    # This is a placeholder for actual credentials.
    # For real tests, set these as environment variables or use a secure config.
    import os
    HATENA_ID = os.getenv("HATENA_TEST_ID", "your_hatena_id")
    BLOG_DOMAIN = os.getenv("HATENA_TEST_BLOG_DOMAIN", "yourblog.hatenablog.com")
    API_KEY = os.getenv("HATENA_TEST_API_KEY", "your_api_key")

    if HATENA_ID == "your_hatena_id" or API_KEY == "your_api_key":
        print("Placeholder credentials detected. Skipping live API tests.")
        print("To run live tests, set HATENA_TEST_ID, HATENA_TEST_BLOG_DOMAIN, and HATENA_TEST_API_KEY environment variables.")
    else:
        print(f"--- Testing HatenaBlogClient with ID: {HATENA_ID}, Domain: {BLOG_DOMAIN} ---")
        client = HatenaBlogClient(hatena_id=HATENA_ID, blog_domain=BLOG_DOMAIN, api_key=API_KEY)

        # Test 1: Get entries
        print("\\n--- Test 1: Get Entries ---")
        entries_result = client.get_entries()
        if entries_result["status"] == "success":
            print(f"Found {len(entries_result['entries'])} entries on the first page.")
            if entries_result['entries']:
                print(f"First entry title: {entries_result['entries'][0]['title']}")
            if entries_result["next_page_url"]:
                print(f"Next page available: {entries_result['next_page_url']}")
        else:
            print(f"Error getting entries: {entries_result['message']}")

        # Test 2: Post a new draft entry
        print("\\n--- Test 2: Post New Draft Entry ---")
        post_title = f"Test Post via API Client ({datetime.now().strftime('%Y%m%d%H%M%S')})"
        post_content = "<p>This is a test post created by the HatenaBlogClient snippet.</p><p>It should be a draft.</p>"
        post_result = client.post_entry(post_title, post_content, is_draft=True, categories=["Testing", "API"])

        posted_entry_id = None
        if post_result["status"] == "success":
            print(f"Successfully posted draft entry: '{post_result['title']}'")
            print(f"Entry ID: {post_result['entry_id']}, URL: {post_result['url']}")
            posted_entry_id = post_result['entry_id']
        else:
            print(f"Error posting entry: {post_result['message']}")

        if posted_entry_id:
            # Test 3: Update the posted entry (e.g., publish it)
            print("\\n--- Test 3: Update Entry (Publish) ---")
            updated_title = f"{post_title} (Updated & Published)"
            updated_content = post_content + "<p>This content has been updated and published!</p>"
            update_result = client.update_entry(
                posted_entry_id, updated_title, updated_content, is_draft=False, categories=["Testing", "API", "Published"]
            )
            if update_result["status"] == "success":
                print(f"Successfully updated and published entry ID: {posted_entry_id}")
                if update_result.get("public_link"):
                     print(f"New public link: {update_result['public_link']}")
            else:
                print(f"Error updating entry: {update_result['message']}")

            # Test 4: Delete the entry
            print("\\n--- Test 4: Delete Entry ---")
            # Add a small delay or prompt before deleting if you want to check the blog manually
            # input("Press Enter to delete the test post...")
            delete_result = client.delete_entry(posted_entry_id)
            if delete_result["status"] == "success":
                print(f"Successfully deleted entry ID: {posted_entry_id}")
            else:
                print(f"Error deleting entry: {delete_result['message']}")

        print("\\nLive API tests finished.")
