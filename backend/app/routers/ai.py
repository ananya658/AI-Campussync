from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import AISearchRequest, AISearchResponse
from backend.app.services.ai_service import AIService
from backend.app.dependencies import require_role
from backend.app.models import User

router = APIRouter(prefix="/ai", tags=["AI Smart Assistant"])

@router.post("/search", response_model=AISearchResponse)
def natural_language_room_search(
    request: AISearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    """
    CampusSync AI Assistant natural language query parser and recommendation engine.
    Extracts constraints from natural text, validates against real database records,
    and returns scored recommendations with transparent explanations and alternatives.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    try:
        return AIService.search_and_recommend(
            db=db,
            query=request.query,
            user_role=current_user.role
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/recommend", response_model=AISearchResponse)
def get_intelligent_recommendation(
    request: AISearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["FACULTY", "ADMIN"]))
):
    return natural_language_room_search(request, db, current_user)

