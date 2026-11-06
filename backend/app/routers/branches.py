from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Branch, Section
from backend.app.schemas import AcademicSectionResponse, BranchResponse

router = APIRouter(prefix="/branches", tags=["Academic Data"])


@router.get("", response_model=List[BranchResponse])
def get_branches(db: Session = Depends(get_db)):
    """Return branch options from the existing academic records."""
    return db.query(Branch).order_by(Branch.code).all()


@router.get("/sections", response_model=List[AcademicSectionResponse])
def get_sections(
    branch_id: int = Query(..., ge=1),
    academic_year: int = Query(..., ge=1, le=4),
    db: Session = Depends(get_db),
):
    if not db.query(Branch.id).filter(Branch.id == branch_id).first():
        raise HTTPException(status_code=404, detail="Branch not found.")
    return db.query(Section).filter(
        Section.branch_id == branch_id,
        Section.academic_year == academic_year,
    ).order_by(Section.section_name).all()
