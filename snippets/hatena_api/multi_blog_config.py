import os
from typing import Dict, List, Optional, NamedTuple
from dotenv import load_dotenv

class BlogConfiguration(NamedTuple):
    """Represents configuration for a single Hatena blog."""
    name: str
    hatena_id: str
    blog_domain: str
    api_key: str
    description: Optional[str] = ""

class MultiBlogConfigManager:
    """
    Manages configurations for multiple Hatena blogs, loaded from environment variables.
    """
    def __init__(self, auto_load_dotenv: bool = True):
        """
        Initializes the manager.

        Args:
            auto_load_dotenv: If True, automatically tries to load a .env file.
        """
        if auto_load_dotenv:
            load_dotenv(verbose=True) # Loads .env from current dir or parent dirs

        self.blogs: Dict[str, BlogConfiguration] = {}
        self._load_configs_from_env()

    def _load_configs_from_env(self):
        """
        Loads blog configurations from predefined environment variable patterns.

        It expects environment variables in a certain format, e.g.,
        BLOG_CONFIG_1_NAME="My Tech Blog"
        BLOG_CONFIG_1_HATENA_ID="user1"
        BLOG_CONFIG_1_DOMAIN="user1.hatenablog.com"
        BLOG_CONFIG_1_API_KEY_ENV="MY_TECH_BLOG_API_KEY"
        # (where MY_TECH_BLOG_API_KEY itself is an env var holding the actual key)
        BLOG_CONFIG_1_DESCRIPTION="My thoughts on tech."

        BLOG_CONFIG_2_NAME="..."
        ...
        """
        i = 1
        while True:
            name_var = f"BLOG_CONFIG_{i}_NAME"
            hatena_id_var = f"BLOG_CONFIG_{i}_HATENA_ID"
            domain_var = f"BLOG_CONFIG_{i}_DOMAIN"
            api_key_env_var_name_var = f"BLOG_CONFIG_{i}_API_KEY_ENV" # Name of the env var that holds the API key
            description_var = f"BLOG_CONFIG_{i}_DESCRIPTION"

            name = os.getenv(name_var)
            hatena_id = os.getenv(hatena_id_var)
            blog_domain = os.getenv(domain_var)
            api_key_env_var_name = os.getenv(api_key_env_var_name_var)

            if not all([name, hatena_id, blog_domain, api_key_env_var_name]):
                if i == 1 and not any([name, hatena_id, blog_domain, api_key_env_var_name]):
                    print("No blog configurations found with BLOG_CONFIG_n_... pattern.")
                elif i > 1 : # Found some configs, but this one is missing parts
                    print(f"Stopping config search at index {i} due to missing required fields.")
                break # Stop if any required part of a config is missing

            actual_api_key = os.getenv(api_key_env_var_name)
            if not actual_api_key:
                print(f"Warning: API key environment variable '{api_key_env_var_name}' not set for blog '{name}'. Skipping this blog.")
                i += 1
                continue

            description = os.getenv(description_var, "")

            blog_config = BlogConfiguration(
                name=name,
                hatena_id=hatena_id,
                blog_domain=blog_domain,
                api_key=actual_api_key,
                description=description
            )

            if name in self.blogs:
                print(f"Warning: Duplicate blog name '{name}' found. Overwriting previous config.")
            self.blogs[name] = blog_config
            print(f"Loaded blog config: '{name}' (Hatena ID: {hatena_id}, Domain: {blog_domain})")

            i += 1

        if not self.blogs:
             print("No blog configurations were successfully loaded.")


    def get_blog_config(self, name: str) -> Optional[BlogConfiguration]:
        """
        Retrieves the configuration for a blog by its name.

        Args:
            name: The unique name of the blog configuration.

        Returns:
            A BlogConfiguration object if found, otherwise None.
        """
        return self.blogs.get(name)

    def list_blog_names(self) -> List[str]:
        """Returns a list of names of all loaded blog configurations."""
        return list(self.blogs.keys())

    def list_all_configs(self) -> List[BlogConfiguration]:
        """Returns a list of all loaded blog configurations."""
        return list(self.blogs.values())

