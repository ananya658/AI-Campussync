from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from backend.app.database import get_db
from backend.app.models import Announcement, AnnouncementVersion, User, Student, Room, Building, Branch, Batch, Section
from backend.app.schemas import (
    AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse, AnnouncementVersionResponse
)
from backend.app.dependencies import get_current_user, require_role
from backend.app.services.audit_service import AuditService
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/announcements", tags=["Announcements"])


def _validate_audience(
    db: Session,
    branch_id: Optional[int],
    year: Optional[int],
    batch_id: Optional[int],
    section: Optional[str],
) -> None:
    if year is not None and year not in {1, 2, 3, 4}:
        raise HTTPException(status_code=422, detail="target_year must be between 1 and 4.")
    if branch_id is not None and not db.query(Branch.id).filter(Branch.id == branch_id).first():
        raise HTTPException(status_code=404, detail="Target branch not found.")
    if batch_id is not None and not db.query(Batch.id).filter(Batch.id == batch_id).first():
        raise HTTPException(status_code=404, detail="Target batch not found.")
    if section and section.upper() != "ALL":
        sections = db.query(Section.id).filter(Section.section_name == section.upper())
        if branch_id is not None:
            sections = sections.filter(Section.branch_id == branch_id)
        if year is not None:
            sections = sections.filter(Section.academic_year == year)
        if not sections.first():
            raise HTTPException(status_code=422, detail="The target section does not exist for that audience.")


def _visible_announcements(db: Session, current_user: User):
    query = db.query(Announcement)
    if current_user.role == "ADMIN":
        return query
    if current_user.role == "FACULTY":
        return query.filter(
            or_(
                Announcement.status == "PUBLISHED",
                and_(
                    Announcement.created_by_id == current_user.id,
                    Announcement.status != "ARCHIVED",
                ),
            )
        )
    if current_user.role == "STUDENT":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return query.filter(Announcement.id == -1)
        return query.filter(
            Announcement.status == "PUBLISHED",
            or_(Announcement.target_branch_id.is_(None), Announcement.target_branch_id == student.branch_id),
            or_(Announcement.target_year.is_(None), Announcement.target_year == student.year),
            or_(Announcement.target_batch_id.is_(None), Announcement.target_batch_id == student.batch_id),
            or_(
                Announcement.target_section.is_(None),
                Announcement.target_section == "ALL",
                Announcement.target_section == student.section,
            ),
        )
    return query.filter(Announcement.id == -1)

def format_announcement(a: Announcement) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "announcement_type": a.announcement_type,
        "date": a.date,
        "start_time": a.start_time,
        "end_time": a.end_time,
        "building_id": a.building_id,
        "room_id": a.room_id,
        "building_name": a.building.name if a.building else None,
        "room_number": a.room.room_number if a.room else None,
        "target_branch_id": a.target_branch_id,
        "target_year": a.target_year,
        "target_batch_id": a.target_batch_id,
        "target_section": a.target_section,
        "created_by_id": a.created_by_id,
        "creator_name": a.creator.full_name if a.creator else None,
        "status": a.status,
        "version": a.version,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "title": v.title,
                "description": v.description,
                "room_id": v.room_id,
                "date": v.date,
                "start_time": v.start_time,
                "end_time": v.end_time,
                "change_summary": v.change_summary,
                "modified_by_id": v.modified_by_id,
                "created_at": v.created_at
            }
            for v in a.versions
        ]
    }

@router.get("", response_model=List[AnnouncementResponse])
def get_announcements(
    type_filter: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = _visible_announcements(db, current_user)

    if type_filter:
        query = query.filter(Announcement.announcement_type == type_filter)

    announcements = query.order_by(desc(Announcement.created_at)).all()
    return [format_announcement(a) for a in announcements]

@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(announcement_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    a = _visible_announcements(db, current_user).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return format_announcement(a)

@router.post("", response_model=AnnouncementResponse)
def create_announcement(
    ann_in: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "FACULTY"]))
):
    if ann_in.status not in {"PUBLISHED", "DRAFT"}:
        raise HTTPException(status_code=422, detail="Announcement status must be PUBLISHED or DRAFT.")
    target_section = ann_in.target_section.strip().upper() if ann_in.target_section else None
    _validate_audience(
        db,
        ann_in.target_branch_id,
        ann_in.target_year,
        ann_in.target_batch_id,
        target_section,
    )

    new_ann = Announcement(
        title=ann_in.title,
        description=ann_in.description,
        announcement_type=ann_in.announcement_type,
        date=ann_in.date,
        start_time=ann_in.start_time,
        end_time=ann_in.end_time,
        building_id=ann_in.building_id,
        room_id=ann_in.room_id,
        target_branch_id=ann_in.target_branch_id,
        target_year=ann_in.target_year,
        target_batch_id=ann_in.target_batch_id,
        target_section=target_section,
        created_by_id=current_user.id,
        status=ann_in.status,
        version=1
    )
    db.add(new_ann)
    db.commit()
    db.refresh(new_ann)

    # Create initial version entry (v1)
    v1 = AnnouncementVersion(
        announcement_id=new_ann.id,
        version=1,
        title=new_ann.title,
        description=new_ann.description,
        room_id=new_ann.room_id,
        date=new_ann.date,
        start_time=new_ann.start_time,
        end_time=new_ann.end_time,
        change_summary="Initial publication",
        modified_by_id=current_user.id
    )
    db.add(v1)
    db.commit()
    db.refresh(new_ann)

    # Audit log
    AuditService.log(
        db=db,
        action_type="CREATE",
        entity_type="ANNOUNCEMENT",
        entity_id=new_ann.id,
        user=current_user,
        new_value=ann_in.model_dump(mode="json"),
        reason=f"Published notice: {new_ann.title}"
    )

    if new_ann.status == "PUBLISHED":
        notif_type = "EXAM_SCHEDULE_CHANGED" if "EXAM" in new_ann.announcement_type else "ANNOUNCEMENT"
        NotificationService.notify_target_students(
            db=db,
            title=f"Official Notice: {new_ann.title}",
            message=f"{new_ann.announcement_type.replace('_', ' ').title()}: {new_ann.description[:120]}",
            notification_type=notif_type,
            branch_id=new_ann.target_branch_id,
            year=new_ann.target_year,
            section=new_ann.target_section,
            batch_id=new_ann.target_batch_id,
            link_url=f"/announcements/{new_ann.id}"
        )

    return format_announcement(new_ann)

