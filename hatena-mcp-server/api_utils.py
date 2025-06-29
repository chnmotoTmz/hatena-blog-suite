import requests
import json
import os
import re
from collections import Counter
import logging
from http.client import HTTPConnection
import pdb

# ロギングの設定
def setup_logging():
    # ルートロガーの設定
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # requestsとurllibのロガーを設定
    logging.getLogger("requests").setLevel(logging.WARNING) # INFO or WARNING is usually enough
    logging.getLogger("urllib3").setLevel(logging.WARNING) # INFO or WARNING is usually enough
    
    # HTTP接続のデバッグログを有効化 (必要な場合のみDEBUGに)
    # HTTPConnection.debuglevel = 1 

def log_request(response):
    logger = logging.getLogger(__name__)
    # Log less verbosely, or make it configurable
    logger.info(f"Request to {response.request.url} returned {response.status_code}")
    if response.status_code >= 400: # Log errors in more detail
        logger.error(f"Request URL: {response.request.url}")
        logger.error(f"Request method: {response.request.method}")
        content_type_req = response.request.headers.get('Content-Type', 'Not specified')
        logger.error(f"Request Content-Type: {content_type_req}")
        body_length = len(response.request.body) if response.request.body else 0
        logger.error(f"Request body length: {body_length}")
        
        logger.error(f"Response status: {response.status_code}")
        content_type_resp = response.headers.get('Content-Type', 'Not specified')
        logger.error(f"Response Content-Type: {content_type_resp}")
        # Avoid logging full response text unless it's small or specifically for debugging
        content_preview = response.text[:200] if response.text else "No content"
        logger.error(f"Response content preview: {content_preview}")


def assign_role(message):
    """Automatically assign a role to the message based on its content using advanced rules and scoring."""
    
    roles = ["USER", "CHATBOT", "SYSTEM", "TOOL"]
    scores = {role: 0 for role in roles}

    # Define keywords for each role
    keywords = {
        "USER": ["お願い", "質問", "教えて", "どうすれば", "なぜ", "ユーザー", "知りたい", "方法", "やり方", "困っている", "問題", "ヘルプ"],
        "CHATBOT": ["こんにちは", "ありがとう", "どういたしまして", "会話", "はい", "いいえ", "確認", "了解", "かしこまりました"],
        "SYSTEM": ["設定", "システム", "エラー", "指示", "操作", "システムメッセージ", "完了", "状態", "バージョン", "アップデート"],
        "TOOL": ["検索", "ツール", "データ", "API", "計算", "解析", "処理", "分析", "変換", "生成", "抽出", "翻訳"]
    }

    # Count keyword occurrences
    words = message.lower().split()
    word_counter = Counter(words)
    
    # Calculate scores based on keyword occurrence
    for role, role_keywords in keywords.items():
        scores[role] = sum(word_counter[word] for word in role_keywords if word in word_counter)

    # Additional context-based scoring
    if "エラー" in message or "システム" in message:
        scores["SYSTEM"] += 2
    if "検索" in message or "ツール" in message:
        scores["TOOL"] += 2
    if "ありがとう" in message or message.strip() in ["はい", "いいえ", "了解"]:
        scores["CHATBOT"] += 2
    if any(keyword in message for keyword in ["お願い", "教えて", "質問"]):
        scores["USER"] += 2

    # Determine the role with the highest score
    assigned_role = max(scores, key=scores.get)

    # If no significant keywords are found, default to "USER"
    if all(score == 0 for score in scores.values()):
        assigned_role = "USER"

    return assigned_role


    
