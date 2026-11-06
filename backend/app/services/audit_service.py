import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend.app.models import AuditLog, User

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action_type: str,  # CREATE, UPDATE, DELETE, CANCEL, APPROVE, REJECT, RESOLVE
        entity_type: str,  # BOOKING, SCHEDULE, ANNOUNCEMENT, ROOM, REPORT, USER
        entity_id: Any,
        user: Optional[User] = None,
        previous_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create and commit an immutable audit log entry."""
        prev_str = json.dumps(previous_value, default=str) if isinstance(previous_value, (dict, list)) else (str(previous_value) if previous_value is not None else None)
        new_str = json.dumps(new_value, default=str) if isinstance(new_value, (dict, list)) else (str(new_value) if new_value is not None else None)

        audit_entry = AuditLog(
            user_id=user.id if user else None,
            user_role=user.role if user else "SYSTEM",
            user_name=user.full_name if user else "System Automated",
            action_type=action_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            previous_value=prev_str,
            new_value=new_str,
            reason=reason,
            ip_address=ip_address
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry
