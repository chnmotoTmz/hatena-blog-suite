import json
import pickle
from typing import Any, Dict, List

def save_json(data: Any, filepath: str) -> None:
    """
    Save data to a JSON file.

    Args:
        data: The data to save (must be JSON serializable).
        filepath: The path to the JSON file.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved JSON data to {filepath}")
    except IOError as e:
        print(f"Error saving JSON to {filepath}: {e}")
    except TypeError as e:
        print(f"Error serializing data to JSON for {filepath}: {e}")

def load_json(filepath: str) -> Any:
    """
    Load data from a JSON file.

    Args:
        filepath: The path to the JSON file.

    Returns:
        The loaded data, or None if an error occurs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded JSON data from {filepath}")
        return data
    except FileNotFoundError:
        print(f"Error: JSON file not found at {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        return None
    except IOError as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return None

def save_pickle(data: Any, filepath: str) -> None:
    """
    Save data to a Pickle file.

    Args:
        data: The Python object to save.
        filepath: The path to the Pickle file.
    """
    try:
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Successfully saved Pickle data to {filepath}")
    except IOError as e:
        print(f"Error saving Pickle to {filepath}: {e}")
    except pickle.PicklingError as e:
        print(f"Error pickling data for {filepath}: {e}")


def load_pickle(filepath: str) -> Any:
    """
    Load data from a Pickle file.

    Args:
        filepath: The path to the Pickle file.

    Returns:
        The loaded Python object, or None if an error occurs.
    """
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        print(f"Successfully loaded Pickle data from {filepath}")
        return data
    except FileNotFoundError:
        print(f"Error: Pickle file not found at {filepath}")
        return None
    except pickle.UnpicklingError as e:
        print(f"Error unpickling data from {filepath}: {e}")
        return None
    except IOError as e:
        print(f"Error loading Pickle from {filepath}: {e}")
        return None

if __name__ == '__main__':
    # Example Usage
    test_data_dict = {"name": "Test Data", "version": 1.0, "items": [1, 2, 3]}
    test_data_list = [{"id": 1, "value": "A"}, {"id": 2, "value": "B"}]

    # JSON Test
    json_dict_filepath = "test_dict.json"
    json_list_filepath = "test_list.json"
    save_json(test_data_dict, json_dict_filepath)
    loaded_dict_data = load_json(json_dict_filepath)
    if loaded_dict_data:
        print(f"Loaded Dict from JSON: {loaded_dict_data}")

    save_json(test_data_list, json_list_filepath)
    loaded_list_data = load_json(json_list_filepath)
    if loaded_list_data:
        print(f"Loaded List from JSON: {loaded_list_data}")

    # Pickle Test
    pickle_filepath = "test_data.pkl"
    save_pickle(test_data_dict, pickle_filepath)
    loaded_pickle_data = load_pickle(pickle_filepath)
    if loaded_pickle_data:
        print(f"Loaded from Pickle: {loaded_pickle_data}")

    # Test error cases
    print("\\nTesting error cases:")
    load_json("non_existent.json")
    load_pickle("non_existent.pkl")
    # Create a malformed JSON file manually for testing json.JSONDecodeError
    with open("malformed.json", "w") as f:
        f.write("{'name': 'test',") # Malformed JSON
    load_json("malformed.json")
