import os
import requests
from xml.etree import ElementTree as ET
from xml.dom import minidom
from adk import Agent, Tool
from dotenv import load_dotenv
from typing import Dict, List
from datetime import datetime
import hashlib
import random
import base64
import logging

# Attempt to import the function from article_updater
# This assumes article_updater.py will be correctly placed/updated in the environment
try:
    from article_updater import enhance_article_content_operations
except ImportError:
    logging.warning("Could not import enhance_article_content_operations from article_updater.py. Ensure the file and function are correctly defined.")
    # Define a placeholder if import fails, so the agent can still be defined
    def enhance_article_content_operations(content: str, keywords_prompt: str, internal_links_url: str, image_prompt: str, article_title: str) -> str:
        logging.error("enhance_article_content_operations (placeholder) called. The real function was not imported.")
        return f"Error: enhance_article_content_operations not available. Original content: {content}"

# 環境変数の読み込み
load_dotenv()

# Setup basic logging for the agent module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_credentials(username: str) -> tuple:
    """はてなAPIアクセスに必要な認証情報をタプルの形式で返す"""
    env_key = f"HATENA_BLOG_ATOMPUB_KEY_{username}"
    api_key = os.getenv(env_key)
    if not api_key:
        logger.error(f"環境変数 {env_key} が設定されていません")
        raise ValueError(f"API key for {username} not found. Set {env_key}.")
    return (username, api_key)

def wsse(username: str, api_key: str) -> str:
    """WSSEヘッダーを生成する"""
    nonce = hashlib.sha1(str(random.random()).encode()).digest()
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    password_digest = hashlib.sha1(nonce + now.encode() + api_key.encode()).digest()
    
    return f'''UsernameToken Username="{username}", PasswordDigest="{base64.b64encode(password_digest).decode()}", Nonce="{base64.b64encode(nonce).decode()}", Created="{now}"'''

def create_post_data(title: str, body: str, username: str, draft: str = 'no', category: str = None) -> bytes:
    """投稿用のXMLデータを生成する"""
    now = datetime.now()
    dtime = now.strftime("%Y-%m-%dT%H:%M:%S")
    category_tag = f'<category term="{category}" />' if category else '<category term="tech" />' # Default category
    template = f'''<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{title}</title>
    <author><name>{username}</name></author>
    <content type="text/html">{body.strip()}</content>
    <updated>{dtime}</updated>
    {category_tag}
    <app:control>
        <app:draft>{draft}</app:draft>
    </app:control>
</entry>'''
    return template.encode('utf-8')

def post_blog_entry(title: str, content: str, is_draft: bool = False, category: str = None) -> dict:
    """はてなブログに新規エントリを投稿する"""
    hatena_id = os.getenv("HATENA_ID")
    blog_domain = os.getenv("BLOG_DOMAIN")
    if not hatena_id or not blog_domain:
        return {"status": "error", "message": "HATENA_ID or BLOG_DOMAIN environment variables not set."}
    
    try:
        username, api_key = load_credentials(hatena_id)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    draft_status = 'yes' if is_draft else 'no'
    data = create_post_data(title, content, username, draft_status, category)
    headers = {'X-WSSE': wsse(username, api_key)}
    url = f'https://blog.hatena.ne.jp/{username}/{blog_domain}/atom/entry'

    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        entry_id_url = response.headers.get("Location", "")
        entry_id = entry_id_url.split("/")[-1] if entry_id_url else None
        public_link = None
        
        if response.text: # Check if response.text is not empty
            try:
                entry_root = ET.fromstring(response.text)
                link_node = entry_root.find("{http://www.w3.org/2005/Atom}link[@rel='alternate'][@type='text/html']")
                if link_node is not None:
                    public_link = link_node.get("href")
            except ET.ParseError as e:
                logger.warning(f"Failed to parse XML from POST response: {e}. Response text: {response.text[:200]}")

        return {"status": "success", "entry_id": entry_id, "url": entry_id_url, "public_link": public_link, "response_status_code": response.status_code}
    except requests.RequestException as e:
        logger.error(f"Error during blog post: {e}. Response: {e.response.text if e.response else 'No response'}")
        return {"status": "error", "message": str(e), "status_code": e.response.status_code if e.response is not None else None}
    except Exception as e:
        logger.error(f"Unexpected error in post_blog_entry: {e}")
        return {"status": "error", "message": str(e)}


