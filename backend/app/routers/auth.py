from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, Student, Faculty, Branch, Batch
from backend.app.schemas import UserLogin, UserCreate, UserResponse, Token
from backend.app.auth import hash_password, verify_password, create_access_token
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

_LOGIN_LIMIT = 5
_LOGIN_WINDOW_SECONDS = 15 * 60
_login_attempts: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_login_attempts_lock = Lock()


def _check_login_limit(request: Request, email: str) -> tuple[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    key = (client_ip, email.strip().lower())
    now = monotonic()
    cutoff = now - _LOGIN_WINDOW_SECONDS

    with _login_attempts_lock:
        for existing_key, attempts in list(_login_attempts.items()):
            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if not attempts:
                _login_attempts.pop(existing_key, None)

        attempts = _login_attempts[key]
        if len(attempts) >= _LOGIN_LIMIT:
            retry_after = max(1, int(_LOGIN_WINDOW_SECONDS - (now - attempts[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )
    return key


def _record_failed_login(key: tuple[str, str]) -> None:
    with _login_attempts_lock:
        _login_attempts[key].append(monotonic())


def _clear_failed_logins(key: tuple[str, str]) -> None:
    with _login_attempts_lock:
        _login_attempts.pop(key, None)

def format_user_response(user: User) -> dict:
    resp = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "department": user.department,
        "phone": user.phone,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "student_profile": None,
        "faculty_profile": None
    }
    if user.student_profile:
        resp["student_profile"] = {
            "id": user.student_profile.id,
            "roll_number": user.student_profile.roll_number,
            "branch_id": user.student_profile.branch_id,
            "branch_code": user.student_profile.branch.code if user.student_profile.branch else None,
            "branch_name": user.student_profile.branch.name if user.student_profile.branch else None,
            "batch_id": user.student_profile.batch_id,
            "year": user.student_profile.year,
            "section": user.student_profile.section
        }
    if user.faculty_profile:
        resp["faculty_profile"] = {
            "id": user.faculty_profile.id,
            "employee_code": user.faculty_profile.employee_code,
            "designation": user.faculty_profile.designation,
            "department": user.faculty_profile.department,
            "cabin_room_id": user.faculty_profile.cabin_room_id
        }
    return resp

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    attempt_key = _check_login_limit(request, login_data.email)
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        _record_failed_login(attempt_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        _clear_failed_logins(attempt_key)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    _clear_failed_logins(attempt_key)
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": format_user_response(user)
    }

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role.upper(),
        department=user_data.department,
        phone=user_data.phone,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return format_user_response(new_user)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return format_user_response(current_user)

