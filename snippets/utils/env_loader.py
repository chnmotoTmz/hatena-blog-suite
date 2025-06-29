import os
from dotenv import load_dotenv

def load_env(env_path: str = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Optional path to the .env file.
                  If None, it will search for a .env file in the current directory
                  or parent directories.

    Returns:
        True if .env file was loaded successfully, False otherwise.
    """
    try:
        if env_path:
            if not os.path.exists(env_path):
                print(f"Warning: Specified .env file not found at {env_path}")
                return False
            loaded = load_dotenv(dotenv_path=env_path, verbose=True)
        else:
            # Searches for .env in current and parent dirs
            loaded = load_dotenv(verbose=True)

        if loaded:
            print(f".env file loaded successfully (path used: {env_path if env_path else 'auto-detected'}).")
        else:
            print("No .env file found or .env file is empty.")
        return loaded
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return False

if __name__ == '__main__':
    # Create a dummy .env file for testing
    dummy_env_content = """
# Test .env file
API_KEY="test_api_key_12345"
SECRET_KEY="a_super_secret_key"
APP_NAME="My Snippet App"
DEBUG_MODE=True
PORT=8080
    """
    dummy_env_path = ".env.test_dummy"
    specific_env_path = "specific.env"

    with open(dummy_env_path, "w") as f:
        f.write(dummy_env_content)

    with open(specific_env_path, "w") as f:
        f.write("SPECIFIC_VAR='This is from specific.env'")

    print("--- Testing auto-detection (using .env.test_dummy as .env) ---")
    # For auto-detection test, temporarily rename dummy to .env
    original_env_exists = os.path.exists(".env")
    original_env_content = None
    if original_env_exists:
        with open(".env", "r") as f_orig:
            original_env_content = f_orig.read()
        os.remove(".env")

    os.rename(dummy_env_path, ".env")
    load_env()
    print(f"API_KEY from env: {os.getenv('API_KEY')}")
    print(f"DEBUG_MODE from env: {os.getenv('DEBUG_MODE')}")

    # Restore original .env if it existed, otherwise clean up
    os.remove(".env")
    if original_env_exists and original_env_content:
        with open(".env", "w") as f_orig_restore:
            f_orig_restore.write(original_env_content)

    print("\\n--- Testing with specific path ---")
    load_env(env_path=specific_env_path)
    print(f"SPECIFIC_VAR from env: {os.getenv('SPECIFIC_VAR')}")
    # Clean up specific .env
    if os.path.exists(specific_env_path):
        os.remove(specific_env_path)

    print("\\n--- Testing with non-existent specific path ---")
    load_env(env_path="non_existent.env")

    print("\\n--- Testing without any .env file (after cleanup) ---")
    # Ensure no .env file exists for this test
    if os.path.exists(".env"): os.remove(".env")
    if os.path.exists(dummy_env_path): os.remove(dummy_env_path) # Should be removed by rename already

    load_env()
    print(f"API_KEY (should be None if .env not found): {os.getenv('API_KEY')}")

    # Final cleanup of any test .env files
    if os.path.exists(dummy_env_path):
        os.remove(dummy_env_path)
    if os.path.exists(specific_env_path):
        os.remove(specific_env_path)
    if os.path.exists(".env"): # If one was created unexpectedly
        os.remove(".env")
    print("\\nEnvironment loading tests finished.")
