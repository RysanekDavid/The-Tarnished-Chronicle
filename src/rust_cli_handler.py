# src/rust_cli_handler.py
import os
import subprocess
import json

class RustCliHandler:
    def __init__(self, cli_path_placeholder="RUST_CLI_TOOL_PATH_PLACEHOLDER"):
        self.cli_path = self.detect_rust_cli_path(cli_path_placeholder)

    def detect_rust_cli_path(self, placeholder):
        # ... (tato metoda zůstává beze změny) ...
        path_to_check = placeholder
        if path_to_check == "RUST_CLI_TOOL_PATH_PLACEHOLDER":
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
        # ... (tato metoda zůstává beze změny) ...
        if not self.is_cli_available():
            return None, "Rust CLI tool not found."
        command = [self.cli_path, "list-characters", "--save-file-path", save_file_path]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if process.returncode != 0:
                return None, f"Rust CLI Error: {process.stderr}"
            return json.loads(process.stdout), None
        except Exception as e:
            return None, f"Error executing list-characters: {e}"


    # --- ZDE JE ZMĚNA: Staré metody jsou nahrazeny jednou novou ---
    def get_full_status(self, save_file_path, slot_index, event_ids):
        """
        Calls the Rust CLI to get all character stats and boss flags in a single operation.
        """
        if not self.is_cli_available():
            return None, "Rust CLI tool not found."
        if not event_ids:
            return None, "No event IDs provided for status check."

        event_ids_str = ",".join(map(str, event_ids))
        command = [
            self.cli_path,
            "get-full-status",
            "--save-file-path", save_file_path,
            "--slot-index", str(slot_index),
            "--event-ids", event_ids_str
        ]
        
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if process.returncode != 0:
                error_message = f"Rust CLI failed (get-full-status): {process.stderr[:250]}"
                return None, error_message
            
            return json.loads(process.stdout), None
        except Exception as e:
            return None, f"Error executing get-full-status: {e}"