def summarize_chat_history_google(chat_history, api_key):
    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'
    headers = {'Content-Type': 'application/json'}
    
    history_text = "\n".join([f"{msg['role']}: {msg['message']}" for msg in chat_history])
    
    prompt = f"以下のチャット履歴を簡潔に要約してください：\n\n{history_text}"
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {'key': api_key}

    try:
        response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
        log_request(response)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                for part in candidate['content']['parts']:
                    if 'text' in part:
                        return part['text']
            
            logging.error(f"Unexpected response structure in summarize_chat_history_google: {candidate}")
            return "Error: Unexpected response structure"
        else:
            logging.error(f"No candidates in API response (summarize_chat_history_google): {result}")
            return "Error: No valid response from API"
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in summarize_chat_history_google: {str(e)}")
        return "Error: Failed to parse API response"
    except KeyError as e:
        logging.error(f"KeyError in summarize_chat_history_google: {str(e)}")
        return f"Error: Unexpected response structure - missing key {str(e)}"
    except requests.RequestException as e:
        logging.error(f"Request error in summarize_chat_history_google: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logging.error(f"Unexpected error in summarize_chat_history_google: {str(e)}")
        return "Error: An unexpected error occurred"

def generate_response(chat_history, message, google_api_key, cohere_api_key):
    """
    まずGoogleのAPIを使用して応答を生成し、失敗した場合やレスポンスが不十分な場合はCohereにフォールバックする
    """
    google_response, updated_history = generate_response_google(chat_history, message, google_api_key)
    
    if is_response_adequate(google_response):
        return google_response, updated_history
    else:
        logging.info("Google APIの応答が不十分です。Cohereにフォールバックします。")
        cohere_response, updated_history = generate_response_cohere(chat_history, message, cohere_api_key,google_api_key)
        return cohere_response, updated_history

def is_response_adequate(response):
    """
    応答が適切かどうかを判断する
    この関数は必要に応じて拡張できます
    """
    if not response or response.startswith("Error:"):
        return False
    if len(response.split()) < 5:  # Example: response with less than 5 words is inadequate
        return False
    return True

def generate_response_google(chat_history, message, api_key):

    url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'
    headers = {'Content-Type': 'application/json'}

    history_summary = summarize_chat_history_google(chat_history, api_key)
    if history_summary.startswith("Error:"): # Handle summary error
        history_summary = "Could not summarize previous conversation."

    last_turn = chat_history[-1] if chat_history else {"role": "SYSTEM", "message": "This is the start of the conversation."}

    prompt = f"""
    This is a summary of the previous conversation: {history_summary}
    
    Last message:
    {last_turn['role']}: {last_turn['message']}
    
    New message:
    {assign_role(message)}: {message}
    
    Considering the context above, generate an appropriate response.
    """

    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {'key': api_key}

    try:
        response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
        log_request(response)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates'] and \
           'content' in result['candidates'][0] and \
           'parts' in result['candidates'][0]['content'] and \
           result['candidates'][0]['content']['parts'][0].get('text'):
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
        else:
            generated_text = "Error: Unable to generate response from Google API."
            logging.error(f"Google API bad response structure: {result}")


        updated_history = chat_history + [ # Append to existing history
            {"role": assign_role(message), "message": message},
            {"role": "CHATBOT", "message": generated_text}
        ]
        
        return generated_text, updated_history
    except requests.RequestException as e:
        logging.error(f"Error in generate_response_google (request): {str(e)}")
        return f"Error: {str(e)}", chat_history
    except Exception as e:
        logging.error(f"Error in generate_response_google (general): {str(e)}")
        return f"Error: {str(e)}", chat_history

def generate_response_cohere(chat_history, message, api_key, google_api_key):
    url = "https://api.cohere.ai/v1/chat"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}" # Corrected to use Bearer token
    }

    history_summary = summarize_chat_history_google(chat_history, google_api_key)
    if history_summary.startswith("Error:"):
        history_summary = "Could not summarize previous conversation."
    
    # Cohere expects history in a specific format
    cohere_chat_history = []
    if chat_history: # Only add summary if there's actual history
        cohere_chat_history.append({"role": "SYSTEM", "message": f"This is a summary of the previous conversation: {history_summary}"})
    for turn in chat_history:
        # Cohere roles: USER, CHATBOT, SYSTEM, TOOL (TOOL_RESULTS for tool output)
        # Map roles if necessary, assuming 'USER' and 'CHATBOT' are fine
        cohere_chat_history.append({"role": turn["role"], "message": turn["message"]})


    data = {
        "chat_history": cohere_chat_history,
        "message": message,
        "connectors": [{"id": "web-search"}] # If you want web search
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        log_request(response)
        response.raise_for_status()
        response_data = response.json()
        generated_text = response_data.get('text', "Error: No 'text' key found in Cohere API response.")
        
        updated_history = chat_history + [ # Append to original history
            {"role": assign_role(message), "message": message}, # Use assigned role for the input message
            {"role": "CHATBOT", "message": generated_text}
        ]
        
        return generated_text, updated_history
    except requests.RequestException as e:
        logging.error(f"Error in generate_response_cohere (request): {str(e)}")
        return f"Error: {str(e)}", chat_history
    except Exception as e:
        logging.error(f"Error in generate_response_cohere (general): {str(e)}")
        return f"Error: {str(e)}", chat_history

def generate_summary_cohere(text: str, length: str = "medium") -> str:
    """
    Cohere APIを使用してテキストを要約します。
    length: "short", "medium", "long" (maps to Cohere's length parameter)
    """
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        logging.error("COHERE_API_KEY is not set.")
        return "Error: COHERE_API_KEY is not set."

    url = "https://api.cohere.ai/v1/summarize"
    payload = {
        "text": text,
        "length": length,  # 'short', 'medium', or 'long'
        "format": "paragraph",  # 'paragraph' or 'bullets'
        "model": "command", # Specify model, e.g., 'command-r' or 'command-light'
        "extractiveness": "auto",  # 'low', 'medium', 'high', 'auto'
        "temperature": 0.3, # Optional: A value between 0.0 and 1.0.
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        log_request(response)
        response.raise_for_status()
        result = response.json()
        if "summary" in result:
            return result["summary"]
        else:
            error_msg = result.get('message', 'No error message provided by API.')
            logging.error(f"Cohere Summarize API did not return a summary: {error_msg}. Full response: {result}")
            return f"Error: Could not generate summary. API Message: {error_msg}"
    except requests.RequestException as e:
        logging.error(f"Cohere Summarize API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response status code: {e.response.status_code}")
            logging.error(f"Response content: {e.response.text}")
            return f"Error: Cohere API request failed - Status: {e.response.status_code}, Body: {e.response.text}"
        return f"Error: Cohere API request failed - {str(e)}"
    except Exception as e:
        logging.error(f"An unexpected error occurred in generate_summary_cohere: {e}")
        return f"Error: An unexpected error occurred - {str(e)}"

def extract_keywords_cohere(text: str, num_keywords: int = 5) -> list[str]:
    """
    Cohere API (Generate endpoint) を使用してキーワードを抽出します。
    """
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        logging.error("COHERE_API_KEY is not set.")
        return ["Error: COHERE_API_KEY is not set."]

    # Prompt designed for keyword extraction.
    prompt = f"""Extract the {num_keywords} most relevant keywords or key phrases from the following text.
The keywords should be returned as a comma-separated list. Do not add any introductory text or numbering.

Text:
"{text}"

Keywords:"""

    url = "https://api.cohere.ai/v1/generate"
    payload = {
        "prompt": prompt,
        "model": "command",  # Or another suitable generation model from Cohere
        "max_tokens": num_keywords * 10,  # Adjusted for typical keyword length and separators
        "temperature": 0.2,  # Lower temperature for more focused and deterministic output
        "k": 0, # For nucleus sampling, k=0 disables it if p is used.
        "p": 0.75, # Nucleus sampling: consider top 75% probable tokens
        "frequency_penalty": 0.2, # Slight penalty for repeating tokens
        "presence_penalty": 0.1,  # Slight penalty for new tokens if they are not relevant
        "stop_sequences": ["\n", "---"],  # Stop generation if a new line or separator is encountered
        "return_likelihoods": "NONE"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        log_request(response)
        response.raise_for_status()
        result = response.json()
        
        if result.get("generations") and result["generations"][0].get("text"):
            generated_text = result["generations"][0]["text"].strip()
            
            # Clean up the generated text:
            # Remove potential prefixes like "Keywords:" if the model adds them.
            if generated_text.lower().startswith("keywords:"):
                generated_text = generated_text[len("keywords:"):].strip()
            
            # Split into keywords and clean each one
            keywords = [kw.strip().rstrip('.').strip() for kw in generated_text.split(',') if kw.strip()]
            # Filter out very short strings or any empty strings resulting from split
            keywords = [kw for kw in keywords if len(kw) > 1 and kw.lower() != "error"] 
            return keywords[:num_keywords]
        else:
            error_msg = result.get('message', 'No error message provided by API.')
            logging.error(f"Cohere Generate API did not return expected generations: {error_msg}. Full response: {result}")
            return [f"Error: Could not extract keywords. API Message: {error_msg}"]
            
    except requests.RequestException as e:
        logging.error(f"Cohere Generate API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response status code: {e.response.status_code}")
            logging.error(f"Response content: {e.response.text}")
            return [f"Error: Cohere API request failed - Status: {e.response.status_code}, Body: {e.response.text}"]
        return [f"Error: Cohere API request failed - {str(e)}"]
    except Exception as e:
        logging.error(f"An unexpected error occurred in extract_keywords_cohere: {e}")
        return [f"Error: An unexpected error occurred - {str(e)}"]


if __name__ == "__main__":
    setup_logging() 
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    cohere_api_key = os.getenv("COHERE_API_KEY")

    if not google_api_key:
        print("Warning: GOOGLE_API_KEY not set. Some tests might be skipped or fail.")
    if not cohere_api_key:
        print("Warning: COHERE_API_KEY not set. Cohere specific tests will be skipped.")

    # Test summarize_chat_history_google (if google_api_key is set)
    if google_api_key:
        sample_chat_history = [
            {"role": "USER", "message": "こんにちは、天気について教えてください。"},
            {"role": "CHATBOT", "message": "はい、どの地域の天気をお知りになりたいですか？"}
        ]
        summary_google = summarize_chat_history_google(sample_chat_history, google_api_key)
        print(f"Google Chat History Summary: {summary_google}\n")

    # Test Cohere summary (if cohere_api_key is set)
    if cohere_api_key:
        sample_text_for_summary = """
        大規模言語モデル（LLM）は、近年、自然言語処理（NLP）の分野で注目を集めている技術です。
        これらのモデルは、大量のテキストデータで訓練され、人間が書いたような自然な文章を生成したり、
        質問に答えたり、文章を要約したりすることができます。LLMの応用範囲は広く、
        カスタマーサポート、コンテンツ作成、教育など、様々な分野での活用が期待されています。
        しかし、LLMには倫理的な課題や誤情報拡散のリスクも指摘されており、今後の研究開発においては、
        これらの課題への対応も重要となります。
        """
        summary_short_cohere = generate_summary_cohere(sample_text_for_summary, length="short")
        print(f"Cohere Summary (short): {summary_short_cohere}\n")

        summary_medium_cohere = generate_summary_cohere(sample_text_for_summary, length="medium")
        print(f"Cohere Summary (medium): {summary_medium_cohere}\n")

        summary_long_cohere = generate_summary_cohere(sample_text_for_summary, length="long")
        print(f"Cohere Summary (long): {summary_long_cohere}\n")

        # Test Cohere keyword extraction
        sample_text_for_keywords = """
        Pythonは、その読みやすさと汎用性から、Web開発、データサイエンス、機械学習、自動化など、
        多岐にわたる分野で利用されている人気のプログラミング言語です。豊富なライブラリと活発なコミュニティも、
        Pythonの魅力の一つです。初心者にも学びやすく、経験豊富な開発者にとっても強力なツールとなります。
        """
        keywords_cohere = extract_keywords_cohere(sample_text_for_keywords, num_keywords=5)
        print(f"Cohere Keywords: {keywords_cohere}\n")

        keywords_cohere_more = extract_keywords_cohere(sample_text_for_summary, num_keywords=7) # Test with different text
        print(f"Cohere Keywords (LLM text): {keywords_cohere_more}\n")
    else:
        print("Skipping Cohere specific tests as COHERE_API_KEY is not set.")

    # Test generate_response (Google and Cohere fallback if keys are set)
    if google_api_key and cohere_api_key:
        chat_hist_for_gen = [
            {"role": "USER", "message": "AI技術の最新トレンドについて教えて。"},
            {"role": "CHATBOT", "message": "AI技術のトレンドですね。特にどの分野に興味がありますか？例えば、生成AI、強化学習、倫理的なAIなどがあります。"}
        ]
        new_message = "生成AIについてもっと詳しく知りたいです。"
        
        print(f"Testing generate_response with new message: '{new_message}'")
        response_text, updated_hist = generate_response(chat_hist_for_gen, new_message, google_api_key, cohere_api_key)
        print(f"Generated Response: {response_text}")
        # print(f"Updated History: {updated_hist}")
    elif google_api_key:
        print("Testing generate_response_google only (COHERE_API_KEY not set)")
        chat_hist_for_gen_google = [
            {"role": "USER", "message": "今日の天気は？"},
        ]
        new_message_google = "東京の天気を教えてください。"
        response_text_google, _ = generate_response_google(chat_hist_for_gen_google, new_message_google, google_api_key)
        print(f"Google Generated Response: {response_text_google}")
    else:
        print("Skipping generate_response tests as GOOGLE_API_KEY or COHERE_API_KEY is not set.")
print("\napi_utils.py tests finished.")
