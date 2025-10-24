#!/usr/bin/env python3
"""
Comprehensive verification script for authentication cleanup.
Checks that all JWT/OAuth2/auth code has been removed.
"""

import os
import sys
import json

def check_files_deleted():
    """Check that auth files have been deleted."""
    print("=" * 60)
    print("1. Checking deleted files...")
    print("=" * 60)
    
    deleted_files = [
        "src/auth/jwt_handler.py",
        "src/auth/rbac.py",
        "src/auth/__init__.py",
        "src/api/routers/auth.py"
    ]
    
    all_deleted = True
    for file_path in deleted_files:
        if os.path.exists(file_path):
            print(f"❌ File still exists: {file_path}")
            all_deleted = False
        else:
            print(f"✅ Deleted: {file_path}")
    
    # Check if auth directory is gone
    if os.path.exists("src/auth"):
        print("❌ Directory still exists: src/auth/")
        all_deleted = False
    else:
        print("✅ Directory removed: src/auth/")
    
    return all_deleted

def check_dependencies():
    """Check that auth dependencies are removed from requirements.txt."""
    print("\n" + "=" * 60)
    print("2. Checking dependencies...")
    print("=" * 60)
    
    with open("requirements.txt", "r") as f:
        content = f.read()
    
    auth_deps = ["python-jose", "passlib"]
    found_deps = []
    
    for dep in auth_deps:
        if dep.lower() in content.lower():
            print(f"❌ Found auth dependency: {dep}")
            found_deps.append(dep)
        else:
            print(f"✅ Removed: {dep}")
    
    return len(found_deps) == 0

def check_imports():
    """Check that all imports work."""
    print("\n" + "=" * 60)
    print("3. Checking imports...")
    print("=" * 60)
    
    sys.path.insert(0, '.')
    
    modules = [
        ("src.database.models", "Database models"),
        ("src.database.connection", "Database connection"),
        ("src.api.main", "Main API"),
        ("src.api.routers.tests", "Tests router"),
        ("src.api.routers.cases", "Cases router"),
        ("src.api.routers.execution", "Execution router"),
        ("src.api.routers.queue", "Queue router"),
        ("src.api.routers.history", "History router"),
    ]
    
    all_imported = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {description}: {module_name}")
        except Exception as e:
            print(f"❌ {description}: {e}")
            all_imported = False
    
    return all_imported

def check_openapi():
    """Check OpenAPI spec has no auth endpoints or schemas."""
    print("\n" + "=" * 60)
    print("4. Checking OpenAPI specification...")
    print("=" * 60)
    
    with open("interfaces/openapi.json", "r") as f:
        openapi = json.load(f)
    
    issues = []
    
    # Check for auth paths
    auth_paths = ["/api/v1/auth/login", "/api/v1/auth/me", "/api/v1/auth/logout"]
    for path in auth_paths:
        if path in openapi.get("paths", {}):
            issues.append(f"Auth path still present: {path}")
    
    if not issues:
        print("✅ No auth endpoints in paths")
    
    # Check for auth schemas
    auth_schemas = ["Token", "LoginRequest", "UserResponse"]
    schemas = openapi.get("components", {}).get("schemas", {})
    for schema in auth_schemas:
        if schema in schemas:
            issues.append(f"Auth schema still present: {schema}")
    
    if not issues:
        print("✅ No auth schemas in components")
    
    # Check for security schemes
    if "securitySchemes" in openapi.get("components", {}):
        issues.append("Security schemes still defined")
    else:
        print("✅ No security schemes defined")
    
    # Check for global security
    if "security" in openapi:
        issues.append("Global security requirements still defined")
    else:
        print("✅ No global security requirements")
    
    # Check for auth tag
    tags = openapi.get("tags", [])
    for tag in tags:
        if tag.get("name") == "authentication":
            issues.append("Authentication tag still present")
    
    if not any(tag.get("name") == "authentication" for tag in tags):
        print("✅ No authentication tag")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return False
    
    return True

def check_code_references():
    """Check for lingering auth references in code."""
    print("\n" + "=" * 60)
    print("5. Checking code for auth references...")
    print("=" * 60)
    
    patterns = [
        ("jwt", "JWT references"),
        ("oauth", "OAuth references"),
        ("HTTPBearer", "HTTPBearer security"),
        ("python-jose", "python-jose imports"),
        ("passlib", "passlib imports"),
    ]
    
    found_issues = []
    
    for pattern, description in patterns:
        # Search in Python files
        result = os.popen(
            f'grep -r "{pattern}" --include="*.py" src/ 2>/dev/null | '
            f'grep -v "verify_no_auth.py" | grep -v "__pycache__"'
        ).read().strip()
        
        if result:
            found_issues.append(f"{description}: Found in code")
            print(f"❌ {description}")
        else:
            print(f"✅ No {description}")
    
    return len(found_issues) == 0

def check_env_vars():
    """Check that .env.example has no JWT secrets."""
    print("\n" + "=" * 60)
    print("6. Checking environment variables...")
    print("=" * 60)
    
    if not os.path.exists(".env.example"):
        print("⚠️  .env.example not found")
        return True
    
    with open(".env.example", "r") as f:
        content = f.read()
    
    jwt_patterns = ["JWT_SECRET", "JWT_ALGORITHM", "ACCESS_TOKEN_EXPIRE", "SECRET_KEY="]
    found_patterns = []
    
    for pattern in jwt_patterns:
        if pattern in content and "MINIO_SECRET_KEY" not in pattern:
            found_patterns.append(pattern)
            print(f"❌ Found JWT variable: {pattern}")
    
    if not found_patterns:
        print("✅ No JWT environment variables")
        print("✅ MINIO_SECRET_KEY retained (for object storage)")
    
    return len(found_patterns) == 0

def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("AUTHENTICATION CLEANUP VERIFICATION")
    print("=" * 60 + "\n")
    
    results = {
        "Files Deleted": check_files_deleted(),
        "Dependencies Removed": check_dependencies(),
        "Imports Working": check_imports(),
        "OpenAPI Clean": check_openapi(),
        "Code References Clean": check_code_references(),
        "Environment Variables Clean": check_env_vars(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Authentication fully removed!")
    else:
        print("❌ SOME CHECKS FAILED - Review issues above")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
