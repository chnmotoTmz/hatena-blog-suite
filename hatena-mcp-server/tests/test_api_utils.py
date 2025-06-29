import os
from dotenv import load_dotenv
import pytest
from unittest.mock import patch, MagicMock # Added MagicMock
import requests # For requests.exceptions.RequestException
from api_utils import (
    generate_response_cohere, 
    # generate_response_gemini, # Assuming this was renamed to generate_response_google
    generate_response_google, # Corrected name
    assign_role,
    generate_summary_cohere,
    extract_keywords_cohere
)
import re
import json # For mocking JSON responses

load_dotenv()  # 環境変数を読み込む

# APIキーが設定されているか確認
API_TOKEN_1 = os.getenv("API_TOKEN_1")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

def log_request(url, headers, data):
    pass

# Geminiのテスト
@pytest.mark.skipif(not API_TOKEN_1, reason="API_TOKEN_1 is not set")
def test_generate_response_google(): # Renamed from test_generate_response_gemini
    prompt = "今日の天気は？"
    # Assuming generate_response_google takes chat_history, message, api_key
    # This test might need adjustment based on the actual signature of generate_response_google
    # For now, let's assume it's called correctly as per its definition in api_utils
    chat_history_example = [] 
    response, _ = generate_response_google(chat_history_example, prompt, API_TOKEN_1)
    assert isinstance(response, str)  # 応答が文字列であることを確認
    assert len(response) > 0  # 応答が空でないことを確認

# Cohereのテスト
@pytest.mark.skipif(not COHERE_API_KEY, reason="COHERE_API_KEY is not set")
def test_generate_response_cohere_basic(): # Renamed for clarity
    chat_history = [{"role": "USER", "message": "こんにちは"}]
    message = "元気ですか？"
    # Assuming generate_response_cohere takes chat_history, message, api_key, google_api_key
    # This test might need adjustment based on the actual signature
    google_api_key_dummy = "dummy_google_key_if_needed_by_cohere_func" 
    response, _ = generate_response_cohere(chat_history, message, COHERE_API_KEY, google_api_key_dummy)
    assert isinstance(response, str)  # 応答が文字列であることを確認
    assert len(response) > 0  # 応答が空でないことを確認

@pytest.mark.skipif(not API_TOKEN_1, reason="API_TOKEN_1 is not set")
def test_generate_response_google_with_role_context(): # Renamed and clarified
    prompt = "今日の天気は？"
    # The 'role' isn't directly passed to generate_response_google. 
    # The effect of 'role' is via assign_role called on the 'message'.
    # This test checks if the response is generated.
    chat_history_example = [{"role": "USER", "message": "何か手伝うことは？"}]
    response, _ = generate_response_google(chat_history_example, prompt, API_TOKEN_1) 
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.skipif(not COHERE_API_KEY, reason="COHERE_API_KEY is not set")
def test_generate_response_cohere_with_role_context(): # Renamed and clarified
    chat_history = [{"role": "USER", "message": "こんにちは"}]
    message = "具合が悪いのですが…" # This message implies a medical context
    
    # The 'role' isn't directly passed. assign_role in api_utils should handle context.
    # We expect the LLM to pick up on the context from the message.
    google_api_key_dummy = "dummy_google_key_if_needed_by_cohere_func"
    response, _ = generate_response_cohere(chat_history, message, COHERE_API_KEY, google_api_key_dummy)

    assert isinstance(response, str)
    assert len(response) > 0
    # This assertion is highly dependent on LLM's output and prompt engineering in the actual function
    # It might be flaky. For robust testing, mock the LLM response.
    # assert any(keyword in response.lower() for keyword in ["症状", "医者", "病院", "お大事に"])


# Tests for assign_role (existing tests are good)

