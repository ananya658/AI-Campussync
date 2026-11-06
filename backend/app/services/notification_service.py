import asyncio
from threading import RLock
from typing import List, Dict, Optional, Set
from fastapi import WebSocket
from sqlalchemy.orm import Session
from backend.app.models import Notification, Student

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_loops: Dict[WebSocket, asyncio.AbstractEventLoop] = {}
        self._lock = RLock()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        with self._lock:
            self.active_connections.setdefault(user_id, set()).add(websocket)
            self.connection_loops[websocket] = asyncio.get_running_loop()

    def disconnect(self, websocket: WebSocket, user_id: int):
        with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            self.connection_loops.pop(websocket, None)

    async def send_personal_message(self, message: dict, user_id: int):
        with self._lock:
            connections = tuple(self.active_connections.get(user_id, ()))
        dead_sockets = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_sockets.add(connection)
        for dead in dead_sockets:
            self.disconnect(dead, user_id)

    async def broadcast_to_users(self, message: dict, user_ids: List[int]):
        for uid in user_ids:
            await self.send_personal_message(message, uid)

    async def _deliver_to_connections(self, message: dict, recipients: list[tuple[int, WebSocket]]) -> None:
        for user_id, connection in recipients:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection, user_id)

    def publish_to_users(self, message: dict, user_ids: List[int]) -> None:
        """Schedule WebSocket delivery from synchronous request handlers."""
        with self._lock:
            recipients_by_loop: Dict[asyncio.AbstractEventLoop, list[tuple[int, WebSocket]]] = {}
            for user_id in user_ids:
                for connection in self.active_connections.get(user_id, ()):
                    loop = self.connection_loops.get(connection)
                    if loop is not None:
                        recipients_by_loop.setdefault(loop, []).append((user_id, connection))
        for loop, recipients in recipients_by_loop.items():
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._deliver_to_connections(message, recipients),
                    loop,
                )

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
        manager.publish_to_users(
            {"type": "notification", "notification_id": notif.id},
            [user_id],
        )
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
        batch_id: Optional[int] = None,
        link_url: Optional[str] = None
    ) -> int:
        """Broadcast notifications to students matching target branch, year, or section."""
        query = db.query(Student)
        if branch_id:
            query = query.filter(Student.branch_id == branch_id)
        if year:
            query = query.filter(Student.year == year)
        if section and section.strip().upper() != "ALL":
            sections = [value.strip().upper() for value in section.split("+") if value.strip()]
            if sections:
                query = query.filter(Student.section.in_(sections))
        if batch_id:
            query = query.filter(Student.batch_id == batch_id)

        target_students = query.all()
        count = 0
        target_user_ids = []
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
            target_user_ids.append(student.user_id)
            count += 1
        
        if count > 0:
            db.commit()
            manager.publish_to_users(
                {"type": "notification", "title": title},
                target_user_ids,
            )
        return count

