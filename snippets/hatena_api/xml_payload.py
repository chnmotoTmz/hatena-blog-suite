from datetime import datetime
from xml.sax.saxutils import escape
from typing import List, Optional

def create_hatena_blog_entry_xml(
    title: str,
    content: str,
    author_name: str,
    is_draft: bool = False,
    categories: Optional[List[str]] = None,
    updated_datetime: Optional[datetime] = None
) -> bytes:
    """
    Creates an XML payload for a Hatena Blog entry (for posting or updating).

    Args:
        title: The title of the blog entry.
        content: The HTML content of the blog entry.
        author_name: The Hatena ID of the author.
        is_draft: If True, the entry will be a draft. Defaults to False.
        categories: A list of category strings. Defaults to None (no categories or default).
                    If an empty list is provided, no category tags will be added.
                    If None, a default 'tech' category might be used by some calling functions,
                    but this function itself won't add a default if categories=None.
        updated_datetime: Optional datetime object for the <updated> tag.
                          If None, the current datetime will be used.

    Returns:
        The XML payload as a UTF-8 encoded byte string.
    """
    if not title:
        raise ValueError("Title cannot be empty.")
    # Content can be empty for some operations, so no check here.
    if not author_name:
        raise ValueError("Author name (Hatena ID) cannot be empty.")

    # Timestamp for the <updated> tag
    if updated_datetime:
        if not isinstance(updated_datetime, datetime):
            raise TypeError("updated_datetime must be a datetime object.")
        update_timestamp_str = updated_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        update_timestamp_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Escape title, content, and author_name to prevent XML injection issues
    escaped_title = escape(title)
    escaped_content = escape(content.strip()) # Content is often HTML, ensure it's properly escaped if needed by caller
    escaped_author_name = escape(author_name)

    # Category tags
    category_tags_xml = ""
    if categories is not None: # Check for None explicitly, empty list means no categories
        if categories: # If list is not empty
            category_tags_xml = "\n    ".join(
                [f'<category term="{escape(cat)}" />' for cat in categories if cat]
            )
        # If categories is an empty list, category_tags_xml remains "" (no categories)
    # If categories is None, it also remains "" (no explicit categories, caller might default)


    # Draft status
    draft_status_str = 'yes' if is_draft else 'no'

    # Construct the XML template
    # Note: The content type is "text/html". Ensure `content` is valid HTML.
    # Some APIs might expect type="text/x-hatena-syntax" for Hatena syntax.
    xml_template = f'''<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{escaped_title}</title>
    <author><name>{escaped_author_name}</name></author>
    <content type="text/html">{escaped_content}</content>
    <updated>{update_timestamp_str}</updated>
    {category_tags_xml}
    <app:control>
        <app:draft>{draft_status_str}</app:draft>
    </app:control>
</entry>'''

    # Remove empty category lines if category_tags_xml is empty
    if not category_tags_xml.strip():
        xml_template = xml_template.replace("    \n    <app:control>", "    <app:control>")


    return xml_template.encode('utf-8')

if __name__ == '__main__':
    print("--- Testing Hatena Blog Entry XML Generation ---")

    # Test case 1: Basic entry
    xml1 = create_hatena_blog_entry_xml(
        title="My First Post",
        content="<p>This is the <b>content</b> of my first post.</p>",
        author_name="testuser"
    )
    print(f"\\nTest Case 1 (Basic):\\n{xml1.decode('utf-8')}")

    # Test case 2: Draft entry with categories
    xml2 = create_hatena_blog_entry_xml(
        title="Draft with Categories & Special Chars < > &",
        content="<p>Content with special characters: &lt;script&gt;alert('XSS');&lt;/script&gt; &amp; more.</p>",
        author_name="anotheruser",
        is_draft=True,
        categories=["Tech", "Python Programming", "Web Dev"]
    )
    print(f"\\nTest Case 2 (Draft, Categories, Special Chars):\\n{xml2.decode('utf-8')}")

    # Test case 3: Entry with specific update time and no categories (empty list)
    custom_time = datetime(2023, 10, 26, 14, 30, 00)
    xml3 = create_hatena_blog_entry_xml(
        title="Post with Custom Time",
        content="<p>This post has a specific update time.</p>",
        author_name="timekeeper",
        updated_datetime=custom_time,
        categories=[] # Explicitly no categories
    )
    print(f"\\nTest Case 3 (Custom Time, No Categories via empty list):\\n{xml3.decode('utf-8')}")

    # Test case 4: Entry with None categories (should also result in no category tags)
    xml4 = create_hatena_blog_entry_xml(
        title="Post with None Categories",
        content="<p>This post has categories=None.</p>",
        author_name="noneuser",
        categories=None
    )
    print(f"\\nTest Case 4 (None Categories):\\n{xml4.decode('utf-8')}")


    print("\\n--- Testing Error Cases ---")
    try:
        create_hatena_blog_entry_xml("", "content", "user")
    except ValueError as e:
        print(f"Caught expected error for empty title: {e}")

    try:
        create_hatena_blog_entry_xml("title", "content", "")
    except ValueError as e:
        print(f"Caught expected error for empty author_name: {e}")

    try:
        create_hatena_blog_entry_xml("title", "content", "user", updated_datetime="not a datetime")
    except TypeError as e:
        print(f"Caught expected error for invalid updated_datetime type: {e}")

    print("\\nXML Payload generation tests finished.")
