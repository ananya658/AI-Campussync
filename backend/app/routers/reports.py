from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import IssueReport, Student, User, Room, Building
from backend.app.schemas import IssueReportCreate, IssueReportResolve, IssueReportResponse
from backend.app.dependencies import get_current_user, require_role
from backend.app.services.audit_service import AuditService
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/reports", tags=["Reports"])

def format_report(r: IssueReport) -> dict:
    return {
        "id": r.id,
        "student_id": r.student_id,
        "reporter_user_id": r.reporter_user_id,
        "reporter_name": r.reporter.full_name if r.reporter else None,
        "reporter_roll": r.student.roll_number if r.student else None,
        "category": r.category,
        "description": r.description,
        "building_id": r.building_id,
        "room_id": r.room_id,
        "building_name": r.building.name if r.building else None,
        "room_number": r.room.room_number if r.room else None,
        "scheduled_date": r.scheduled_date,
        "scheduled_time": r.scheduled_time,
        "status": r.status,
        "admin_resolution_note": r.admin_resolution_note,
        "resolved_by_id": r.resolved_by_id,
        "resolved_by_name": r.resolved_by.full_name if r.resolved_by else None,
        "resolved_at": r.resolved_at,
        "created_at": r.created_at
    }

@router.post("", response_model=IssueReportResponse)
def submit_issue_report(
    report_in: IssueReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=400,
            detail="Student profile not found. Only students can submit academic discrepancies."
        )

    new_report = IssueReport(
        student_id=student.id,
        reporter_user_id=current_user.id,
        category=report_in.category,
        description=report_in.description,
        building_id=report_in.building_id,
        room_id=report_in.room_id,
        scheduled_date=report_in.scheduled_date,
        scheduled_time=report_in.scheduled_time,
        status="PENDING"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # Audit log
    AuditService.log(
        db=db,
        action_type="CREATE",
        entity_type="REPORT",
        entity_id=new_report.id,
        user=current_user,
        new_value={"category": report_in.category, "description": report_in.description},
        reason="Student reported academic schedule discrepancy"
    )

    # Notify student that report has been registered
    NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        title="Discrepancy Report Submitted",
        message=f"Your ticket regarding '{report_in.category.replace('_', ' ').title()}' is received and under administrative review.",
        notification_type="REPORT_RESOLVED"
    )

    return format_report(new_report)

@router.get("", response_model=List[IssueReportResponse])
def get_issue_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(IssueReport)

    # Students only see their own reports
    if current_user.role == "STUDENT":
        query = query.filter(IssueReport.reporter_user_id == current_user.id)

    if status_filter:
        query = query.filter(IssueReport.status == status_filter)

    reports = query.order_by(desc(IssueReport.created_at)).all()
    return [format_report(r) for r in reports]

@router.patch("/{report_id}/resolve", response_model=IssueReportResponse)
def resolve_issue_report(
    report_id: int,
    resolve_in: IssueReportResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    report = db.query(IssueReport).filter(IssueReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    old_status = report.status
    report.status = resolve_in.status
    report.admin_resolution_note = resolve_in.admin_resolution_note
    report.resolved_by_id = current_user.id
    report.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(report)

    # Audit log
    AuditService.log(
        db=db,
        action_type="RESOLVE",
        entity_type="REPORT",
        entity_id=report.id,
        user=current_user,
        previous_value={"status": old_status},
        new_value={"status": report.status, "note": resolve_in.admin_resolution_note},
        reason=f"Admin report resolution: {resolve_in.admin_resolution_note}"
    )

    # Notify student who reported the discrepancy
    NotificationService.create_notification(
        db=db,
        user_id=report.reporter_user_id,
        title=f"Report {resolve_in.status.title()}: {report.category.replace('_', ' ').title()}",
        message=f"Administrator note: {resolve_in.admin_resolution_note}",
        notification_type="REPORT_RESOLVED"
    )

    return format_report(report)

