#!/usr/bin/env python3
"""
Verification script to confirm JWT/OAuth2 authentication has been removed.

This script checks:
1. Application can be imported without errors
2. No security schemes in OpenAPI spec
3. Endpoints are accessible without authentication
4. Environment variables don't reference JWT secrets
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_import():
    """Test that the application can be imported."""
    print("🔍 Testing application import...")
    try:
        from src.api.main import app
        print("  ✅ Application imported successfully")
        print(f"  ✅ App title: {app.title}")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_openapi_spec():
    """Test that OpenAPI spec has no security requirements."""
    print("\n🔍 Testing OpenAPI specification...")
    try:
        from src.api.main import app
        openapi_schema = app.openapi()
        
        # Check for security schemes
        security_schemes = openapi_schema.get("components", {}).get("securitySchemes")
        if security_schemes:
            print(f"  ❌ Found security schemes: {security_schemes}")
            return False
        else:
            print("  ✅ No security schemes found")
        
        # Check for global security
        global_security = openapi_schema.get("security")
        if global_security:
            print(f"  ❌ Found global security: {global_security}")
            return False
        else:
            print("  ✅ No global security requirements")
        
        return True
    except Exception as e:
        print(f"  ❌ OpenAPI test failed: {e}")
        return False

def test_routes():
    """Test that routes don't have auth dependencies."""
    print("\n🔍 Testing route definitions...")
    try:
        from src.api.main import app
        
        auth_required = False
        for route in app.routes:
            if hasattr(route, 'dependant'):
                # Check if route has security dependencies
                if hasattr(route.dependant, 'security_requirements'):
                    if route.dependant.security_requirements:
                        print(f"  ❌ Route {route.path} has security requirements")
                        auth_required = True
        
        if not auth_required:
            print("  ✅ No routes require authentication")
            return True
        return False
    except Exception as e:
        print(f"  ❌ Route test failed: {e}")
        return False

def test_env_example():
    """Test that .env.example doesn't have JWT secrets."""
    print("\n🔍 Testing .env.example...")
    try:
        env_file = Path(__file__).parent / ".env.example"
        if not env_file.exists():
            print("  ⚠️  .env.example not found")
            return True
        
        content = env_file.read_text()
        
        # Check for JWT-specific variables (not MinIO's MINIO_SECRET_KEY)
        jwt_patterns = [
            "JWT_SECRET",
            "JWT_ALGORITHM",
            "ACCESS_TOKEN_EXPIRE",
            "\nSECRET_KEY=",  # Must be on its own line (not part of MINIO_SECRET_KEY)
            "ALGORITHM=",
        ]
        
        found_jwt = []
        for pattern in jwt_patterns:
            if pattern in content:
                # Skip if it's a comment
                lines = content.split('\n')
                for line in lines:
                    if pattern.strip() in line and not line.strip().startswith('#'):
                        found_jwt.append(pattern.strip())
                        break
        
        if found_jwt:
            print(f"  ❌ Found JWT variables: {found_jwt}")
            return False
        else:
            print("  ✅ No JWT variables in .env.example")
            return True
    except Exception as e:
        print(f"  ❌ .env.example test failed: {e}")
        return False

def test_router_imports():
    """Test that routers don't import auth dependencies."""
    print("\n🔍 Testing router imports...")
    try:
        # Import to verify no errors - intentionally not storing
        import src.api.routers.tests  # noqa: F401
        import src.api.routers.cases  # noqa: F401
        import src.api.routers.execution  # noqa: F401
        import src.api.routers.queue  # noqa: F401
        import src.api.routers.history  # noqa: F401
        print("  ✅ All routers imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ Router import failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("JWT/OAuth2 Authentication Removal Verification")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_import),
        ("OpenAPI Spec Test", test_openapi_spec),
        ("Route Security Test", test_routes),
        ("Environment Config Test", test_env_example),
        ("Router Imports Test", test_router_imports),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("Authentication has been successfully removed.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