def edit_blog_entry(entry_id: str, title: str, content: str, is_draft: bool = False, category: str = None) -> dict:
    """はてなブログの既存エントリを編集する"""
    hatena_id = os.getenv("HATENA_ID")
    blog_domain = os.getenv("BLOG_DOMAIN")
    if not hatena_id or not blog_domain:
        return {"status": "error", "message": "HATENA_ID or BLOG_DOMAIN environment variables not set."}

    try:
        username, api_key = load_credentials(hatena_id)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    draft_status = 'yes' if is_draft else 'no'
    data = create_post_data(title, content, username, draft_status, category)
    headers = {'X-WSSE': wsse(username, api_key)}
    url = f'https://blog.hatena.ne.jp/{username}/{blog_domain}/atom/entry/{entry_id}'

    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()
        
        public_link = None
        if response.text: # Check if response.text is not empty
            try:
                entry_root = ET.fromstring(response.text) # Hatena PUT response is usually the entry XML
                link_node = entry_root.find("{http://www.w3.org/2005/Atom}link[@rel='alternate'][@type='text/html']")
                if link_node is not None:
                    public_link = link_node.get("href")
            except ET.ParseError as e:
                 logger.warning(f"Failed to parse XML from PUT response: {e}. Response text: {response.text[:200]}")
        
        return {"status": "success", "entry_id": entry_id, "public_link": public_link, "response_status_code": response.status_code}
    except requests.RequestException as e:
        logger.error(f"Error during blog edit: {e}. Response: {e.response.text if e.response else 'No response'}")
        return {"status": "error", "message": str(e), "status_code": e.response.status_code if e.response is not None else None}
    except Exception as e:
        logger.error(f"Unexpected error in edit_blog_entry: {e}")
        return {"status": "error", "message": str(e)}

def is_draft(entry_element: ET.Element) -> bool:
    """ブログ記事がドラフトかどうか判定する"""
    app_ns = "{http://www.w3.org/2007/app}"
    control_element = entry_element.find(f".//{app_ns}control") # Use .// to find anywhere
    if control_element is not None:
        draft_element = control_element.find(f".//{app_ns}draft")
        if draft_element is not None and draft_element.text == "yes":
            return True
    return False

def get_public_link(entry_element: ET.Element) -> str | None:
    """エントリの公開リンクを取得する"""
    atom_ns = "{http://www.w3.org/2005/Atom}"
    # Find link with rel='alternate' and type='text/html'
    link_element = entry_element.find(f".//{atom_ns}link[@rel='alternate'][@type='text/html']")
    if link_element is not None:
        return link_element.get("href")
    return None

def get_blog_entries(page_url: str = None) -> List[Dict] | Dict:
    """ブログエントリの一覧を詳細情報付きで取得する. オプションでページURLを指定可能."""
    hatena_id = os.getenv("HATENA_ID")
    blog_domain = os.getenv("BLOG_DOMAIN")
    if not hatena_id or not blog_domain:
        return {"status": "error", "message": "HATENA_ID or BLOG_DOMAIN environment variables not set."}

    try:
        username, api_key = load_credentials(hatena_id)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    atom_ns = "{http://www.w3.org/2005/Atom}"
    
    if page_url:
        blog_entries_uri = page_url
    else:
        root_endpoint = f"https://blog.hatena.ne.jp/{hatena_id}/{blog_domain}/atom"
        blog_entries_uri = f"{root_endpoint}/entry"
    
    entries_data = []
    next_page_url = None

    logger.info(f"Fetching entries from: {blog_entries_uri}")
    try:
        response = requests.get(blog_entries_uri, auth=(username, api_key))
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching entries: {e}. Response: {e.response.text if e.response else 'No response'}")
        return {"status": "error", "message": f"Error fetching entries: {e}", "status_code": e.response.status_code if e.response is not None else None}

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as e:
        logger.error(f"Error parsing XML for entries: {e}. Response text: {response.text[:200]}")
        return {"status": "error", "message": f"Error parsing XML for entries: {e}"}
        
    next_link_element = root.find(f".//{atom_ns}link[@rel='next']")
    if next_link_element is not None:
        next_page_url = next_link_element.get('href')

    for entry_element in root.findall(f".//{atom_ns}entry"):
        title_element = entry_element.find(f".//{atom_ns}title")
        title = title_element.text if title_element is not None else "No Title"
        
        id_element = entry_element.find(f".//{atom_ns}id")
        entry_id = id_element.text.split("/")[-1] if id_element is not None and id_element.text else "Unknown ID"
        
        published_element = entry_element.find(f".//{atom_ns}published")
        published_date = published_element.text if published_element is not None else "No Published Date"

        updated_element = entry_element.find(f".//{atom_ns}updated")
        updated_date = updated_element.text if updated_element is not None else "No Updated Date"
        
        public_link = get_public_link(entry_element)
        draft_status = is_draft(entry_element)
        
        # Get categories
        categories = [cat.get("term") for cat in entry_element.findall(f".//{atom_ns}category") if cat.get("term")]

        entries_data.append({
            "id": entry_id, 
            "title": title,
            "public_link": public_link,
            "is_draft": draft_status,
            "published_date": published_date,
            "updated_date": updated_date,
            "categories": categories
        })
    
    # Return a dictionary if used for pagination, or just list for single use
    if page_url or next_page_url: # If pagination is involved
        return {"entries": entries_data, "next_page_url": next_page_url}
    return entries_data # If called without page_url and there's no next page

