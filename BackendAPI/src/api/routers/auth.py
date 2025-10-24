"""
Authentication router.
Handles user authentication, login, logout, and user info endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.user_schemas import LoginRequest, TokenResponse, UserResponse
from src.services.auth_service import auth_service
from src.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Authenticate user and issue token")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and issue JWT token.
    
    - **username**: Username for authentication
    - **password**: User password
    
    Returns JWT access token and token type.
    """
    try:
        token_response = auth_service.login(db, login_data)
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse, summary="Retrieve current user info and roles")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information and roles.
    
    Requires valid JWT token in Authorization header.
    Returns user ID, username, email, and assigned roles.
    """
    try:
        user_id = current_user.get("sub")
        user_info = auth_service.get_user_info(db, user_id)
        return user_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Invalidate session/token")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout and invalidate session/token.
    
    In a stateless JWT implementation, the client should discard the token.
    Future enhancement: Token blacklisting could be implemented here.
    """
    # In stateless JWT, logout is handled client-side by discarding the token
    # For enhanced security, implement token blacklisting here
    return None
