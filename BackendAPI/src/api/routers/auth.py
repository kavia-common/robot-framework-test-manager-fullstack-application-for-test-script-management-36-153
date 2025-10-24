from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    roles: list[str]

class LoginRequest(BaseModel):
    username: str
    password: str

# PUBLIC_INTERFACE
@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint (no authentication required - returns dummy token).
    
    Args:
        login_data: Username and password
        db: Database session
        
    Returns:
        Dummy access token
    """
    # Return a dummy token - authentication is disabled
    return {
        "access_token": "dummy-token-no-auth-required",
        "token_type": "bearer"
    }

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db)
):
    """
    Get current user information (no authentication required - returns dummy user).
    
    Args:
        db: Database session
        
    Returns:
        Dummy user information
    """
    return UserResponse(
        user_id="system",
        username="public-user",
        roles=["viewer"]
    )

# PUBLIC_INTERFACE
@router.post("/logout", status_code=204)
async def logout():
    """
    Logout endpoint (no-op since authentication is disabled).
    """
    return None
