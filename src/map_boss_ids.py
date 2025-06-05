import os
import json
import re

def load_json_file(file_path: str) -> list | dict | None:
    """Loads data from a JSON file."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
    return None

def normalize_name(name: str) -> str:
    """Normalizes a name for basic matching (lowercase, remove some specifics)."""
    name = name.lower()
    name = re.sub(r'\(.*?\)', '', name) # Remove content in parentheses
    name = re.sub(r'[^\w\s]', '', name) # Remove punctuation
    name = name.strip()
    return name

def find_best_match(english_name: str, reference_bosses: list[dict], known_translations: dict) -> dict | None:
    """
    Attempts to find a match for an English boss name in the reference list.
    This is a placeholder for a more sophisticated matching or manual mapping.
    """
    normalized_english_name = normalize_name(english_name)

    # Check known translations first
    if normalized_english_name in known_translations:
        jp_name_target = known_translations[normalized_english_name]
        for ref_boss in reference_bosses:
            if ref_boss.get("japanese_name") == jp_name_target:
                return ref_boss
        # If direct match fails after translation, try normalized jp name
        normalized_jp_target = normalize_name(jp_name_target)
        for ref_boss in reference_bosses:
            if normalize_name(ref_boss.get("japanese_name","")) == normalized_jp_target:
                return ref_boss


    # Basic direct matching attempt (very naive for Japanese vs English)
    # This part is unlikely to yield good results without actual translation.
    # For now, it's a placeholder.
    # A more robust solution would involve a translation step or a pre-compiled mapping.
    
    # Example: If we had a way to translate english_name to a possible japanese_name
    # or if some reference names were already in English.
    # For now, this function will mostly rely on the known_translations.
    return None


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    processed_boss_data_path = os.path.join(project_root, "data", "Bosses", "bosses_extracted_details.json")
    reference_ids_path = os.path.join(project_root, "data", "Bosses", "reference_boss_ids.json")
    output_path = os.path.join(project_root, "data", "Bosses", "final_boss_data_preliminary.json")

    main_boss_data = load_json_file(processed_boss_data_path)
    reference_boss_ids = load_json_file(reference_ids_path)

    if not main_boss_data or not reference_boss_ids:
        print("Error: Could not load necessary data files. Exiting.")
    else:
        print(f"Loaded {len(main_boss_data)} bosses from processed data.")
        print(f"Loaded {len(reference_boss_ids)} reference IDs.")

        # Manual partial mapping based on common knowledge / previous translations
        # This would ideally be expanded or come from a dedicated translation file.
        known_translations_to_japanese = {
            normalize_name("Margit, the Fell Omen"): "忌み鬼マルギット",
            normalize_name("Godrick the Grafted"): "接ぎ木の王",
            normalize_name("Red Wolf of Radagon"): "ラダゴンの赤狼", # Assuming this is the one in EFID_common
            normalize_name("Rennala, Queen of the Full Moon"): "レナラ",
            normalize_name("Starscourge Radahn"): "ラダーン",
            normalize_name("Godfrey, First Elden Lord (Golden Shade)"): "ゴッドフレイ（ゴッドフレイ）", # Distinguish from real Godfrey
            normalize_name("Godfrey, First Elden Lord"): "ゴッドフレイ", # The real one
            normalize_name("Morgott, the Omen King"): "忌み鬼マルギット（本気）", # Morgott is "Margit (Full Power)"
            normalize_name("Sir Gideon Ofnir, the All-Knowing"): "百智卿",
            normalize_name("Maliketh, the Black Blade"): "マリケス",
            normalize_name("Hoarah Loux, Warrior"): "ゴッドフレイ", # Hoarah Loux is Godfrey's second phase
            normalize_name("Radagon of the Golden Order"): "ラスボス", # Placeholder, Radagon is part of the last boss entry
            normalize_name("Elden Beast"): "ラスボス", # Placeholder, Elden Beast is part of the last boss entry
            normalize_name("Ancestor Spirit"): "祖霊（弱）", # Assuming the weaker one
            normalize_name("Regal Ancestor Spirit"): "祖霊（強）",
            normalize_name("Mimic Tear"): "変身スライム",
            normalize_name("Valiant Gargoyle"): "同衾達", # This is Valiant Gargoyle Duo
            normalize_name("Astel, Naturalborn of the Void"): "アステール",
            normalize_name("Fire Giant"): "巨人",
            normalize_name("Godskin Duo"): "神肌タッグチーム",
            normalize_name("Dragonlord Placidusax"): "古龍",
            normalize_name("Malenia, Blade of Miquella"): "マレニア",
            normalize_name("Mohg, Lord of Blood"): "グールの王", # This is Mohg, Lord of Blood
            normalize_name("Mohg, the Omen"): "王都地下下水ボス", # This is Mohg, the Omen
            # Add more known mappings here
        }


        final_data = []
        unmatched_count = 0

        for boss in main_boss_data:
            english_name = boss.get("name", "")
            matched_ref = find_best_match(english_name, reference_boss_ids, known_translations_to_japanese)
            
            entry = boss.copy()
            if matched_ref:
                entry["reference_event_id"] = matched_ref.get("event_id")
                entry["japanese_reference_name"] = matched_ref.get("japanese_name")
            else:
                entry["reference_event_id"] = None
                entry["japanese_reference_name"] = None
                unmatched_count +=1
            final_data.append(entry)
        
        print(f"Processed {len(final_data)} bosses. {unmatched_count} bosses could not be automatically matched to a reference ID.")

        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                json.dump(final_data, outfile, ensure_ascii=False, indent=4)
            print(f"Preliminary mapped boss data saved to: {output_path}")
            print("Please review this file and manually correct/add 'reference_event_id' and 'japanese_reference_name' where needed.")
        except IOError as e:
            print(f"Error writing JSON file {output_path}: {e}")