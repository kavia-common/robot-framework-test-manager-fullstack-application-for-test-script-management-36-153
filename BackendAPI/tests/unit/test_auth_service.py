"""
Unit tests for authentication service.
"""

import pytest
from src.services.auth_service import auth_service
from src.schemas.auth import UserCreate
from src.database.models import UserRole


@pytest.mark.unit
def test_create_user(db_session):
    """Test user creation."""
    user_data = UserCreate(
        username="newuser",
        email="newuser@example.com",
        password="securepassword123"
    )
    
    user = auth_service.create_user(db_session, user_data)
    
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.role == UserRole.TESTER
    assert user.is_active is True


@pytest.mark.unit
def test_create_duplicate_username(db_session, test_user):
    """Test creating user with duplicate username fails."""
    user_data = UserCreate(
        username="testuser",  # Already exists
        email="different@example.com",
        password="password123"
    )
    
    with pytest.raises(ValueError, match="Username already exists"):
        auth_service.create_user(db_session, user_data)


@pytest.mark.unit
def test_authenticate_user_success(db_session, test_user):
    """Test successful user authentication."""
    user = auth_service.authenticate_user(db_session, "testuser", "testpassword")
    
    assert user is not None
    assert user.username == "testuser"


@pytest.mark.unit
def test_authenticate_user_wrong_password(db_session, test_user):
    """Test authentication with wrong password fails."""
    user = auth_service.authenticate_user(db_session, "testuser", "wrongpassword")
    
    assert user is None


@pytest.mark.unit
def test_authenticate_user_not_found(db_session):
    """Test authentication with non-existent user fails."""
    user = auth_service.authenticate_user(db_session, "nonexistent", "password")
    
    assert user is None


@pytest.mark.unit
def test_create_token(test_user):
    """Test JWT token creation."""
    token = auth_service.create_token(test_user)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.unit
def test_get_user_by_id(db_session, test_user):
    """Test getting user by ID."""
    user = auth_service.get_user_by_id(db_session, test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.username == test_user.username


@pytest.mark.unit
def test_get_user_by_username(db_session, test_user):
    """Test getting user by username."""
    user = auth_service.get_user_by_username(db_session, "testuser")
    
    assert user is not None
    assert user.username == "testuser"


@pytest.mark.unit
def test_log_audit_event(db_session, test_user):
    """Test audit logging."""
    auth_service.log_audit_event(
        db_session,
        test_user.id,
        "test_action",
        resource_type="test_resource",
        resource_id="123",
        details={"key": "value"}
    )
    
    # Verify audit log was created
    from src.database.models import AuditLog
    log = db_session.query(AuditLog).filter(
        AuditLog.user_id == test_user.id,
        AuditLog.action == "test_action"
    ).first()
    
    assert log is not None
    assert log.resource_type == "test_resource"
    assert log.resource_id == "123"
