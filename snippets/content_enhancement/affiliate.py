import re
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import json

class AffiliateLinkManager:
    """
    Manages affiliate links, including adding tags to URLs, processing article content
    for affiliate links, and generating product link HTML.
    """
    DEFAULT_CONFIG = {
        'rakuten': {
            'tag_param': 'mafRakutenWidgetParam', # Standard Rakuten parameter
            'domains': [
                'hb.afl.rakuten.co.jp',
                'affiliate.rakuten.co.jp',
                'rpx.afl.rakuten.co.jp', # Another common Rakuten domain
                's.click.aliexpress.com', # Example if also handling AliExpress via Rakuten
            ],
            'default_tracking_id': '', # User needs to set this
        },
        'amazon': {
            'tag_param': 'tag', # Standard Amazon parameter
            'domains': [
                'amazon.com', 'amazon.co.jp', 'amazon.co.uk', # etc.
                'amzn.to' # Amazon short links
            ],
            'default_tracking_id': '', # User needs to set this (e.g., yourassociateid-20)
        }
        # Add other services here
    }

    def __init__(self, service_configs: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initializes the AffiliateLinkManager.

        Args:
            service_configs: A dictionary defining configurations for affiliate services.
                             If None, uses DEFAULT_CONFIG. Each service config should include:
                             - 'tag_param': The URL parameter name for the affiliate tag/ID.
                             - 'domains': A list of domains associated with this service.
                             - 'default_tracking_id': The default affiliate tag/ID to use for this service.
        """
        self.service_configs = service_configs if service_configs is not None else self.DEFAULT_CONFIG

    def set_tracking_id(self, service_name: str, tracking_id: str) -> bool:
        """
        Sets the default tracking ID for a specific affiliate service.

        Args:
            service_name: The name of the affiliate service (e.g., 'rakuten', 'amazon').
            tracking_id: The affiliate tracking ID.

        Returns:
            True if the service exists and ID was set, False otherwise.
        """
        if service_name in self.service_configs:
            self.service_configs[service_name]['default_tracking_id'] = tracking_id
            return True
        print(f"Warning: Service '{service_name}' not found in configurations.")
        return False

    def get_affiliate_service_for_url(self, url: str) -> Optional[str]:
        """
        Detects which configured affiliate service a URL belongs to.

        Args:
            url: The URL string to check.

        Returns:
            The name of the affiliate service if detected, otherwise None.
        """
        if not url:
            return None
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            for service_name, config in self.service_configs.items():
                if any(affiliate_domain in domain for affiliate_domain in config.get('domains', [])):
                    return service_name
        except ValueError: # Handle malformed URLs
            return None
        return None

    def add_tracking_to_url(self, url: str, service_name: Optional[str] = None, tracking_id: Optional[str] = None) -> str:
        """
        Adds an affiliate tracking ID to a given URL if it matches a configured service.

        Args:
            url: The original URL.
            service_name: The name of the affiliate service. If None, it will be auto-detected.
            tracking_id: The specific tracking ID to use. If None, the service's
                         default_tracking_id will be used.

        Returns:
            The modified URL with the tracking ID, or the original URL if no tracking was added.
        """
        if not url:
            return ""

        detected_service = service_name or self.get_affiliate_service_for_url(url)
        if not detected_service or detected_service not in self.service_configs:
            return url

        config = self.service_configs[detected_service]
        tag_to_use = tracking_id or config.get('default_tracking_id')
        tag_param = config.get('tag_param')

        if not tag_to_use or not tag_param:
            # print(f"Debug: No tag or param for service {detected_service}. URL: {url}")
            return url # No tag to add or param name missing

        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query, keep_blank_values=True) # Keep blank to avoid losing params

            # Add or update the tracking parameter
            query_params[tag_param] = [tag_to_use]

            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment
            ))
            return new_url
        except ValueError: # Handle malformed URLs
            return url


    def process_html_content(self, html_content: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Processes HTML content to find and modify affiliate links.

        Args:
            html_content: The HTML content string.

        Returns:
            A tuple containing:
            - The modified HTML content with updated affiliate links.
            - A list of dictionaries, each detailing an original and modified URL.
        """
        if not html_content:
            return "", []

        # Regex to find URLs within href attributes of <a> tags
        # This is safer than a generic URL regex for HTML processing.
        # It captures the full <a> tag to allow replacement.
        link_pattern = re.compile(r'(<a\s+(?:[^>]*?\s+)?href=(["\']))(.*?)\2')

        processed_links_info: List[Dict[str, str]] = []

        def replace_link(match):
            prefix = match.group(1) # <a ... href="
            original_url = match.group(3) # The URL itself

            modified_url = self.add_tracking_to_url(original_url)

            if original_url != modified_url:
                processed_links_info.append({
                    'original_url': original_url,
                    'modified_url': modified_url,
                    'service': self.get_affiliate_service_for_url(original_url) or "unknown"
                })
            return f"{prefix}{modified_url}{match.group(2)}" # match.group(2) is the quote " or '

        modified_html_content = link_pattern.sub(replace_link, html_content)

        return modified_html_content, processed_links_info

    def generate_product_link_html(
        self,
        product_name: str,
        product_url: str,
        service_name: Optional[str] = None, # e.g., 'amazon', 'rakuten'
        tracking_id: Optional[str] = None,
        image_url: Optional[str] = None,
        price: Optional[str] = None,
        description: Optional[str] = None,
        button_text: str = "View Product"
    ) -> str:
        """
        Generates an HTML block for a product, with an affiliate-tagged link.

        Args:
            product_name: Name of the product.
            product_url: The direct URL to the product page.
            service_name: The affiliate service for this product. If None, will try to detect.
            tracking_id: Specific tracking ID to use. If None, service default is used.
            image_url: URL of the product image.
            price: Price of the product (string).
            description: Short description of the product.
            button_text: Text for the call-to-action button.

        Returns:
            An HTML string for the product display.
        """
        affiliate_product_url = self.add_tracking_to_url(product_url, service_name, tracking_id)

        html_parts = [f'<div class="affiliate-product-snippet" data-service="{service_name or "unknown"}">']
        if image_url:
            html_parts.append(f'    <img src="{escape(image_url)}" alt="{escape(product_name)}" class="product-image">')
        html_parts.append(f'    <h4 class="product-name"><a href="{escape(affiliate_product_url)}" target="_blank" rel="noopener sponsored">{escape(product_name)}</a></h4>')
        if price:
            html_parts.append(f'    <p class="product-price">{escape(price)}</p>')
        if description:
            html_parts.append(f'    <p class="product-description">{escape(description)}</p>')
        html_parts.append(f'    <a href="{escape(affiliate_product_url)}" class="product-button" target="_blank" rel="noopener sponsored">{escape(button_text)}</a>')
        html_parts.append('</div>')

        return "\n".join(html_parts)

if __name__ == '__main__':
    print("--- Testing AffiliateLinkManager ---")
    manager = AffiliateLinkManager()

    # Set some default tracking IDs for testing
    manager.set_tracking_id('rakuten', 'myrakutenid-001')
    manager.set_tracking_id('amazon', 'myamazonid-20')

    print("\\n--- Test 1: URL Tagging ---")
    rakuten_url = "http://hb.afl.rakuten.co.jp/hgc/12345/?pc=http%3A%2F%2Fexample.com"
    tagged_rakuten_url = manager.add_tracking_to_url(rakuten_url)
    print(f"Original Rakuten URL: {rakuten_url}")
    print(f"Tagged Rakuten URL: {tagged_rakuten_url}")
    assert manager.service_configs['rakuten']['default_tracking_id'] in tagged_rakuten_url
    assert manager.service_configs['rakuten']['tag_param'] in tagged_rakuten_url


    amazon_url = "https://www.amazon.co.jp/dp/B08SAMPLEID/ref=sxts_sxwds-bia-wc-p13n1_0"
    tagged_amazon_url = manager.add_tracking_to_url(amazon_url, service_name='amazon', tracking_id='customamazon-21')
    print(f"Original Amazon URL: {amazon_url}")
    print(f"Tagged Amazon URL (custom ID): {tagged_amazon_url}")
    assert 'customamazon-21' in tagged_amazon_url
    assert manager.service_configs['amazon']['tag_param'] + '=customamazon-21' in tagged_amazon_url

    non_affiliate_url = "http://www.google.com"
    tagged_non_affiliate = manager.add_tracking_to_url(non_affiliate_url)
    print(f"Non-affiliate URL: {non_affiliate_url}")
    print(f"Tagged non-affiliate URL: {tagged_non_affiliate}")
    assert non_affiliate_url == tagged_non_affiliate

    print("\\n--- Test 2: HTML Content Processing ---")
    sample_html = f"""
    <p>Check out this awesome product: <a href="{rakuten_url}">Rakuten Product</a>.</p>
    <p>Also available on <a href="{amazon_url}">Amazon</a>!</p>
    <p>A normal link to <a href="http://example.com">Example Corp</a>.</p>
    """
    modified_html, processed_info = manager.process_html_content(sample_html)
    print("Original HTML:")
    print(sample_html)
    print("Modified HTML:")
    print(modified_html)
    print("Processed Links Info:")
    for info in processed_info:
        print(f"  - From: {info['original_url']} To: {info['modified_url']} (Service: {info['service']})")

    assert manager.service_configs['rakuten']['default_tracking_id'] in modified_html
    assert manager.service_configs['amazon']['default_tracking_id'] in modified_html # Default used as no custom ID passed to process_html_content
    assert "example.com" in modified_html and manager.service_configs['rakuten']['tag_param'] not in modified_html.split("example.com")[0][-50:] # Rough check

    print("\\n--- Test 3: Generate Product Link HTML ---")
    product_html = manager.generate_product_link_html(
        product_name="Cool Gadget",
        product_url="https://www.amazon.co.jp/dp/B09COOLGADGET",
        service_name="amazon", # Explicitly set service
        image_url="http://example.com/gadget.jpg",
        price="¥19,800",
        description="A very cool gadget you need."
    )
    print("Generated Product HTML:")
    print(product_html)
    assert manager.service_configs['amazon']['default_tracking_id'] in product_html
    assert "Cool Gadget" in product_html
    assert "gadget.jpg" in product_html

    print("\\nAffiliateLinkManager tests finished.")