# --- ADK Tools Definition ---
post_tool = Tool(
    func=post_blog_entry,
    name="post_blog_entry",
    description="Hatena Blog に新規エントリを投稿します。タイトル(title: str), 本文(content: str)が必須です。オプションで下書き状態(is_draft: bool), カテゴリ(category: str)を指定できます。"
)

edit_tool = Tool(
    func=edit_blog_entry,
    name="edit_blog_entry",
    description="Hatena Blog の既存エントリを編集します。エントリID(entry_id: str)、新しいタイトル(title: str)、新しい本文(content: str)が必須です。オプションで下書き状態(is_draft: bool), カテゴリ(category: str)を指定できます。"
)

get_entries_tool = Tool(
    func=get_blog_entries,
    name="get_blog_entries",
    description="Hatena Blog のエントリ一覧を詳細情報付きで取得します。オプションでページURL(page_url: str)を指定し、次のページを取得できます。結果には'entries'リストと'next_page_url'が含まれることがあります。"
)

enhance_article_tool = Tool(
    func=enhance_article_content_operations,
    name="enhance_article_content",
    description="Enhances article HTML content using AI rewrite, keyword-based affiliate/internal links, and a generated image. Requires: content (str), keywords_prompt (str), internal_links_url (str for site base URL), image_prompt (str), article_title (str)."
)

# エージェントの作成
agent = Agent(
    tools=[post_tool, edit_tool, get_entries_tool, enhance_article_tool], # Added enhance_article_tool
    model_name="gemini-1.5-flash", 
    name="HatenaBlogAgent",
    description="A specialized agent for managing and enhancing Hatena Blog entries. It can post, edit, list entries, and enhance content with AI summaries, keywords, affiliate links, internal links, and images.",
    logger=logger # Pass the logger to the agent
)

# エージェントの実行例 (Interactive Loop)
if __name__ == "__main__":
    logger.info("Starting HatenaBlogAgent interactive session.")
    print("Welcome to the Hatena Blog Agent! Type 'exit' to quit.")

    # Check for essential environment variables for agent to function
    hatena_id_env = os.getenv("HATENA_ID")
    blog_domain_env = os.getenv("BLOG_DOMAIN")
    api_key_env_name = f"HATENA_BLOG_ATOMPUB_KEY_{hatena_id_env}" if hatena_id_env else None
    api_key_env = os.getenv(api_key_env_name) if api_key_env_name else None

    if not (hatena_id_env and blog_domain_env and api_key_env):
        logger.error(f"Essential Hatena environment variables are not set. Please set HATENA_ID, BLOG_DOMAIN, and {api_key_env_name}.")
        print(f"Error: Essential Hatena environment variables are not set. Please set HATENA_ID, BLOG_DOMAIN, and {api_key_env_name}.")
        print("The agent may not function correctly without these settings.")
    
    # Optional check for Cohere API key if enhance_article_tool is expected to be used
    if not os.getenv("COHERE_API_KEY"):
        logger.warning("COHERE_API_KEY is not set. The 'enhance_article_content' tool may not function as expected (might use placeholders or fail).")
        print("Warning: COHERE_API_KEY is not set. Content enhancement features might be limited.")

    while True:
        try:
            user_query = input("You: ")
            if user_query.strip().lower() == "exit":
                print("Agent: Exiting. Goodbye!")
                break
            if not user_query.strip():
                continue
            
            # Assuming agent.run() handles the full interaction including calling LLM if needed
            # and returning a string or directly printable result.
            result = agent.run(user_query) 
            print(f"Agent: {result}")

        except KeyboardInterrupt:
            print("\nAgent: Exiting due to keyboard interrupt. Goodbye!")
            break
        except Exception as e:
            logger.error(f"An error occurred in the interactive loop: {e}", exc_info=True)
            print(f"Agent: An unexpected error occurred: {e}")

    logger.info("HatenaBlogAgent interactive session finished.")
