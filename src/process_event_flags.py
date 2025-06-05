import os

def load_event_flag_map(file_path: str) -> dict[int, int]:
    """
    Loads the event flag map from the given file.

    The file is expected to be in the format: block_id,mapped_offset_value
    per line.

    Args:
        file_path: The path to the eventflag_bst.txt file.

    Returns:
        A dictionary mapping block_id (int) to mapped_offset_value (int).
    """
    event_flag_map: dict[int, int] = {}
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return event_flag_map

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',')
                if len(parts) == 2:
                    try:
                        block_id = int(parts[0])
                        mapped_offset_value = int(parts[1])
                        event_flag_map[block_id] = mapped_offset_value
                    except ValueError:
                        print(f"Warning: Could not parse line: {line}. Skipping.")
                else:
                    print(f"Warning: Malformed line: {line}. Skipping.")
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
    return event_flag_map

if __name__ == "__main__":
    # Construct the path relative to this script's location
    # Assuming eventflag_bst.txt is in ../data/EventFlags/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Assumes src is one level down from project root
    bst_file_path = os.path.join(project_root, "data", "EventFlags", "eventflag_bst.txt")

    print(f"Attempting to load event flag map from: {bst_file_path}")
    python_event_flag_map = load_event_flag_map(bst_file_path)

    if python_event_flag_map:
        print(f"Successfully loaded {len(python_event_flag_map)} entries into the event flag map.")
        print("Sample entries (first 5):")
        count = 0
        for key, value in python_event_flag_map.items():
            print(f"  {key}: {value}")
            count += 1
            if count >= 5:
                break
        # Example of accessing a known key if available, e.g., from your provided snippet
        if 1045540 in python_event_flag_map:
            print(f"Value for key 1045540: {python_event_flag_map[1045540]}")
        if 0 in python_event_flag_map:
            print(f"Value for key 0: {python_event_flag_map[0]}")
    else:
        print("Failed to load the event flag map or the map is empty.")