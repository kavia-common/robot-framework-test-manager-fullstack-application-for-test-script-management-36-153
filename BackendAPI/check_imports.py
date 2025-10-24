#!/usr/bin/env python3
"""
Quick import check to verify no broken imports after auth removal.
"""
import sys
import importlib.util

def check_import(module_path, module_name):
    """Try to import a module and report any issues."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {module_name}: Import successful")
            return True
    except ImportError as e:
        print(f"❌ {module_name}: Import error - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name}: Other error - {e}")
        return False

def main():
    """Check critical modules for import errors."""
    print("Checking Python imports after auth removal...\n")
    
    modules = [
        ("src/database/models.py", "models"),
        ("src/database/connection.py", "connection"),
        ("src/api/main.py", "main"),
        ("src/api/routers/tests.py", "tests"),
        ("src/api/routers/cases.py", "cases"),
        ("src/api/routers/execution.py", "execution"),
        ("src/api/routers/queue.py", "queue"),
        ("src/api/routers/history.py", "history"),
    ]
    
    success_count = 0
    for module_path, module_name in modules:
        if check_import(module_path, module_name):
            success_count += 1
    
    print(f"\n{success_count}/{len(modules)} modules imported successfully")
    
    if success_count == len(modules):
        print("\n✅ All imports verified - no broken dependencies!")
        return 0
    else:
        print("\n❌ Some imports failed - review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