@router.patch("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    ann_update: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "FACULTY"]))
):
    a = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Faculty can only edit their own; admin can edit any
    if current_user.role == "FACULTY" and a.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit announcements created by others.")

    if ann_update.status is not None and ann_update.status not in {"PUBLISHED", "DRAFT", "ARCHIVED"}:
        raise HTTPException(status_code=422, detail="Unsupported announcement status.")

    old_status = a.status
    old_target = {
        "branch_id": a.target_branch_id,
        "year": a.target_year,
        "batch_id": a.target_batch_id,
        "section": a.target_section,
    }
    old_schedule = (a.date, a.start_time, a.end_time, a.building_id, a.room_id)
    old_content = (a.title, a.description)
    a.version += 1
    
    if ann_update.title is not None:
        a.title = ann_update.title
    if ann_update.description is not None:
        a.description = ann_update.description
    if ann_update.date is not None:
        a.date = ann_update.date
    if ann_update.start_time is not None:
        a.start_time = ann_update.start_time
    if ann_update.end_time is not None:
        a.end_time = ann_update.end_time
    if ann_update.building_id is not None:
        a.building_id = ann_update.building_id
    if ann_update.room_id is not None:
        a.room_id = ann_update.room_id
    if ann_update.status is not None:
        a.status = ann_update.status
    if "target_branch_id" in ann_update.model_fields_set:
        a.target_branch_id = ann_update.target_branch_id
    if "target_year" in ann_update.model_fields_set:
        a.target_year = ann_update.target_year
    if "target_batch_id" in ann_update.model_fields_set:
        a.target_batch_id = ann_update.target_batch_id
    if "target_section" in ann_update.model_fields_set:
        a.target_section = ann_update.target_section.strip().upper() if ann_update.target_section else None

    _validate_audience(db, a.target_branch_id, a.target_year, a.target_batch_id, a.target_section)

    # Record version history
    ver = AnnouncementVersion(
        announcement_id=a.id,
        version=a.version,
        title=a.title,
        description=a.description,
        room_id=a.room_id,
        date=a.date,
        start_time=a.start_time,
        end_time=a.end_time,
        change_summary=ann_update.change_summary,
        modified_by_id=current_user.id
    )
    db.add(ver)
    db.commit()
    db.refresh(a)

    # Audit log
    AuditService.log(
        db=db,
        action_type="UPDATE",
        entity_type="ANNOUNCEMENT",
        entity_id=a.id,
        user=current_user,
        previous_value={
            "status": old_status,
            "target": old_target,
            "schedule": old_schedule,
            "title": old_content[0],
            "description": old_content[1],
        },
        new_value={
            "version": a.version,
            "summary": ann_update.change_summary,
            "status": a.status,
            "target": {
                "branch_id": a.target_branch_id,
                "year": a.target_year,
                "batch_id": a.target_batch_id,
                "section": a.target_section,
            },
            "schedule": (a.date, a.start_time, a.end_time, a.building_id, a.room_id),
            "title": a.title,
            "description": a.description,
        },
        reason=f"Announcement updated (v{a.version}): {ann_update.change_summary}"
    )

    new_target = {
        "branch_id": a.target_branch_id,
        "year": a.target_year,
        "batch_id": a.target_batch_id,
        "section": a.target_section,
    }
    if old_status == "PUBLISHED" and a.status == "ARCHIVED":
        NotificationService.notify_target_students(
            db=db,
            title=f"Notice withdrawn: {a.title}",
            message=f"This notice was withdrawn. {ann_update.change_summary}",
            notification_type="EXAM_SCHEDULE_CHANGED",
            **old_target,
            link_url=f"/announcements/{a.id}",
        )
    elif a.status == "PUBLISHED" and (
        old_status != "PUBLISHED"
        or old_schedule != (a.date, a.start_time, a.end_time, a.building_id, a.room_id)
        or old_content != (a.title, a.description)
        or old_target != new_target
    ):
        if old_status == "PUBLISHED" and old_target != new_target:
            NotificationService.notify_target_students(
                db=db,
                title=f"Notice audience updated: {a.title}",
                message="A published notice is no longer targeted to your group. Check the student portal for current notices.",
                notification_type="ANNOUNCEMENT",
                **old_target,
                link_url=f"/announcements/{a.id}",
            )
        NotificationService.notify_target_students(
            db=db,
            title=f"Schedule update: {a.title} (v{a.version})",
            message=f"{ann_update.change_summary}. Open the notice to see the current details.",
            notification_type="EXAM_SCHEDULE_CHANGED",
            **new_target,
            link_url=f"/announcements/{a.id}",
        )

    return format_announcement(a)

