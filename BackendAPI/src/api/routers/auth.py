from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database.connection import get_db
from ...database.models import User
from ...auth.jwt_handler import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ...auth.rbac import get_current_user, get_user_roles

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
    Authenticate user and issue access token.
    
    Args:
        login_data: Username and password
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException: If authentication fails
    """
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information and roles.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User information including roles
    """
    user_roles = get_user_roles(current_user, db)
    return UserResponse(
        user_id=current_user.id,
        username=current_user.username,
        roles=[role.value for role in user_roles]
    )

# PUBLIC_INTERFACE
@router.post("/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (invalidate session/token).
    
    Note: In a JWT-based system, logout is typically handled client-side
    by removing the token. This endpoint exists for API completeness.
    
    Args:
        current_user: Current authenticated user
    """
    # In a JWT system, we would typically maintain a blacklist
    # For now, this is a no-op as the client should discard the token
    return None
