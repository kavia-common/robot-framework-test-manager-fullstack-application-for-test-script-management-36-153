from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .app_config import get_settings
from .database import get_db
from .models import User

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

auth_router = APIRouter()


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type, always 'bearer'")


class UserOut(BaseModel):
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="User name")
    roles: List[str] = Field(..., description="List with one role: admin|tester|viewer")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Hash a password using passlib."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or settings.jwt_expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


# PUBLIC_INTERFACE
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Decode token and return the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


# PUBLIC_INTERFACE
def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """In real app we could check 'disabled'. For now return user."""
    return user


# PUBLIC_INTERFACE
def require_roles(*roles: str):
    """Dependency factory enforcing role membership."""

    def _inner(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return user

    return _inner


# Auth endpoints
@auth_router.post("/login", response_model=Token, summary="Authenticate user and issue token")
def login(form_data: dict = Depends(), db: Session = Depends(get_db)):
    # Accept JSON body with username/password
    username = form_data.get("username")
    password = form_data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")

    user = get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username, "role": user.role})
    return Token(access_token=token, token_type="bearer")


@auth_router.get("/me", response_model=UserOut, summary="Retrieve current user info and roles")
def me(user: User = Depends(get_current_active_user)):
    return UserOut(user_id=user.id, username=user.username, roles=[user.role])


@auth_router.post("/logout", status_code=204, summary="Invalidate session/token")
def logout(_: User = Depends(get_current_active_user)):
    # Stateless JWT: client should discard token. For future: add blacklist.
    return None