if __name__ == '__main__':
    print("--- Testing MultiBlogConfigManager ---")

    # Create a dummy .env file for testing
    # This simulates the environment variables the manager expects
    dummy_env_content = """
# Blog 1 Configuration
BLOG_CONFIG_1_NAME="Tech Blog"
BLOG_CONFIG_1_HATENA_ID="techblogger"
BLOG_CONFIG_1_DOMAIN="tech.hatenablog.com"
BLOG_CONFIG_1_API_KEY_ENV="TECH_BLOG_API_KEY_ACTUAL" # This var stores the actual key
TECH_BLOG_API_KEY_ACTUAL="tech_api_key_123"
BLOG_CONFIG_1_DESCRIPTION="My primary technology blog."

# Blog 2 Configuration
BLOG_CONFIG_2_NAME="Lifestyle Blog"
BLOG_CONFIG_2_HATENA_ID="lifeblogger"
BLOG_CONFIG_2_DOMAIN="life.hatenadiary.jp"
BLOG_CONFIG_2_API_KEY_ENV="LIFESTYLE_BLOG_API_KEY_ACTUAL"
LIFESTYLE_BLOG_API_KEY_ACTUAL="life_api_key_456"
# No description for this one to test optional field

# Blog 3 Configuration (missing API key env var value)
BLOG_CONFIG_3_NAME="Travel Blog"
BLOG_CONFIG_3_HATENA_ID="traveler"
BLOG_CONFIG_3_DOMAIN="travel.hatenablog.com"
BLOG_CONFIG_3_API_KEY_ENV="TRAVEL_KEY_NOT_SET"
BLOG_CONFIG_3_DESCRIPTION="Adventures around the world."

# Blog 4 Configuration (API Key env var name not set)
BLOG_CONFIG_4_NAME="Food Blog"
BLOG_CONFIG_4_HATENA_ID="foodie"
BLOG_CONFIG_4_DOMAIN="food.hatenablog.com"
# BLOG_CONFIG_4_API_KEY_ENV missing
FOOD_BLOG_API_KEY_ACTUAL="food_api_789"
"""
    test_env_path = ".env.multiblogtest"
    with open(test_env_path, "w") as f:
        f.write(dummy_env_content)

    # Load this specific .env file for the test
    load_dotenv(dotenv_path=test_env_path, override=True, verbose=True)

    manager = MultiBlogConfigManager(auto_load_dotenv=False) # Env already loaded for test

    print("\\n--- Loaded Blog Configurations ---")
    all_configs = manager.list_all_configs()
    if all_configs:
        for config in all_configs:
            print(f"Name: {config.name}, ID: {config.hatena_id}, Domain: {config.blog_domain}, "
                  f"API Key: {'*' * len(config.api_key) if config.api_key else 'N/A'}, "
                  f"Desc: {config.description if config.description else 'N/A'}")
    else:
        print("No configurations were loaded.")

    print("\\n--- Get Specific Blog Config ---")
    tech_blog_config = manager.get_blog_config("Tech Blog")
    if tech_blog_config:
        print(f"Tech Blog API Key: {'*' * len(tech_blog_config.api_key)}")
    else:
        print("Tech Blog config not found.")

    travel_blog_config = manager.get_blog_config("Travel Blog")
    if travel_blog_config:
         print(f"Travel Blog config found (unexpected, API key was not set): {travel_blog_config.api_key}")
    else:
        print("Travel Blog config not found (as expected, API key was missing).")

    food_blog_config = manager.get_blog_config("Food Blog")
    if food_blog_config:
         print(f"Food Blog config found (unexpected, API_KEY_ENV was not set).")
    else:
        print("Food Blog config not found (as expected, API_KEY_ENV was missing).")


    print("\\n--- List Blog Names ---")
    blog_names = manager.list_blog_names()
    print(f"Available blog configurations: {blog_names}")

    assert "Tech Blog" in blog_names
    assert "Lifestyle Blog" in blog_names
    assert "Travel Blog" not in blog_names # Should be skipped
    assert "Food Blog" not in blog_names # Should be skipped


    # Clean up the dummy .env file
    if os.path.exists(test_env_path):
        os.remove(test_env_path)

    print("\\nMultiBlogConfigManager tests finished.")
