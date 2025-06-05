import json
import hashlib # Still used for debug prints, can be removed if not needed
import argparse
import subprocess
import os
# tempfile is no longer needed as er-save-utils is not used directly for dumping full JSON

# Constants for Rust CLI path will be handled by argparse and default logic
# RUST_LIB_FLAG_DIVISOR and RUST_LIB_BLOCK_SIZE_BYTES are no longer needed

def load_boss_data(json_filepath):
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"CHYBA: Soubor s daty bossů '{json_filepath}' nebyl nalezen.")
        return None
    except json.JSONDecodeError as e:
        print(f"CHYBA: Chyba při parsování JSON souboru s daty bossů '{json_filepath}': {e}")
        return None

# Functions load_event_flag_map_from_bst, get_event_flag_byte_offset_and_bit,
# check_boss_status_from_data_block, and the old get_event_flags_from_er_save_utils
# ARE NO LONGER NEEDED as the Rust CLI handles event flag checking.

def get_boss_statuses_from_rust_cli(sl2_filepath, character_slot_index, all_event_ids_to_check, rust_cli_executable_path):
    """
    Spustí tvůj Rust CLI nástroj s jedním velkým seznamem event ID a vrátí slovník {event_id_str: bool}.
    """
    if not all_event_ids_to_check:
        print("DEBUG: Nebyla poskytnuta žádná event ID ke kontrole pro Rust CLI.")
        return {}

    # Ensure all event IDs are strings for joining and for matching keys from JSON
    event_ids_str_list = [str(eid) for eid in all_event_ids_to_check]
    
    try:
        command = [
            rust_cli_executable_path,
            "--slot-index", str(character_slot_index),
            "--event-ids", ",".join(event_ids_str_list), # IDs separated by comma
            sl2_filepath
        ]
        print(f"Spouštím Rust CLI: {' '.join(command)}")
        
        process = subprocess.run(
            command,
            capture_output=True, text=True, check=False, encoding='utf-8' # check=False for custom error handling
        )

        if process.returncode != 0:
            print(f"CHYBA: Tvůj Rust CLI nástroj ({rust_cli_executable_path}) selhal s kódem {process.returncode}.")
            print(f"Stdout: {process.stdout}")
            print(f"Stderr: {process.stderr}")
            return None 

        # Check if stdout is empty before trying to parse JSON
        if not process.stdout.strip():
            print(f"CHYBA: Rust CLI nástroj ({rust_cli_executable_path}) nevrátil žádný výstup na stdout.")
            print(f"Stderr: {process.stderr}")
            return None

        try:
            # Output is a JSON object mapping event_id (string) to bool
            statuses = json.loads(process.stdout)
            # The keys in `statuses` will be strings, which is fine for direct lookup.
            return statuses 
        except json.JSONDecodeError as e:
            print(f"CHYBA: Nepodařilo se dekódovat JSON výstup z tvého Rust CLI nástroje: {e}")
            print(f"Raw stdout: '{process.stdout}'")
            return None

    except FileNotFoundError:
        print(f"CHYBA: Spustitelný soubor tvého Rust CLI ({rust_cli_executable_path}) nebyl nalezen.")
        print("Ujisti se, že je správně zkompilován a cesta k němu je správná.")
        return None
    except subprocess.TimeoutExpired:
        print(f"CHYBA: Vypršel časový limit při čekání na dokončení Rust CLI ({rust_cli_executable_path}).")
        return None
    except Exception as e:
        print(f"Neočekávaná chyba při volání tvého Rust CLI: {e}")
        return None

