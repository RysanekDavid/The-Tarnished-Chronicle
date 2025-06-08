# src/rust_cli_handler.py
import os
import subprocess
import json

class RustCliHandler:
    def __init__(self, cli_path_placeholder="RUST_CLI_TOOL_PATH_PLACEHOLDER"):
        self.cli_path = self.detect_rust_cli_path(cli_path_placeholder)

    def detect_rust_cli_path(self, placeholder):
        path_to_check = placeholder
        if path_to_check == "RUST_CLI_TOOL_PATH_PLACEHOLDER": # Check against the actual string
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                default_path = os.path.join(project_root, "flag_extractor_cli", "target", "release", "flag_extractor_cli")
                if os.name == 'nt':
                    default_path += ".exe"
                
                if os.path.exists(default_path):
                    print(f"Automatically set Rust CLI path: {default_path}")
                    return default_path
                else:
                    print(f"ERROR: Rust CLI tool not automatically found at: {default_path}")
                    return ""
            except Exception as e:
                print(f"ERROR during automatic Rust CLI path detection: {e}")
                return ""
        return path_to_check

    def is_cli_available(self):
        return bool(self.cli_path and os.path.exists(self.cli_path))

    def list_characters(self, save_file_path):
        if not self.is_cli_available():
            print("ERROR: Rust CLI tool not found or path not set for list_characters.")
            return None, "Rust CLI tool not found."

        command = [
            self.cli_path,
            "list-characters",
            "--save-file-path", save_file_path
        ]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if process.returncode != 0:
                error_message = f"Error listing characters (Rust CLI): {process.stderr[:200]}..."
                print(f"Rust CLI Error (list-characters): {process.stderr}")
                return None, error_message
            if not process.stdout.strip():
                return [], "No character data from Rust CLI."
            
            characters_data = json.loads(process.stdout)
            return characters_data, None
        except FileNotFoundError:
            return None, "Rust CLI not found during character listing."
        except json.JSONDecodeError:
            print(f"JSON Decode Error from list-characters output: {process.stdout}")
            return None, "Error parsing character data from Rust CLI."
        except Exception as e:
            print(f"General error in list_characters: {e}")
            return None, f"Error loading characters: {e}"

    def get_event_flags(self, save_file_path, slot_index, event_ids):
        if not self.is_cli_available():
            print("ERROR: Rust CLI tool not found or path not set for get_event_flags.")
            return None, "Rust CLI tool not found."
        if not save_file_path or not os.path.exists(save_file_path):
            return None, "Save file path not valid for Rust CLI."
        if not event_ids:
            return {}, None # Return empty dict if no event IDs to check

        event_ids_str_list = [str(eid) for eid in event_ids]
        command = [
            self.cli_path,
            "get-event-flags",
            "--save-file-path", save_file_path,
            "--slot-index", str(slot_index),
            "--event-ids", ",".join(event_ids_str_list)
        ]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if process.returncode != 0:
                error_message = f"Rust CLI failed (code {process.returncode}): {process.stderr[:200]}"
                print(f"ERROR: {error_message}")
                return None, error_message
            if not process.stdout.strip():
                print("ERROR: Rust CLI returned no output for get-event-flags.")
                return None, "Rust CLI returned no output."
            
            return json.loads(process.stdout), None
        except FileNotFoundError:
            return None, f"Rust CLI not found when attempting to run: {self.cli_path}"
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON from Rust CLI: {e}. Output: '{process.stdout}'")
            return None, "Failed to decode JSON from Rust CLI."
        except Exception as e:
            print(f"ERROR calling Rust CLI or parsing output: {e}")
            return None, f"Error during Rust CLI call: {e}"