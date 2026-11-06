from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import AuditLog, User
from backend.app.schemas import AuditLogResponse
from backend.app.dependencies import require_role

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)

    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
    return logs
