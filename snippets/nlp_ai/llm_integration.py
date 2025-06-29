import os
import requests
import json
from typing import List, Dict, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# --- Google Gemini Integration ---

def summarize_chat_history_google(
    chat_history: List[Dict[str, str]],
    api_key: str,
    model: str = "gemini-1.5-flash-latest"
) -> Optional[str]:
    """
    Summarizes chat history using Google Gemini API.

    Args:
        chat_history: A list of message dictionaries, e.g., [{"role": "USER", "message": "Hello"}].
        api_key: Google API key.
        model: The Gemini model to use for summarization.

    Returns:
        The summary text, or None if an error occurs.
    """
    if not api_key:
        logger.error("Google API key not provided for chat history summarization.")
        return None
    if not chat_history:
        return "No chat history to summarize."

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    headers = {'Content-Type': 'application/json'}

    history_text = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('message', '')}" for msg in chat_history])
    prompt = f"以下のチャット履歴を簡潔に要約してください。重要なポイントや話題の変遷がわかるように記述してください。:\n\n{history_text}"

    data = {"contents": [{"parts": [{"text": prompt}]}]}
    params = {'key': api_key}

    try:
        response = requests.post(url, headers=headers, params=params, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        result = response.json()

        candidate = result.get('candidates', [{}])[0]
        if candidate and candidate.get('content', {}).get('parts', [{}])[0].get('text'):
            return candidate['content']['parts'][0]['text']
        else:
            logger.error(f"Unexpected response structure from Google (summarize): {result}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error in Google summarization: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Google summarization: {e}")
        return None

def generate_response_google(
    chat_history: List[Dict[str, str]],
    new_message: str,
    api_key: str,
    model: str = "gemini-1.5-flash-latest",
    system_instruction: Optional[str] = None
) -> Optional[str]:
    """
    Generates a response using Google Gemini API based on chat history and a new message.

    Args:
        chat_history: List of previous messages.
        new_message: The new user message to respond to.
        api_key: Google API key.
        model: The Gemini model to use.
        system_instruction: Optional system-level instruction for the model.

    Returns:
        The generated response text, or None if an error occurs.
    """
    if not api_key:
        logger.error("Google API key not provided for response generation.")
        return None

    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    headers = {'Content-Type': 'application/json'}

    # Constructing the 'contents' payload for Gemini
    # Roles should be 'user' or 'model'. System instructions can be at the start.
    gemini_contents = []
    if system_instruction:
        gemini_contents.append({"role": "user", "parts": [{"text": system_instruction}]}) # System as user
        gemini_contents.append({"role": "model", "parts": [{"text": "Understood."}]}) # Dummy model ack

    for msg in chat_history:
        role = "user" if msg.get("role", "").upper() == "USER" else "model"
        gemini_contents.append({"role": role, "parts": [{"text": msg.get("message", "")}]})

    gemini_contents.append({"role": "user", "parts": [{"text": new_message}]})

    data = {"contents": gemini_contents}
    params = {'key': api_key}

    try:
        response = requests.post(url, headers=headers, params=params, data=json.dumps(data), timeout=45)
        response.raise_for_status()
        result = response.json()

        candidate = result.get('candidates', [{}])[0]
        if candidate and candidate.get('content', {}).get('parts', [{}])[0].get('text'):
            return candidate['content']['parts'][0]['text']
        else:
            logger.error(f"Unexpected response structure from Google (generate_response): {result}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error in Google response generation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Google response generation: {e}")
        return None

# --- Cohere Integration ---

def generate_summary_cohere(
    text_to_summarize: str,
    api_key: str,
    length: str = "medium",
    model: str = "command"
) -> Optional[str]:
    """
    Summarizes text using Cohere API.

    Args:
        text_to_summarize: The text to summarize.
        api_key: Cohere API key.
        length: "short", "medium", or "long".
        model: Cohere model to use (e.g., "command", "command-light").

    Returns:
        The summary text, or None if an error occurs.
    """
    if not api_key:
        logger.error("Cohere API key not provided for summarization.")
        return None
    if not text_to_summarize:
        return ""


    url = "https://api.cohere.ai/v1/summarize"
    payload = {
        "text": text_to_summarize,
        "length": length,
        "format": "paragraph",
        "model": model,
        "extractiveness": "auto",
        "temperature": 0.3,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        if "summary" in result:
            return result["summary"]
        else:
            logger.error(f"Cohere Summarize API did not return a summary: {result.get('message', result)}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error in Cohere summarization: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Cohere summarization: {e}")
        return None

def extract_keywords_cohere(
    text_to_extract_from: str,
    api_key: str,
    num_keywords: int = 5,
    model: str = "command"
) -> Optional[List[str]]:
    """
    Extracts keywords using Cohere Generate API.

    Args:
        text_to_extract_from: The text to extract keywords from.
        api_key: Cohere API key.
        num_keywords: Desired number of keywords.
        model: Cohere model to use for generation.

    Returns:
        A list of keywords, or None if an error occurs.
    """
    if not api_key:
        logger.error("Cohere API key not provided for keyword extraction.")
        return None
    if not text_to_extract_from:
        return []

    prompt = f"""Extract the {num_keywords} most relevant keywords or key phrases from the following text.
Return the keywords as a comma-separated list. Do not add any introductory text, numbering, or explanations.

Text:
"{text_to_extract_from}"

Keywords:"""

    url = "https://api.cohere.ai/v1/generate"
    payload = {
        "prompt": prompt,
        "model": model,
        "max_tokens": num_keywords * 15, # Allow more tokens for longer keywords and separators
        "temperature": 0.2,
        "k": 0,
        "p": 0.75,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1,
        "stop_sequences": ["\n"],
        "return_likelihoods": "NONE"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        if result.get("generations") and result["generations"][0].get("text"):
            generated_text = result["generations"][0]["text"].strip()
            if generated_text.lower().startswith("keywords:"): # Remove potential prefix
                generated_text = generated_text[len("keywords:"):].strip()

            keywords = [kw.strip().rstrip('.').strip() for kw in generated_text.split(',') if kw.strip()]
            return [kw for kw in keywords if kw][:num_keywords] # Filter empty and limit
        else:
            logger.error(f"Cohere Generate API (keywords) did not return expected result: {result.get('message', result)}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error in Cohere keyword extraction: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Cohere keyword extraction: {e}")
        return None

def generate_response_cohere(
    chat_history: List[Dict[str, str]],
    new_message: str,
    api_key: str,
    model: str = "command-r", # command-r is good for chat
    system_message: Optional[str] = None,
    connectors: Optional[List[Dict[str, str]]] = None # e.g., [{"id": "web-search"}]
) -> Optional[str]:
    """
    Generates a response using Cohere Chat API.

    Args:
        chat_history: List of previous messages. Roles should be "USER", "CHATBOT", "SYSTEM", "TOOL".
        new_message: The new user message.
        api_key: Cohere API key.
        model: Cohere model to use.
        system_message: An initial system message (preamble).
        connectors: List of connectors to use (e.g., for web search).

    Returns:
        The generated response text, or None if an error occurs.
    """
    if not api_key:
        logger.error("Cohere API key not provided for response generation.")
        return None

    url = "https://api.cohere.ai/v1/chat"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Cohere expects specific roles: USER, CHATBOT, SYSTEM, TOOL
    cohere_chat_hist = []
    for msg in chat_history:
        role = msg.get("role", "USER").upper()
        if role not in ["USER", "CHATBOT", "SYSTEM", "TOOL"]:
            role = "USER" # Default unknown roles to USER
        cohere_chat_hist.append({"role": role, "message": msg.get("message", "")})

    data = {
        "chat_history": cohere_chat_hist,
        "message": new_message,
        "model": model,
    }
    if system_message: # Cohere's preamble is similar to a system message
        data["preamble"] = system_message
    if connectors:
        data["connectors"] = connectors

    try:
        response = requests.post(url, headers=headers, json=data, timeout=45)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get('text'):
            return response_data['text']
        # Check for tool calls if that's expected, or other response types
        elif response_data.get('tool_calls'):
            logger.info(f"Cohere API returned tool calls: {response_data['tool_calls']}")
            # This function is designed to return text; handling tool calls is outside its scope.
            return f"Tool call requested: {response_data['tool_calls'][0]['name'] if response_data['tool_calls'] else 'Unknown'}"
        else:
            logger.error(f"Cohere Chat API did not return text or expected structure: {response_data}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error in Cohere response generation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Cohere response generation: {e}")
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    google_api_key_env = os.getenv("GOOGLE_API_KEY")
    cohere_api_key_env = os.getenv("COHERE_API_KEY")

    sample_history = [
        {"role": "USER", "message": "こんにちは！今日の天気はどうですか？"},
        {"role": "CHATBOT", "message": "こんにちは！どちらの地域の天気が知りたいですか？"},
        {"role": "USER", "message": "東京です。"},
    ]
    new_user_message = "詳しく教えてください。"
    long_text_for_summary = """
    大規模言語モデル（LLM）は、AI研究の最前線に位置し、自然言語理解と生成において驚異的な能力を示しています。
    これらのモデルは、翻訳、要約、質問応答、さらには創造的な文章作成まで、多岐にわたるタスクをこなすことができます。
    GPTシリーズやPaLM、LLaMAなどがその代表例です。LLMの訓練には、ウェブ上の膨大なテキストデータが利用され、
    自己教師あり学習の手法が中心となります。このため、モデルは言語の複雑なパターンやニュアンスを捉えることが可能です。
    しかし、その強力さゆえに、誤情報拡散のリスクやバイアスの問題、計算資源の消費といった課題も抱えています。
    今後の研究では、これらの課題を克服し、より安全で効率的、かつ公平なLLMの開発が求められています。
    """

    if google_api_key_env:
        print("\\n--- Testing Google Gemini Functions ---")
        summary_google = summarize_chat_history_google(sample_history, google_api_key_env)
        print(f"Google - Chat Summary: {summary_google}")

        response_google = generate_response_google(sample_history, new_user_message, google_api_key_env, system_instruction="あなたは親切なアシスタントです。")
        print(f"Google - Generated Response: {response_google}")
    else:
        print("\\nSkipping Google Gemini tests: GOOGLE_API_KEY not set.")

    if cohere_api_key_env:
        print("\\n--- Testing Cohere Functions ---")
        summary_cohere = generate_summary_cohere(long_text_for_summary, cohere_api_key_env, length="short")
        print(f"Cohere - Text Summary (short): {summary_cohere}")

        keywords_cohere = extract_keywords_cohere(long_text_for_summary, cohere_api_key_env, num_keywords=3)
        print(f"Cohere - Extracted Keywords: {keywords_cohere}")

        response_cohere = generate_response_cohere(
            sample_history,
            new_user_message,
            cohere_api_key_env,
            system_message="You are a helpful AI assistant focusing on providing concise information."
            # connectors=[{"id": "web-search"}] # Uncomment to test web search
        )
        print(f"Cohere - Generated Response: {response_cohere}")
    else:
        print("\\nSkipping Cohere tests: COHERE_API_KEY not set.")

    print("\\nLLM Integration tests finished.")
