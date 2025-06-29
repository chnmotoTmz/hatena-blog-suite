import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime
import time
import logging

# Assuming extractor is in a sibling directory: snippets/content_processing/extractor.py
# Adjust import path if necessary based on your project structure.
try:
    from ..content_processing.extractor import extract_links_from_html, LinkDetail
except ImportError:
    # Fallback if running this script directly or structure is different
    # This is a simplified placeholder for the actual extract_links_from_html
    def extract_links_from_html(html_content: str, base_article_url: Optional[str] = None) -> List[Dict]:
        logging.warning("Using placeholder extract_links_from_html. For full functionality, ensure correct import.")
        import re
        from bs4 import BeautifulSoup # Requires BeautifulSoup4 if using this fallback

        if not html_content: return []
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        base_domain = urlparse(base_article_url).netloc if base_article_url else None
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            absolute_url = urljoin(base_article_url, href) if base_article_url and not href.startswith(('http','javascript:','#','mailto:','tel:')) else href
            is_internal = base_domain and urlparse(absolute_url).netloc == base_domain
            links.append({'url': absolute_url, 'text': link_tag.get_text(strip=True), 'is_internal': is_internal, 'html_element': str(link_tag)})
        return links
    LinkDetail = Dict # Placeholder for type hint


logger = logging.getLogger(__name__)

class LinkStatus(Dict):
    """Type hint for dictionary containing link check status."""
    url: str
    status_code: Optional[int]
    status_description: str # e.g., "Valid", "Not Found", "Timeout", "Error"
    final_url: Optional[str] # After redirects
    error_message: Optional[str]
    response_time_ms: Optional[float]
    checked_at: str # ISO datetime string

class LinkCheckResult(LinkDetail, LinkStatus): # Inherits from both
    """Combined link details and its check status."""
    pass


