import unittest
import sys
import os

# Add project root to sys.path to allow importing hatena_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adk import Agent
from hatena_agent import agent as hatena_blog_agent_instance # Import the specific agent instance
from hatena_agent import post_blog_entry, edit_blog_entry, get_blog_entries, enhance_article_content_operations
from unittest.mock import patch # Added for potential future mocking

class TestAgentStructure(unittest.TestCase):

    def test_hatena_blog_agent_initialization(self):
        """Tests the initialization and structure of HatenaBlogAgent."""
        self.assertIsNotNone(hatena_blog_agent_instance)
        self.assertIsInstance(hatena_blog_agent_instance, Agent)
        
        # Check for expected tool names
        expected_tool_names = [
            "post_blog_entry",
            "edit_blog_entry",
            "get_blog_entries",
            "enhance_article_content" # This is the name given in hatena_agent.py
        ]
        actual_tool_names = [tool.name for tool in hatena_blog_agent_instance.tools]
        
        for tool_name in expected_tool_names:
            self.assertIn(tool_name, actual_tool_names, f"Tool '{tool_name}' not found in agent.")

        # Optionally, check if the functions are correctly mapped (more involved)
        # For example, check one tool's function
        get_entries_tool = next((t for t in hatena_blog_agent_instance.tools if t.name == "get_blog_entries"), None)
        self.assertIsNotNone(get_entries_tool)
        self.assertEqual(get_entries_tool.func, get_blog_entries) # Check if the func attribute points to the correct function

    def test_agent_responds_to_query(self):
        """Tests if the agent provides a string response to a generic query."""
        # This is a very basic test. It doesn't check the content of the response,
        # only that the agent's run method executes and returns a string.
        # A more thorough test would involve mocking the LLM call and checking
        # for specific expected outputs based on the query and agent's system prompt.
        
        # For this test, we assume that even without specific tool invocation,
        # the agent's .run() method will produce some textual response (e.g., from the LLM).
        # We are not mocking any tools here, relying on the agent's default behavior
        # for non-tool-triggering inputs or its ability to say it can't do something.
        
        query = "Hello, how are you today?"
        try:
            result = hatena_blog_agent_instance.run(query)
            self.assertIsInstance(result, str, "Agent response should be a string.")
            # self.assertTrue(len(result) > 0, "Agent response should not be empty.") # Optional: check if it's non-empty
        except Exception as e:
            self.fail(f"Agent run failed with query '{query}': {e}")


if __name__ == '__main__':
    unittest.main()