# --- Hlavní logika v Pythonu ---
def main():
    parser = argparse.ArgumentParser(description="Analyzuje Elden Ring SL2 save soubor pro statusy bossů pomocí vlastního Rust CLI.")
    parser.add_argument("--sl2_file", type=str, default="SavesTest/ER0000.sl2", help="Cesta k SL2 save souboru")
    parser.add_argument("--slot_index", type=int, default=0, help="Index slotu postavy (0-9)")
    parser.add_argument("--boss_data_json", type=str, default="data/Bosses/reference_boss_ids.json", help="Cesta k JSON souboru s daty bossů")
    parser.add_argument("--rust_cli_path", type=str, default="RUST_CLI_TOOL_PATH_PLACEHOLDER", help="Cesta ke spustitelnému souboru tvého Rust CLI (flag_extractor_cli)")
    
    args = parser.parse_args()

    rust_cli_actual_path = args.rust_cli_path
    if rust_cli_actual_path == "RUST_CLI_TOOL_PATH_PLACEHOLDER":
        # Attempt to find it relative to this script's location (assuming script is in src/)
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir) 
            default_path = os.path.join(project_root, "flag_extractor_cli", "target", "release", "flag_extractor_cli")
            if os.name == 'nt':
                default_path += ".exe"
            
            if os.path.exists(default_path):
                rust_cli_actual_path = default_path
                print(f"Automaticky nastavena cesta k Rust CLI: {rust_cli_actual_path}")
            else:
                print(f"CHYBA: Placeholder pro Rust CLI cestu byl použit, ale výchozí cesta nebyla nalezena: {default_path}")
                print("Prosím, zadej správnou cestu pomocí --rust_cli_path nebo umísti zkompilovaný nástroj na očekávané místo.")
                return
        except Exception as e:
            print(f"CHYBA: Nepodařilo se automaticky určit cestu k Rust CLI: {e}")
            print("Prosím, zadej správnou cestu pomocí --rust_cli_path.")
            return


    all_bosses_data_from_json = load_boss_data(args.boss_data_json)
    if all_bosses_data_from_json is None:
        return # Error message already printed by load_boss_data
    
    bosses_to_check = []
    if isinstance(all_bosses_data_from_json, dict):
        bosses_to_check.extend(all_bosses_data_from_json.get("base_game_bosses", []))
        bosses_to_check.extend(all_bosses_data_from_json.get("dlc_shadow_of_the_erdtree_bosses", []))
    elif isinstance(all_bosses_data_from_json, list):
        bosses_to_check = all_bosses_data_from_json
    else:
        print(f"CHYBA: Neočekávaný formát hlavního JSON souboru s bossy: {type(all_bosses_data_from_json)}. Očekáván dict nebo list.")
        return

    if not bosses_to_check:
        print("INFO: V souboru s daty bossů nebyly nalezeny žádné záznamy bossů ke kontrole.")
        return

    # Shromáždi všechna unikátní event ID ke kontrole
    unique_event_ids_to_query = set()
    for boss_original in bosses_to_check:
        event_id_value = boss_original.get("event_id")
        if event_id_value is None: 
            # print(f"DEBUG: Boss '{boss_original.get('name', 'Neznámý')}' nemá event_id.")
            continue

        ids_for_this_boss = []
        if isinstance(event_id_value, list):
            ids_for_this_boss = event_id_value
        else: # Předpoklad, že je to jedno ID (string nebo int)
            ids_for_this_boss.append(event_id_value)
        
        for id_val in ids_for_this_boss:
            try:
                unique_event_ids_to_query.add(int(str(id_val))) # Normalizuj na int
            except ValueError:
                print(f"VAROVÁNÍ: Nevalidní formát event_id '{id_val}' pro bosse '{boss_original.get('name', 'Neznámý')}' - bude ignorováno.")
                pass 

    if not unique_event_ids_to_query:
        print("Nenašly se žádné validní event ID ke kontrole v datech bossů.")
        # Create an empty JSON if no bosses or no valid IDs
        processed_bosses_data = []
        defeated_boss_count = 0
        # Fall through to print/save logic to make it consistent
    else:
        # Zavolej Rust CLI jednou se všemi unikátními ID
        print(f"DEBUG: Dotazuji se na statusy pro {len(unique_event_ids_to_query)} unikátních event ID.")
        event_id_statuses = get_boss_statuses_from_rust_cli(
            args.sl2_file, 
            args.slot_index, 
            list(unique_event_ids_to_query), 
            rust_cli_actual_path
        )

        if event_id_statuses is None:
            print("Nepodařilo se získat statusy event flagů z Rust CLI. Zpracování bossů neproběhne.")
            return

        print(f"DEBUG: Získané statusy z Rust CLI: {event_id_statuses}")

        defeated_boss_count = 0
        processed_bosses_data = []

        for boss_original in bosses_to_check:
            boss = boss_original.copy() # Pracuj s kopií
            event_id_value = boss.get("event_id")
            boss_name = boss.get('name', f'Neznámý boss s event_id {event_id_value}')

            if event_id_value is None: 
                boss["is_defeated"] = False # Default if no event_id
                processed_bosses_data.append(boss)
                continue

            current_boss_event_ids_as_str = []
            original_event_ids_for_output = [] # Pro zachování původního formátu (int nebo list intů)

            if isinstance(event_id_value, list):
                for id_val in event_id_value:
                    try:
                        current_boss_event_ids_as_str.append(str(int(id_val)))
                        original_event_ids_for_output.append(int(id_val))
                    except ValueError:
                        # Pokud je v listu nevalidní ID, ponecháme ho jako string pro výstup, ale Rust CLI ho ignoruje
                        current_boss_event_ids_as_str.append(str(id_val)) 
                        original_event_ids_for_output.append(str(id_val))
            else:
                try:
                    current_boss_event_ids_as_str.append(str(int(event_id_value)))
                    original_event_ids_for_output.append(int(event_id_value))
                except ValueError:
                    current_boss_event_ids_as_str.append(str(event_id_value))
                    original_event_ids_for_output.append(str(event_id_value))
            
            is_defeated = False
            found_valid_id_for_boss = False
            for eid_str in current_boss_event_ids_as_str:
                # event_id_statuses má klíče jako stringy
                status = event_id_statuses.get(eid_str)
                if status is not None: # Klíč existuje v odpovědi z CLI
                    found_valid_id_for_boss = True
                    if status is True:
                        is_defeated = True
                        break # Stačí jeden flag pro potvrzení, že boss je poražen
            
            boss["is_defeated"] = is_defeated
            
            # Obnovení event_id do původního formátu (int nebo list intů) pro výstupní JSON
            if len(original_event_ids_for_output) == 1 and not isinstance(event_id_value, list):
                boss["event_id"] = original_event_ids_for_output[0]
            else:
                boss["event_id"] = original_event_ids_for_output
            
            processed_bosses_data.append(boss)
            
            if is_defeated:
                defeated_boss_count += 1
                print(f"Boss Defeated: {boss_name} (Relevantní ID: {current_boss_event_ids_as_str}) JE PORAŽEN.")
            else:
                if not found_valid_id_for_boss and current_boss_event_ids_as_str:
                     print(f"Boss Not Defeated: {boss_name} (Relevantní ID: {current_boss_event_ids_as_str}) NENÍ poražen (žádné z ID nemělo platný status z CLI).")
                else:
                     print(f"Boss Not Defeated: {boss_name} (Relevantní ID: {current_boss_event_ids_as_str}) NENÍ poražen.")
                
    print(f"\nPočet bossů, pro které byl status úspěšně zjištěn: {len(processed_bosses_data)}")
    print(f"Celkový počet detekovaných poražených bossů (z těch výše): {defeated_boss_count}")

    if processed_bosses_data or not unique_event_ids_to_query : # Ulož i prázdný výsledek, pokud nebyly ID
        output_filename = "data/Bosses/reference_boss_ids_processed_via_er_save_lib_cli.json"
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_bosses_data, f, ensure_ascii=False, indent=4)
            print(f"Zpracovaný seznam bossů uložen do: {output_filename}")
        except IOError as e:
            print(f"Chyba při ukládání zpracovaného JSON souboru {output_filename}: {e}")
        except Exception as e:
            print(f"Neočekávaná chyba při ukládání výstupního JSON souboru: {e}")


if __name__ == "__main__":
    main()