class AsyncLinkChecker:
    """
    Checks the validity of URLs asynchronously.
    Extracts links from HTML content and verifies their status.
    """

    def __init__(self, default_timeout_sec: int = 10, max_concurrent_checks: int = 20):
        """
        Initializes the AsyncLinkChecker.

        Args:
            default_timeout_sec: Default timeout for HTTP requests in seconds.
            max_concurrent_checks: Maximum number of concurrent link checks.
        """
        self.default_timeout = aiohttp.ClientTimeout(total=default_timeout_sec)
        self.semaphore = asyncio.Semaphore(max_concurrent_checks)
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 LinkCheckerBot/1.0'
        self._link_status_cache: Dict[str, LinkStatus] = {} # Cache results for URLs already checked in this session

    async def _fetch_link_status(self, session: aiohttp.ClientSession, url: str) -> LinkStatus:
        """Fetches the status of a single URL asynchronously."""
        if url in self._link_status_cache:
            return self._link_status_cache[url]

        start_time = time.perf_counter()
        status_info: LinkStatus = {
            'url': url, 'status_code': None, 'status_description': 'Unknown',
            'final_url': url, 'error_message': None, 'response_time_ms': None,
            'checked_at': datetime.now(datetime.utcnow().tzinfo).isoformat() # Ensure timezone aware
        }

        try:
            async with self.semaphore: # Control concurrency
                async with session.head(url, timeout=self.default_timeout, allow_redirects=True) as response:
                    # Using HEAD request first to be quicker and less resource-intensive
                    status_info['status_code'] = response.status
                    status_info['final_url'] = str(response.url) # Capture final URL after redirects

                    if 200 <= response.status < 300:
                        status_info['status_description'] = 'Valid'
                    elif 300 <= response.status < 400:
                        status_info['status_description'] = 'Redirect' # Should be resolved by allow_redirects=True
                    elif response.status == 404:
                        status_info['status_description'] = 'Not Found'
                    elif response.status == 403:
                        status_info['status_description'] = 'Forbidden'
                    elif response.status >= 400:
                        status_info['status_description'] = f'Client Error ({response.status})'
                    else: # 5xx etc.
                        status_info['status_description'] = f'Server Error ({response.status})'

        except asyncio.TimeoutError:
            status_info['status_description'] = 'Timeout'
            status_info['error_message'] = f'Request timed out after {self.default_timeout.total}s'
        except aiohttp.ClientError as e: # Covers various connection errors, SSL errors, etc.
            status_info['status_description'] = 'Connection Error'
            status_info['error_message'] = str(e)
            # Try to get status code from exception if available (e.g. for ClientResponseError)
            if hasattr(e, 'status') and e.status is not None:
                 status_info['status_code'] = e.status
                 if e.status == 404: status_info['status_description'] = 'Not Found'
                 elif e.status == 403: status_info['status_description'] = 'Forbidden'

        except Exception as e:
            status_info['status_description'] = 'Generic Error'
            status_info['error_message'] = f'An unexpected error occurred: {str(e)}'

        end_time = time.perf_counter()
        status_info['response_time_ms'] = (end_time - start_time) * 1000
        self._link_status_cache[url] = status_info
        return status_info

    async def check_multiple_urls(self, urls: List[str]) -> List[LinkStatus]:
        """
        Checks a list of URLs asynchronously.

        Args:
            urls: A list of URL strings to check.

        Returns:
            A list of LinkStatus dictionaries.
        """
        if not urls:
            return []

        unique_urls = sorted(list(set(u for u in urls if u and isinstance(u, str) and u.startswith(('http://', 'https://')))))
        if not unique_urls:
            logger.warning("No valid HTTP/HTTPS URLs provided for checking.")
            return []


        async with aiohttp.ClientSession(headers={'User-Agent': self.user_agent}) as session:
            tasks = [self._fetch_link_status(session, url) for url in unique_urls]
            results = await asyncio.gather(*tasks, return_exceptions=False) # Exceptions are handled in _fetch
        return results

    async def check_links_in_html_content(
        self,
        html_content: str,
        base_article_url: Optional[str] = None
    ) -> List[LinkCheckResult]:
        """
        Extracts links from HTML content and checks their status asynchronously.

        Args:
            html_content: The HTML string.
            base_article_url: The base URL of the article for resolving relative links.

        Returns:
            A list of LinkCheckResult dictionaries, combining link details and status.
        """
        extracted_links: List[LinkDetail] = extract_links_from_html(html_content, base_article_url)
        if not extracted_links:
            return []

        urls_to_check = [link['url'] for link in extracted_links if link['url']]

        link_statuses_list: List[LinkStatus] = await self.check_multiple_urls(urls_to_check)

        # Create a dictionary for quick lookup of statuses by URL
        status_map: Dict[str, LinkStatus] = {status['url']: status for status in link_statuses_list}

        results: List[LinkCheckResult] = []
        for link_detail in extracted_links:
            status = status_map.get(link_detail['url'])
            if status:
                # Combine LinkDetail and LinkStatus into LinkCheckResult
                # Type casting to satisfy mypy if LinkCheckResult is properly defined
                combined_result = LinkCheckResult(**link_detail, **status)
                results.append(combined_result)
            else: # Should not happen if all extracted URLs were checked
                logger.warning(f"Status not found for extracted link: {link_detail['url']}")
                # Add with unknown status
                unknown_status: LinkStatus = {'url': link_detail['url'], 'status_code': None, 'status_description': 'Not Checked', 'final_url': link_detail['url'], 'error_message': None, 'response_time_ms': None, 'checked_at': datetime.now(datetime.utcnow().tzinfo).isoformat()}
                results.append(LinkCheckResult(**link_detail, **unknown_status))
        return results

    def generate_report_from_results(self, check_results: List[LinkCheckResult], article_title: Optional[str] = None) -> str:
        """Generates a human-readable report from link check results."""
        report_lines = []
        if article_title:
            report_lines.append(f"# Link Check Report for: {article_title}")
        else:
            report_lines.append("# Link Check Report")
        report_lines.append(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total links analyzed: {len(check_results)}")

        broken_links = [r for r in check_results if r['status_description'] not in ['Valid', 'Redirect']]
        redirected_links = [r for r in check_results if r['status_description'] == 'Redirect']

        report_lines.append(f"\n## Summary:")
        report_lines.append(f"- Valid links: {len(check_results) - len(broken_links) - len(redirected_links)}")
        report_lines.append(f"- Broken/Error links: {len(broken_links)}")
        report_lines.append(f"- Redirected links: {len(redirected_links)}")

        if broken_links:
            report_lines.append("\n## Broken or Erroneous Links:")
            for link in broken_links:
                report_lines.append(f"- URL: {link['url']}")
                report_lines.append(f"  - Text: '{link['text']}'")
                report_lines.append(f"  - Status: {link['status_description']} (Code: {link['status_code'] or 'N/A'})")
                if link['error_message']:
                    report_lines.append(f"  - Error: {link['error_message']}")

        if redirected_links:
            report_lines.append("\n## Redirected Links:")
            for link in redirected_links:
                report_lines.append(f"- Original URL: {link['url']}")
                report_lines.append(f"  - Text: '{link['text']}'")
                report_lines.append(f"  - Final URL: {link['final_url']}")
                report_lines.append(f"  - Status Code: {link['status_code']}")

        return "\n".join(report_lines)

# Main execution for testing
async def main_test():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    checker = AsyncLinkChecker(default_timeout_sec=5, max_concurrent_checks=10)

    print("--- Testing AsyncLinkChecker ---")

    urls_to_test = [
        "https://www.google.com",
        "https://www.wikipedia.org",
        "http://example.com/nonexistentpage123abc", # Likely 404
        "https://github.com",
        "https://httpstat.us/403", # Forbidden
        "https://httpstat.us/500", # Server Error
        "https://httpstat.us/301", # Permanent Redirect (should be followed)
        "https://jigsaw.w3.org/HTTP/Basic/", # Requires auth, might give 401 or redirect
        "http://localhost:9999/timeout", # Will timeout if nothing is running there
        "https://expired.badssl.com/", # SSL error
        "invalid-url-schema", # Invalid URL
        None, # Test None
        "ftp://example.com" # Non-HTTP
    ]

    print(f"\\n--- Checking {len(urls_to_test)} individual URLs ---")
    results_individual = await checker.check_multiple_urls(urls_to_test)
    for res in results_individual:
        print(f"URL: {res['url']}, Status: {res['status_description']}, Code: {res['status_code']}, Final: {res['final_url']}, Time: {res['response_time_ms']:.2f}ms, Error: {res['error_message']}")

    sample_html_for_test = """
    <html><body>
        <h1>Test Page</h1>
        <p>A valid link to <a href="https://www.python.org">Python Official Site</a>.</p>
        <p>A link that will likely be a <a href="http://example.com/broken-link-test">broken link</a>.</p>
        <p>An internal link <a href="/about">About Us</a>.</p>
        <p>A link to a redirecting page <a href="https://httpbin.org/redirect/1">HTTPBin Redirect</a>.</p>
        <p>Link with fragment <a href="#section1">Go to section</a>.</p>
        <p>External link <a href="https://www.djangoproject.com/">Django Project</a>.</p>
    </body></html>
    """
    base_url_for_html_test = "http://mytestblog.com/article1"

    print(f"\\n--- Checking links within HTML content (base: {base_url_for_html_test}) ---")
    html_link_results = await checker.check_links_in_html_content(sample_html_for_test, base_url_for_html_test)

    # Print summary of HTML link checks
    for res in html_link_results:
        print(f"  URL: {res['url']} (Text: '{res['text']}', Internal: {res['is_internal']}) -> Status: {res['status_description']} (Code: {res['status_code']})")

    print("\\n--- Generating Report from HTML Link Check Results ---")
    report = checker.generate_report_from_results(html_link_results, article_title="My Test Article")
    print(report)

    # Test caching (check one URL again)
    print("\\n--- Testing Link Status Cache ---")
    cached_url_to_recheck = "https://www.google.com"
    if cached_url_to_recheck in checker._link_status_cache:
         print(f"'{cached_url_to_recheck}' is in cache. Re-checking (should use cache).")
    status_again = await checker.check_multiple_urls([cached_url_to_recheck]) # Should be fast
    print(f"Re-check for {cached_url_to_recheck}: Status {status_again[0]['status_description']}, Time {status_again[0]['response_time_ms']:.2f}ms (check if significantly lower than first time)")


    print("\\nAsyncLinkChecker tests finished.")

if __name__ == '__main__':
    # To run asyncio code:
    if os.name == 'nt': # Fix for ProactorLoop an Windows for aiohttp
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main_test())
