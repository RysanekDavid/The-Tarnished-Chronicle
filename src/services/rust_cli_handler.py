# src/rust_cli_handler.py
import os
import subprocess
import json
import sys


class RustCliHandler:
    def __init__(self, cli_path_placeholder="RUST_CLI_TOOL_PATH_PLACEHOLDER"):
        self.cli_path = self.detect_rust_cli_path(cli_path_placeholder)

    def detect_rust_cli_path(self, placeholder):
        # Check if running in a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # If bundled, the executable is in the root of the temporary directory
            base_path = sys._MEIPASS
            cli_name = "flag_extractor_cli.exe" if os.name == 'nt' else "flag_extractor_cli"
            bundle_path = os.path.join(base_path, cli_name)
            if os.path.exists(bundle_path):
                print(f"Found bundled Rust CLI at: {bundle_path}")
                return bundle_path

        # Fallback to original method for development environment
        path_to_check = placeholder
        if path_to_check == "RUST_CLI_TOOL_PATH_PLACEHOLDER":
            try:
                from ..utils import get_resource_path
                cli_name = "flag_extractor_cli.exe" if os.name == 'nt' else "flag_extractor_cli"
                default_path = get_resource_path(os.path.join("flag_extractor_cli", "target", "release", cli_name))

                if os.path.exists(default_path):
                    print(f"Automatically set Rust CLI path for dev: {default_path}")
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

    def _run_cli(self, command, operation_name):
        """Runs the Rust CLI and returns (parsed_json, error_message)."""
        try:
            process = subprocess.run(
                command,
                capture_output=True, text=True, check=False,
                encoding='utf-8', errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            return None, f"The game data reader ({operation_name}) took too long to respond."
        except OSError as e:
            return None, f"Failed to start the game data reader ({operation_name}): {e}"

        # The CLI emits non-fatal warnings (skipped slots, skipped regulation
        # data) on stderr even on success — keep them visible for diagnostics.
        stderr = (process.stderr or "").strip()
        if stderr:
            print(f"[RustCLI {operation_name}] {stderr}")

        if process.returncode != 0:
            detail = stderr or "no error output"
            return None, f"Save file could not be parsed ({operation_name}): {detail}"

        try:
            return json.loads(process.stdout), None
        except json.JSONDecodeError as e:
            return None, (
                f"The game data reader ({operation_name}) returned invalid output: {e}. "
                f"Output started with: {process.stdout[:200]!r}"
            )

    def list_characters(self, save_file_path):
        if not self.is_cli_available():
            return None, "Rust CLI tool not found."
        command = [self.cli_path, "list-characters", "--save-file-path", save_file_path]
        return self._run_cli(command, "list-characters")

    def get_full_status(self, save_file_path, slot_index, event_ids):
        """
        Calls the Rust CLI to get all character stats and boss flags in a single operation.
        """
        if not self.is_cli_available():
            return None, "Rust CLI tool not found."
        if not event_ids:
            return None, "No event IDs provided for status check."

        command = [
            self.cli_path,
            "get-full-status",
            "--save-file-path", save_file_path,
            "--slot-index", str(slot_index),
            "--event-ids", ",".join(map(str, event_ids)),
        ]
        return self._run_cli(command, "get-full-status")
