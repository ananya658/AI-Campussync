from typing import List, Dict, Optional, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from backend.app.models import Notification, User, Student, Branch

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            dead_sockets = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_sockets.add(connection)
            for dead in dead_sockets:
                self.active_connections[user_id].discard(dead)

    async def broadcast_to_users(self, message: dict, user_ids: List[int]):
        for uid in user_ids:
            await self.send_personal_message(message, uid)

manager = ConnectionManager()

class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        link_url: Optional[str] = None
    ) -> Notification:
        """Persist notification to database."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link_url=link_url,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def notify_target_students(
        db: Session,
        title: str,
        message: str,
        notification_type: str,
        branch_id: Optional[int] = None,
        year: Optional[int] = None,
        section: Optional[str] = None,
        link_url: Optional[str] = None
    ) -> int:
        """Broadcast notifications to students matching target branch, year, or section."""
        query = db.query(Student)
        if branch_id:
            query = query.filter(Student.branch_id == branch_id)
        if year:
            query = query.filter(Student.year == year)
        if section:
            query = query.filter(Student.section == section)

        target_students = query.all()
        count = 0
        for student in target_students:
            notif = Notification(
                user_id=student.user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                link_url=link_url,
                is_read=False
            )
            db.add(notif)
            count += 1
        
        if count > 0:
            db.commit()
        return count
