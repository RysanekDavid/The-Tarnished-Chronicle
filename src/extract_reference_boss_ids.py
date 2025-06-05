import os
import re
import json

def extract_boss_defeat_flags(file_path: str) -> list[dict]:
    """
    Extracts boss defeat event flag IDs and Japanese names from the markdown reference file.

    Args:
        file_path: Path to the index.md or combined EFID file.

    Returns:
        A list of dictionaries, each containing 'event_id' and 'japanese_name'.
    """
    boss_flags = []
    # Regex to capture the ID and the Japanese name after "ボス撃破 "
    # It looks for a markdown table row: | ID | FN | UT | PC | ボス撃破 Name |
    # We need to be careful with spaces and potential variations.
    # Example line: | 61100 | 1 | 1 | 0 | ボス撃破 忌み鬼マルギット |
    # The ID is the first numerical group. The name is after "ボス撃破 ".
    regex = re.compile(r"\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*ボス撃破\s*([^\|]+?)\s*\|")

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return boss_flags

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                match = regex.search(line)
                if match:
                    event_id_str = match.group(1).strip()
                    japanese_name = match.group(2).strip()
                    try:
                        event_id = int(event_id_str)
                        boss_flags.append({
                            "event_id": event_id,
                            "japanese_name": japanese_name
                        })
                    except ValueError:
                        print(f"Warning: Could not parse event_id '{event_id_str}' from line {line_num}: {line.strip()}")
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    return boss_flags

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    index_md_path = os.path.join(project_root, "data", "Bosses", "index.md")

    print(f"Attempting to extract boss defeat flags from: {index_md_path}")
    extracted_boss_ids = extract_boss_defeat_flags(index_md_path)

    if extracted_boss_ids:
        print(f"Successfully extracted {len(extracted_boss_ids)} boss defeat flag entries.")
        print("Sample entries (first 10):")
        for i, entry in enumerate(extracted_boss_ids[:10]):
            print(json.dumps(entry, ensure_ascii=False, indent=2))
        
        output_json_path = os.path.join(project_root, "data", "Bosses", "reference_boss_ids.json")
        try:
            with open(output_json_path, 'w', encoding='utf-8') as outfile:
                json.dump(extracted_boss_ids, outfile, ensure_ascii=False, indent=4)
            print(f"Extracted boss IDs saved to: {output_json_path}")
        except IOError as e:
            print(f"Error writing JSON file {output_json_path}: {e}")
    else:
        print("No boss defeat flags found or an error occurred during extraction.")