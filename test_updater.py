#!/usr/bin/env python3
"""
Test script for auto-updater functionality
This simulates the update process locally
"""

import os
import sys
import shutil
import hashlib
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

def calculate_sha256(file_path):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def setup_test_environment():
    """Prepare test files and manifest"""
    print("Setting up test environment...")
    
    # 1. Check if installer exists
    installer_path = "ER_Boss_Checklist_Setup.exe"
    if not os.path.exists(installer_path):
        print(f"ERROR: {installer_path} not found!")
        print("Please build the installer first with: powershell.exe build_installer.ps1")
        return False
    
    # 2. Copy installer for testing
    test_installer = "ER_Boss_Checklist_Setup_Test.exe"
    shutil.copy(installer_path, test_installer)
    print(f"Created test installer: {test_installer}")
    
    # 3. Calculate hash
    sha256 = calculate_sha256(test_installer)
    print(f"SHA256: {sha256}")
    
    # 4. Update test manifest
    with open("test_manifest.json", "r") as f:
        manifest = json.load(f)
    
    manifest["sha256"] = sha256
    manifest["version"] = "1.0.6"  # Test version
    
    with open("test_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("Updated test_manifest.json with correct hash")
    
    return True

def start_test_server():
    """Start local HTTP server for testing"""
    class TestHTTPHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            print(f"[SERVER] {format}" % args)
    
    server = HTTPServer(('localhost', 8000), TestHTTPHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print("\nTest server started at http://localhost:8000")
    return server

def run_test_app():
    """Run the app with test configuration"""
    print("\n" + "="*50)
    print("STARTING TEST APPLICATION")
    print("="*50)
    
    # Temporarily replace app_config with test config
    import shutil
    
    # Backup original config
    shutil.copy("src/config/app_config.py", "src/config/app_config_backup.py")
    
    # Use test config
    shutil.copy("src/config/app_config_test.py", "src/config/app_config.py")
    
    print("\nTest app will:")
    print("1. Show as version 1.0.4")
    print("2. Check for updates from localhost:8000")
    print("3. Find version 1.0.6 available")
    print("4. Allow you to test download")
    print("\nLaunching app...")
    
    try:
        # Run the app
        os.system("python src/main.py")
    finally:
        # Restore original config
        shutil.copy("src/config/app_config_backup.py", "src/config/app_config.py")
        os.remove("src/config/app_config_backup.py")
        print("\nTest completed - config restored")

def main():
    print("="*50)
    print("AUTO-UPDATER TEST SUITE")
    print("="*50)
    
    # Setup test environment
    if not setup_test_environment():
        return 1
    
    # Start test server
    server = start_test_server()
    
    print("\n" + "="*50)
    print("TEST INSTRUCTIONS:")
    print("="*50)
    print("1. The app will start showing version 1.0.4")
    print("2. It should detect update to 1.0.6")
    print("3. Click 'Yes' to test download")
    print("4. Watch console for download progress")
    print("5. Check if installer launches")
    print("\nPress ENTER to start test app...")
    input()
    
    try:
        run_test_app()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    
    print("\n" + "="*50)
    print("CLEANUP")
    print("="*50)
    
    # Cleanup
    if os.path.exists("ER_Boss_Checklist_Setup_Test.exe"):
        os.remove("ER_Boss_Checklist_Setup_Test.exe")
        print("Removed test installer")
    
    print("\nTest complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
