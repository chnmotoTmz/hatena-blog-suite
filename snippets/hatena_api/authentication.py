import base64
import hashlib
import random
from datetime import datetime, timezone

def generate_wsse_header(username: str, api_key: str) -> str:
    """
    Generates a WSSE (Web Services Security Extensions) authentication header
    for Hatena Blog API.

    Args:
        username: Your Hatena ID.
        api_key: Your Hatena Blog API key (AtomPub key).

    Returns:
        A string formatted for the X-WSSE HTTP header.
    """
    if not username:
        raise ValueError("Username cannot be empty.")
    if not api_key:
        raise ValueError("API key cannot be empty.")

    # Generate a random nonce
    # Using os.urandom for cryptographically secure random bytes, then hex-encoding
    # nonce_bytes = os.urandom(16) # 16 bytes = 128 bits
    # nonce = nonce_bytes.hex()
    # For compatibility with original implementation, using hashlib.sha1(random.random())
    nonce_bytes = hashlib.sha1(str(random.random()).encode('utf-8')).digest()
    nonce_b64 = base64.b64encode(nonce_bytes).decode('utf-8')

    # Get current time in UTC, formatted as YYYY-MM-DDTHH:MM:SSZ
    created_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Create the password digest
    # sha1(nonce + created_time + api_key)
    # Ensure all parts are bytes before concatenation for hashing
    digest_input = nonce_bytes + created_time.encode('utf-8') + api_key.encode('utf-8')
    password_digest_bytes = hashlib.sha1(digest_input).digest()
    password_digest_b64 = base64.b64encode(password_digest_bytes).decode('utf-8')

    # Construct the WSSE header string
    wsse_header = (
        f'UsernameToken Username="{username}", '
        f'PasswordDigest="{password_digest_b64}", '
        f'Nonce="{nonce_b64}", '
        f'Created="{created_time}"'
    )

    return wsse_header

if __name__ == '__main__':
    # Example Usage (replace with your actual credentials for a real test)
    test_username = "testuser"
    test_api_key = "testapikey12345"

    print(f"--- Testing with dummy credentials ---")
    try:
        header1 = generate_wsse_header(test_username, test_api_key)
        print(f"Generated WSSE Header 1: {header1}")

        # Call again to ensure nonce and created time change
        header2 = generate_wsse_header(test_username, test_api_key)
        print(f"Generated WSSE Header 2: {header2}")

        if header1 == header2:
            print("Warning: Headers are identical. Nonce or timestamp might not be changing.")
        else:
            print("Headers are different, which is expected.")

    except ValueError as e:
        print(f"Error during header generation: {e}")

    print("\\n--- Testing with empty credentials (should raise ValueError) ---")
    try:
        generate_wsse_header("", test_api_key)
    except ValueError as e:
        print(f"Caught expected error for empty username: {e}")

    try:
        generate_wsse_header(test_username, "")
    except ValueError as e:
        print(f"Caught expected error for empty API key: {e}")

    print("\\nWSSE Authentication header generation tests finished.")
