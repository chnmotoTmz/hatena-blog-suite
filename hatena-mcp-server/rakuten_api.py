# rakuten_api.py

import requests
import os
import logging

# Setup basic logging
logger = logging.getLogger(__name__)
if not logger.handlers: # Add handler if not already configured by root logger
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID") # Changed from RAKUTEN_API_KEY to RAKUTEN_APP_ID for consistency
RAKUTEN_AFFILIATE_ID = os.getenv("RAKUTEN_AFFILIATE_ID")


def search_products(keyword: str, applicationId: str = None) -> list | dict:
    """
    Searches for products on Rakuten Ichiba based on a keyword.
    Returns a list of products or an error dictionary.
    `applicationId` can be passed, otherwise it uses the environment variable RAKUTEN_APP_ID.
    """
    app_id_to_use = applicationId if applicationId else RAKUTEN_APP_ID

    if not app_id_to_use:
        logger.error("Rakuten Application ID (RAKUTEN_APP_ID) is not set.")
        return {"status": "error", "message": "Rakuten Application ID is not configured."}

    # API endpoint for Rakuten Ichiba Item Search API
    # Version 2022-06-01 is an example, check for the latest or most suitable version.
    # The original used 2017-04-04 for product search, which might be for a different API (Product API vs Item Search API).
    # Let's stick to a more general item search for now.
    # The URL from the original code was: "https://api.rakuten.co.jp/ichiba/product/search/20170404"
    # A more common one is: "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    # For this task, I'll use the one provided in the original snippet if it was functional.
    # Let's assume the original "product/search" was intended and worked.
    
    # The original code in article_updater was calling this with `applicationId` as a kwarg
    # but the old definition didn't take it. Now it does.
    
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601" # More recent version
    # url = "https://api.rakuten.co.jp/ichiba/product/search/20170404" # As per original snippet, but this might be Product API
    
    params = {
        "format": "json",
        "keyword": keyword,
        "applicationId": app_id_to_use,
        "hits": 5,  # Number of items to return, adjust as needed
        # "sort": "standard" # Default sort
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if "Items" in data and data["Items"]:
            products = []
            for item in data["Items"]:
                # Ensure 'item' is a dictionary, then access 'Item' key
                actual_item = item.get('Item', item) if isinstance(item, dict) else item
                if isinstance(actual_item, dict):
                    products.append({
                        "itemName": actual_item.get("itemName"),
                        "itemPrice": actual_item.get("itemPrice"),
                        "itemUrl": actual_item.get("itemUrl"),
                        "itemCode": actual_item.get("itemCode"), # Important for affiliate links
                        "imageUrl": actual_item.get("mediumImageUrls", [{}])[0].get("imageUrl") if actual_item.get("mediumImageUrls") else None
                    })
                else:
                    logger.warning(f"Unexpected item structure in Rakuten API response: {actual_item}")
            return products
        elif "error" in data:
            logger.error(f"Rakuten API error: {data.get('error_description', data['error'])}")
            return {"status": "error", "message": f"Rakuten API error: {data.get('error_description', data['error'])}"}
        else:
            logger.info(f"No items found for keyword: {keyword}. Response: {data}")
            return [] # Return empty list if no items but no error

    except requests.RequestException as e:
        logger.error(f"Request to Rakuten API failed: {e}")
        return {"status": "error", "message": f"Request to Rakuten API failed: {e}"}
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from Rakuten API.")
        return {"status": "error", "message": "Failed to decode JSON response from Rakuten API."}


def generate_affiliate_link(item_url: str, item_price: str, affiliate_id: str, product_name: str) -> str:
    """
    Generates a Rakuten affiliate link.
    This is a conceptual function. Actual Rakuten affiliate link generation
    might involve their specific tools/APIs or formatting rules.
    A common way is to use Rakuten Web Service for link generation or specific affiliate portals.
    For now, this creates a basic affiliate link structure.
    """
    if not affiliate_id:
        logger.warning("RAKUTEN_AFFILIATE_ID is not set. Cannot generate affiliate link.")
        return f"Error: RAKUTEN_AFFILIATE_ID not set. Original URL: {item_url}"
    
    if not item_url:
        logger.warning("Item URL is missing. Cannot generate affiliate link.")
        return "Error: Item URL is missing."

    # Example affiliate link structure (this is a simplified placeholder)
    # Real Rakuten affiliate links often look like:
    # https://hb.afl.rakuten.co.jp/hgc/[YourAffiliateID]/?pc=[EncodedItemURL]&m=http%3A%2F%2Fm.rakuten.co.jp%2F
    # Or involve using their LinkShare/TG platform.
    # This placeholder is for demonstrating the flow.
    
    # A simple approach if you have a direct affiliate link generator or format:
    # This is a highly simplified example and likely not a functional Rakuten affiliate link.
    # Consult Rakuten's affiliate program documentation for correct link formatting.
    try:
        from urllib.parse import quote
        encoded_item_url = quote(item_url)
        # This is a common pattern, but the exact format depends on the Rakuten affiliate program details.
        aff_link = f"https://hb.afl.rakuten.co.jp/hgc/{affiliate_id}/?pc={encoded_item_url}&m=http%3A%2F%2Fm.rakuten.co.jp%2F"
        logger.info(f"Generated affiliate link for {product_name}: {aff_link}")
        return aff_link
    except Exception as e:
        logger.error(f"Error generating affiliate link for {product_name}: {e}")
        return f"Error generating affiliate link. Original URL: {item_url}"

if __name__ == '__main__':
    logger.info("Testing Rakuten API functions...")
    if not RAKUTEN_APP_ID:
        logger.warning("RAKUTEN_APP_ID is not set in environment variables. API calls will fail or use mocks.")
        print("Please set RAKUTEN_APP_ID environment variable for live testing.")
    
    if not RAKUTEN_AFFILIATE_ID:
        logger.warning("RAKUTEN_AFFILIATE_ID is not set. Affiliate links will show an error or be incomplete.")
        print("Please set RAKUTEN_AFFILIATE_ID environment variable for live testing.")

    # Test search_products
    keyword_to_search = "Python プログラミング" # Python Programming
    print(f"\nSearching for products with keyword: '{keyword_to_search}'")
    products_result = search_products(keyword_to_search)

    if isinstance(products_result, dict) and products_result.get("status") == "error":
        print(f"Error searching products: {products_result['message']}")
    elif products_result:
        print(f"Found {len(products_result)} products (showing first 2):")
        for i, product in enumerate(products_result[:2]):
            print(f"  Product {i+1}:")
            print(f"    Name: {product.get('itemName')}")
            print(f"    Price: {product.get('itemPrice')}")
            print(f"    URL: {product.get('itemUrl')}")
            print(f"    Image URL: {product.get('imageUrl')}")
            print(f"    Item Code: {product.get('itemCode')}")
            
            # Test generate_affiliate_link with the first product found
            if i == 0 and product.get("itemUrl") and RAKUTEN_AFFILIATE_ID:
                print("\n  Generating affiliate link for the first product...")
                aff_link = generate_affiliate_link(
                    item_url=product["itemUrl"],
                    item_price=str(product.get("itemPrice", "")),
                    affiliate_id=RAKUTEN_AFFILIATE_ID,
                    product_name=product.get("itemName", "Test Product")
                )
                print(f"    Affiliate Link: {aff_link}")
            elif i==0:
                 print("\n  Skipping affiliate link generation for first product (missing URL or RAKUTEN_AFFILIATE_ID).")

    else:
        print("No products found or an unexpected error occurred.")

    # Test with missing API Key for search
    print("\nTesting search_products with Application ID explicitly set to None (should fail gracefully):")
    error_search_result = search_products(keyword_to_search, applicationId=None) # Override to test
    if isinstance(error_search_result, dict) and error_search_result.get("status") == "error":
        print(f"Graceful failure for missing App ID: {error_search_result['message']}")
    else:
        print(f"Unexpected result for missing App ID test: {error_search_result}")
        
    print("\nRakuten API tests finished.")