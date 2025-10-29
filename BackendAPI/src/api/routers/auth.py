"""
Authentication API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models import User
from src.schemas.auth import LoginRequest, TokenResponse, UserResponse
from src.services.auth_service import auth_service
from src.api.dependencies import get_current_user, get_client_info

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Authenticate user and issue token")
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    
    Args:
        login_data: Username and password
        request: Request object for client info
        db: Database session
        
    Returns:
        TokenResponse: Access token and token type
        
    Raises:
        HTTPException: If authentication fails
    """
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log authentication event
    client_info = get_client_info(request)
    auth_service.log_audit_event(
        db, user.id, "login",
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )
    
    # Create token
    token = auth_service.create_token(user)
    
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse, summary="Retrieve current user info and roles")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User information including roles
    """
    return UserResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        roles=[current_user.role.value],
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Invalidate session/token")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate token.
    Note: JWT tokens are stateless, so actual invalidation would require a token blacklist.
    This endpoint logs the logout event for audit purposes.
    
    Args:
        request: Request object for client info
        current_user: Current authenticated user
        db: Database session
    """
    client_info = get_client_info(request)
    auth_service.log_audit_event(
        db, current_user.id, "logout",
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )
    
    return None