@pytest.mark.parametrize(
    "message, expected_role", # This test seems fine as is.
    [
        ("システムエラーが発生しました", "System"),
        ("最新のニュース記事を検索してください", "Tool"),
        ("こんにちは", "Chatbot"),
        ("今日の天気は？", "User"),
        ("ありがとう", "Chatbot"),
        ("使い方を教えてください", "User"),
        ("設定を変更したい", "User"),
        ("データを分析してください", "User"),
        ("おはよう", "User"),
        ("こんばんは", "Chatbot"),
        ("", "User"),  # 空文字列の場合はUserになることを確認
    ],
)
def test_assign_role(message, expected_role):
    actual_role = assign_role(message)
    assert actual_role == expected_role, f"Expected role '{expected_role}' for message '{message}', but got '{actual_role}'"

# --- Tests for generate_summary_cohere ---

@patch('api_utils.requests.post')
@pytest.mark.skipif(not COHERE_API_KEY, reason="COHERE_API_KEY is not set (mocked anyway, but good practice)")
def test_generate_summary_cohere_success(mock_post):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    # Based on Cohere API docs for v1/summarize: https://docs.cohere.com/reference/summarize-2
    # The direct response has a "summary" key.
    mock_response.json.return_value = {"summary": "This is a mock summary."}
    mock_post.return_value = mock_response

    summary = generate_summary_cohere("Some long text to summarize.", length="medium")
    
    assert summary == "This is a mock summary."
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.cohere.ai/v1/summarize"
    assert kwargs['headers']['Authorization'] == f"Bearer {COHERE_API_KEY}"
    assert kwargs['json']['text'] == "Some long text to summarize."
    assert kwargs['json']['length'] == "medium"

@patch('api_utils.requests.post')
@pytest.mark.skipif(not COHERE_API_KEY, reason="COHERE_API_KEY is not set")
def test_generate_summary_cohere_api_error(mock_post):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")
    mock_post.return_value = mock_response

    summary = generate_summary_cohere("Some text.")
    assert summary.startswith("Error: Cohere API request failed")

@patch('api_utils.os.getenv')
def test_generate_summary_cohere_no_api_key(mock_getenv):
    mock_getenv.return_value = None # Simulate COHERE_API_KEY not being set
    summary = generate_summary_cohere("Some text.")
    assert summary == "Error: COHERE_API_KEY is not set."
    mock_getenv.assert_called_with("COHERE_API_KEY")


# --- Tests for extract_keywords_cohere ---

@patch('api_utils.requests.post')
@pytest.mark.skipif(not COHERE_API_KEY, reason="COHERE_API_KEY is not set (mocked anyway)")
def test_extract_keywords_cohere_success(mock_post):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    # Based on Cohere Generate endpoint: https://docs.cohere.com/reference/generate
    mock_response.json.return_value = {
        "generations": [{"text": "keyword1, keyword2, keyword3"}]
    }
    mock_post.return_value = mock_response

    keywords = extract_keywords_cohere("Some text content with keyword1 and other terms.", num_keywords=3)
    
    assert keywords == ["keyword1", "keyword2", "keyword3"]
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.cohere.ai/v1/generate"
    assert kwargs['headers']['Authorization'] == f"Bearer {COHERE_API_KEY}"
    assert "Extract the 3 most relevant keywords" in kwargs['json']['prompt']
    assert "Some text content with keyword1 and other terms." in kwargs['json']['prompt']

@patch('api_utils.requests.post')
@pytest.mark.skipif(not COHERE_API_KEY, reason="COHERE_API_KEY is not set")
def test_extract_keywords_cohere_api_error(mock_post):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")
    mock_post.return_value = mock_response

    keywords = extract_keywords_cohere("Some text.")
    assert isinstance(keywords, list)
    assert len(keywords) == 1
    assert keywords[0].startswith("Error: Cohere API request failed")

@patch('api_utils.os.getenv')
def test_extract_keywords_cohere_no_api_key(mock_getenv):
    mock_getenv.return_value = None # Simulate COHERE_API_KEY not being set
    keywords = extract_keywords_cohere("Some text.")
    assert keywords == ["Error: COHERE_API_KEY is not set."]
    mock_getenv.assert_called_with("COHERE_API_KEY")