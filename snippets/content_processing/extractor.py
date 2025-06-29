import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union
from urllib.parse import urljoin, urlparse
import re

class HatenaBlogArticleDetails(Dict):
    """Type hint for dictionary containing extracted article details."""
    title: str
    url: str
    author: Optional[str] # Hatena ID
    date: Optional[str] # ISO format string
    categories: List[str]
    full_html_content: Optional[str] # Raw HTML of the entry-content div
    text_content: Optional[str] # Text extracted from entry-content
    images: List[Dict[str, str]] # List of {'url': ..., 'alt': ..., 'title': ...}
    links: List[Dict[str, Union[str, bool]]] # List of {'url': ..., 'text': ..., 'is_internal': ...}
    word_count: Optional[int]
    raw_response_content: Optional[str] # Full HTML of the page

class LinkDetail(Dict):
    """Type hint for dictionary containing extracted link details."""
    url: str
    text: str
    is_internal: bool
    html_element: str # The raw <a> tag HTML

def extract_links_from_html(html_content: str, base_article_url: Optional[str] = None) -> List[LinkDetail]:
    """
    Extracts all hyperlinks from an HTML content string.

    Args:
        html_content: The HTML string to parse.
        base_article_url: The base URL of the article, used to resolve relative links
                          and determine if a link is internal.

    Returns:
        A list of LinkDetail dictionaries, each representing a hyperlink.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    links: List[LinkDetail] = []

    base_domain = urlparse(base_article_url).netloc if base_article_url else None

    for link_tag in soup.find_all('a', href=True):
        href = link_tag['href']
        text = link_tag.get_text(strip=True)

        # Resolve relative URLs if base_article_url is provided
        absolute_url = href
        if base_article_url and not href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:')):
            try:
                absolute_url = urljoin(base_article_url, href)
            except ValueError: # Handle cases like javascript:void(0)
                 pass # Keep href as is

        # Determine if the link is internal
        is_internal_link = False
        if base_domain and absolute_url:
            try:
                link_domain = urlparse(absolute_url).netloc
                if link_domain == base_domain:
                    is_internal_link = True
            except ValueError: # Handle malformed URLs
                pass

        links.append({
            'url': absolute_url,
            'text': text,
            'is_internal': is_internal_link,
            'html_element': str(link_tag)
        })
    return links

def extract_hatena_article_details(article_url: str, fetch_content: bool = True) -> Optional[HatenaBlogArticleDetails]:
    """
    Extracts detailed information from a single Hatena Blog article URL.

    Args:
        article_url: The URL of the Hatena Blog article.
        fetch_content: If True, fetches the content from the URL.
                       If False, assumes article_url is actually HTML content string.

    Returns:
        A HatenaBlogArticleDetails dictionary containing extracted information,
        or None if extraction fails.
    """
    if not article_url:
        return None

    html_page_content = ""
    if fetch_content:
        try:
            response = requests.get(article_url, timeout=10)
            response.raise_for_status()
            html_page_content = response.text
        except requests.RequestException as e:
            print(f"Error fetching article URL {article_url}: {e}")
            return None
    else: # If fetch_content is False, article_url is treated as HTML content
        html_page_content = article_url
        article_url = "" # No actual URL if content is passed directly

    if not html_page_content:
        return None

    soup = BeautifulSoup(html_page_content, 'html.parser')

    details: HatenaBlogArticleDetails = {
        'title': "", 'url': article_url, 'author': None, 'date': None,
        'categories': [], 'full_html_content': None, 'text_content': None,
        'images': [], 'links': [], 'word_count': None,
        'raw_response_content': html_page_content if fetch_content else None # Store raw only if fetched
    }

    # Title
    title_tag = soup.find('h1', class_='entry-title')
    if title_tag:
        details['title'] = title_tag.get_text(strip=True)
        # If URL wasn't from input (because content was passed), try to get it from title link
        if not details['url'] and title_tag.find('a', href=True):
            details['url'] = title_tag.find('a')['href']


    # Author (Hatena ID, often found in profile links or meta tags)
    # This is a common pattern, but might need adjustment for different themes
    author_tag = soup.find('a', class_=['author', 'fn']) # Common classes for author links
    if author_tag and author_tag.get('href'):
        match = re.search(r'/profile/([^/]+)', author_tag['href']) or \
                re.search(r'blog.hatena.ne.jp/([^/]+)/', author_tag['href']) # More specific
        if match:
            details['author'] = match.group(1)
    if not details['author']: # Fallback, try to get from meta tag
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            details['author'] = meta_author['content']


    # Date (ISO format from <time datetime="...">)
    time_tag = soup.find('time', attrs={'datetime': True})
    if time_tag:
        details['date'] = time_tag['datetime']

    # Categories
    category_tags = soup.find_all('a', class_='entry-category-link') # Hatena's typical class
    if not category_tags: # Fallback for other common category link patterns
        category_tags = soup.select('div.categories a, ul.categories a, span.categories a') # More generic

    for cat_tag in category_tags:
        details['categories'].append(cat_tag.get_text(strip=True))
    details['categories'] = list(set(details['categories'])) # Unique categories


    # Full HTML Content (within entry-content div) and Text Content
    entry_content_div = soup.find('div', class_='entry-content')
    if entry_content_div:
        details['full_html_content'] = str(entry_content_div)
        details['text_content'] = entry_content_div.get_text(separator='\n', strip=True)
        details['word_count'] = len(details['text_content'].split()) if details['text_content'] else 0

        # Images within entry-content
        for img_tag in entry_content_div.find_all('img', src=True):
            img_src = img_tag['src']
            # Resolve relative image URLs
            if details['url'] and not img_src.startswith(('http://', 'https://')):
                 try:
                    img_src = urljoin(details['url'], img_src)
                 except ValueError:
                    pass
            details['images'].append({
                'url': img_src,
                'alt': img_tag.get('alt', ''),
                'title': img_tag.get('title', '')
            })

        # Links within entry-content (using the dedicated function)
        if details['full_html_content']:
             details['links'] = extract_links_from_html(details['full_html_content'], details['url'])
    else: # Fallback if 'entry-content' is not found, try to get from body
        details['text_content'] = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
        details['word_count'] = len(details['text_content'].split()) if details['text_content'] else 0
        # Links from whole body if specific content div not found
        details['links'] = extract_links_from_html(html_page_content, details['url'])


    # If title is still empty, try another common pattern or meta tag
    if not details['title']:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            details['title'] = og_title['content']
        else: # Final fallback for title
            title_tag_html = soup.find('title')
            if title_tag_html:
                details['title'] = title_tag_html.get_text(strip=True)


    return details if details['title'] else None # Return None if no title could be extracted

if __name__ == '__main__':
    print("--- Testing Hatena Blog Article Extractor ---")

    # Example 1: Test with a known Hatena Blog article URL
    # Note: This is a live test and requires internet access.
    # Replace with a valid and publicly accessible Hatena Blog URL.
    # test_url = "https://motochan1969.hatenablog.com/entry/2024/01/15/070000" # Example
    test_url = "https://staff.hatenablog.com/entry/2024/03/25/150000" # Hatena Staff blog

    print(f"\\n--- Test 1: Extracting details from URL: {test_url} ---")
    article_data = extract_hatena_article_details(test_url)
    if article_data:
        print(f"Title: {article_data['title']}")
        print(f"Author: {article_data['author']}")
        print(f"Date: {article_data['date']}")
        print(f"Categories: {article_data['categories']}")
        print(f"Word Count: {article_data['word_count']}")
        print(f"First 3 Images: {article_data['images'][:3]}")
        print(f"First 3 Links: {article_data['links'][:3]}")
        # print(f"Text Content Snippet: {article_data['text_content'][:200]}...")
    else:
        print(f"Failed to extract details from {test_url}")

    # Example 2: Test with provided HTML content
    print("\\n--- Test 2: Extracting details from HTML string ---")
    sample_html_content = """
    <html><head><title>Sample Page Title</title></head>
    <body>
        <h1 class="entry-title">My Sample Article</h1>
        <div class="entry-content">
            <p>This is the first paragraph with a <a href="/internal-link">local link</a>.</p>
            <img src="/images/sample.jpg" alt="Sample Image">
            <p>Another paragraph with an <a href="http://example.com/external-link">external site</a>.</p>
            <time datetime="2023-01-01T12:00:00Z">January 1, 2023</time>
            <div class="categories"><a class="entry-category-link" href="/category/Tech">Tech</a></div>
            <a class="author fn" href="/profile/testauthor">Test Author</a>
        </div>
    </body></html>
    """
    # For HTML content, pass fetch_content=False and the base URL for link resolution
    # The 'article_url' argument becomes the HTML string itself.
    # A 'base_article_url' is needed for extract_links_from_html if called from within.
    # Let's refine how extract_hatena_article_details handles this.
    # For now, we'll test extract_links_from_html directly for HTML content.

    print("\\n--- Test 2a: Extracting links from HTML string ---")
    base_for_html_test = "http://myblog.hatenablog.com"
    links_from_html = extract_links_from_html(sample_html_content, base_for_html_test)
    if links_from_html:
        print(f"Found {len(links_from_html)} links from HTML string:")
        for link in links_from_html:
            print(f"  URL: {link['url']}, Text: '{link['text']}', Internal: {link['is_internal']}")
    else:
        print("No links found in sample HTML.")

    print("\\n--- Test 2b: Extracting full details from HTML string ---")
    # This now passes the HTML content as the first argument, and fetch_content=False
    article_data_from_html = extract_hatena_article_details(sample_html_content, fetch_content=False)
    if article_data_from_html:
        # We need to provide a base_url for link resolution if we want `is_internal` to be accurate
        # For this test, we'll re-extract links with a base_url if the main extraction worked.
        if article_data_from_html['full_html_content']:
             article_data_from_html['links'] = extract_links_from_html(
                 article_data_from_html['full_html_content'],
                 base_for_html_test # Provide a base URL for context
             )

        print(f"Title: {article_data_from_html['title']}")
        print(f"Author: {article_data_from_html['author']}")
        print(f"Date: {article_data_from_html['date']}")
        print(f"Categories: {article_data_from_html['categories']}")
        print(f"Word Count: {article_data_from_html['word_count']}")
        print(f"Images: {article_data_from_html['images']}")
        print(f"Links: {article_data_from_html['links']}")
    else:
        print("Failed to extract details from sample HTML content.")


    print("\\n--- Test 3: Extracting links from more complex HTML ---")
    complex_html = """
    <div>
        <a href="page1.html">Page 1</a>
        <a href="https://external.com/path">External</a>
        <a href="/abs/path">Absolute Path</a>
        <a href="#section">Fragment</a>
        <a href="mailto:test@example.com">Mail To</a>
        <a href="tel:123456789">Tel</a>
        <a href="javascript:void(0);">JS Link</a>
    </div>
    """
    links_complex = extract_links_from_html(complex_html, "http://myblog.com/current/article.html")
    for link in links_complex:
        print(f"  URL: {link['url']}, Text: '{link['text']}', Internal: {link['is_internal']}")

    print("\\nExtractor tests finished.")
