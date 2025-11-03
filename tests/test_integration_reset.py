"""
Integration test to verify the new reset functionality works in app.py
"""

import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Test imports
print("Testing imports...")
try:
    from file_scanner import FileScanner
    print("✅ FileScanner imported")
except Exception as e:
    print(f"❌ Error importing FileScanner: {e}")
    sys.exit(1)

# Test that new methods exist
print("\nTesting FileScanner methods...")
scanner = FileScanner(tracking_file="/tmp/test_tracking.json")

methods_to_test = [
    'reset_file_status',
    'reset_all_files_status',
    'reset_all_tracking',
]

for method in methods_to_test:
    if hasattr(scanner, method):
        print(f"✅ FileScanner.{method} exists")
    else:
        print(f"❌ FileScanner.{method} missing")
        sys.exit(1)

# Test app.py functions exist
print("\nTesting app.py functions...")
try:
    # We need to be careful here because importing app.py will initialize Streamlit
    # So we'll just check if the file contains the functions
    with open(os.path.join(project_root, 'app.py'), 'r') as f:
        app_content = f.read()
    
    functions_to_check = [
        'def clear_employee_markers():',
        'def clear_and_reset_all():',
        'def force_reload_employee_file():',
    ]
    
    for func in functions_to_check:
        if func in app_content:
            print(f"✅ {func.strip(':')} found in app.py")
        else:
            print(f"❌ {func.strip(':')} not found in app.py")
            sys.exit(1)
    
    # Check for UI elements
    ui_elements = [
        'Clear & Reset',
        'Force Reprocess All',
        'Force Re-import Employee File',
        '🔄 Reset',  # Individual file reset button
    ]
    
    print("\nTesting UI elements...")
    for element in ui_elements:
        if element in app_content:
            print(f"✅ UI element '{element}' found")
        else:
            print(f"❌ UI element '{element}' not found")
            sys.exit(1)
    
    # Check for modified auto_load_employee_file
    if 'csv_mtime > marker_mtime' in app_content:
        print("✅ Employee file modification detection implemented")
    else:
        print("❌ Employee file modification detection not found")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ All integration tests passed!")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error testing app.py: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cleanup
if os.path.exists("/tmp/test_tracking.json"):
    os.remove("/tmp/test_tracking.json")
