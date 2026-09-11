from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.task import MessageResponse
from app.schemas.user import LoginRequest, PasswordChange, ProfileUpdate, TokenResponse, UserCreate, UserResponse
from app.security import (
    oauth2_scheme,
    create_access_token,
    get_current_user,
    hash_password,
    revoked_tokens,
    verify_password,
)
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(db, user.id, "User Registered", "User", user.id)
    return user

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return TokenResponse(
        access_token=create_access_token(
            str(user.id),
            user.role.value,
        )
    )

@router.post("/logout", response_model=MessageResponse)
def logout(token: str = Depends(oauth2_scheme)):
    revoked_tokens.add(token)

    return MessageResponse(
        message="Logged out successfully"
    )


@router.get("/profile", response_model=UserResponse)
def profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    record_audit(db, current_user.id, "Profile Updated", "User", current_user.id)
    return current_user


@router.put("/change-password", response_model=MessageResponse)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    record_audit(db, current_user.id, "Password Changed", "User", current_user.id)
    return MessageResponse(message="Password changed successfully")
