# CampusSync AI

> **Find the right campus room at the right time.**
>
> A classroom coordination prototype for the Institute of Engineering and Technology (IET) and Deeksha Bhawan at Deen Dayal Upadhyaya Gorakhpur University (DDUGU).

CampusSync AI brings room discovery, faculty bookings, student schedules, academic notices, and discrepancy reporting into one role-based application. It is designed around the *Build With AI: DevOps 2026* problem statement.

## How the prototype addresses the problem

| Problem statement need | CampusSync AI |
| --- | --- |
| Find rooms by campus location and availability | Browse the IET and Deeksha Bhawan floor maps, filter rooms, and check availability for a date and time. |
| Book rooms for classes, examinations, practicals, and events | Faculty and administrators can create and manage room bookings. |
| Prevent conflicting allocations | The booking service checks room, capacity, timetable, section, faculty, and travel-buffer conflicts before accepting a booking. |
| Suggest alternatives | When a room is unavailable, the app can show suitable alternative rooms. The assistant can also rank available rooms for a natural-language request. |
| Keep students informed | Students can view cohort schedules and relevant announcements, including schedule and venue updates. |
| Let students report inaccurate information | Students can submit discrepancy reports; administrators review and resolve them. Students cannot manage official bookings. |
| Provide access by role and retain history | Admin, faculty, and student permissions are enforced by the backend. Important actions are recorded in audit logs, and announcement edits have version history. |

## Main features

- **Campus room maps:** Interactive floor maps represent IET and Deeksha Bhawan as separate buildings.
- **Room discovery:** View room details, capacity, facilities, and availability.
- **Booking and conflict checks:** Booking rules include room availability, allowed use, room capacity, examination capacity, recurring schedules, section and faculty conflicts, and the cross-building travel buffer.
- **Alternative rooms:** Conflict responses can include available room options for the requested slot.
- **Natural-language room assistant:** A local rule-based parser extracts details such as date, time, building, room type, capacity, and facilities. Recommendations are checked against current room availability and ranked with an explanation. No external AI API key is required for this prototype.
- **Schedules and announcements:** Faculty and administrators can publish or update academic notices; students see relevant information and notifications.
- **Student reports:** Students can report room or schedule discrepancies and track their status.
- **Administrative tools:** Manage rooms and verification status, review reports, view audit history, and inspect capacity analytics.

## Roles

| Role | Typical actions |
| --- | --- |
| **Faculty** | Find rooms, request bookings, view their reservations, and publish or update announcements. |
| **Student** | View relevant schedules and notices and submit discrepancy reports. |
| **Admin** | Manage campus rooms, review reports, publish notices, inspect audit logs, and view analytics. |

## Technology

| Area | Stack |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Local database | SQLite |
| Other database option | PostgreSQL through `DATABASE_URL` |
| Authentication | JWT bearer tokens and role-based access control |
| Notifications | In-app notification center and a WebSocket endpoint |

## Run locally

### Prerequisites

- Python 3.12
- Node.js 20 and npm

### 1. Configure the backend

Run these commands from the repository root.

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux, use `cp .env.example .env`.

Generate a unique JWT secret:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `.env` as `JWT_SECRET`. The backend requires a secret of at least 32 bytes. Keep `.env` private; it is excluded from Git.

Create and activate a virtual environment, then install the backend requirements:

```powershell
python -m venv backend/venv
.\backend\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

On macOS or Linux, activate it with `source backend/venv/bin/activate`.

### 2. Start the backend

From the repository root, run:

```sh
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

On first startup, the app creates the local SQLite tables and seeds the prototype campus data. The API is at `http://127.0.0.1:8000`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

### 3. Start the frontend

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. The Vite development server proxies API and WebSocket requests to the local backend.

## Demo accounts

The backend seeds local demonstration accounts. The login page also has a one-click role switcher.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@ddugu.ac.in` | `Admin@123` |
| Faculty | `prof.sharma@ddugu.ac.in` | `Faculty@123` |
| Student | `rahul.cse23@ddugu.ac.in` | `Student@123` |

These credentials and seeded accounts are for local demonstrations only. Do not use them for real institutional accounts.

## Run the backend tests

With the backend virtual environment active, run this from the repository root:

```sh
python -m pytest backend/tests/test_campus_sync.py -v
```

The pytest configuration uses a temporary SQLite database and a test-only JWT secret so the suite does not connect to the developer's configured database.

## Useful API routes

All REST routes use the `/api` prefix.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check API availability |
| `POST` | `/api/auth/login` | Sign in and receive a JWT |
| `GET` | `/api/buildings` | List campus buildings and floors |
| `GET` | `/api/rooms` | Browse rooms |
| `GET` | `/api/rooms/availability` | Search room availability |
| `POST` | `/api/bookings` | Create a room booking |
| `GET` | `/api/bookings` | View bookings available to the signed-in role |
| `GET` | `/api/schedules/me` | View the current user's schedule |
| `GET` / `POST` | `/api/announcements` | View or publish announcements |
| `POST` | `/api/reports` | Submit a student discrepancy report |
| `POST` | `/api/ai/search` | Search for rooms with a natural-language request |
| `GET` | `/api/audit-logs` | View administrative audit history |

For the complete request and response schemas, open `/docs` while the backend is running.

## Repository layout

```text
backend/
  app/
    routers/                   FastAPI routes
    services/                  Booking, AI, audit, and notification logic
    campus_room_registry.json  Seed room and campus data
    sample_students.csv        Sample student data
  tests/                       Backend integration tests
frontend/
  src/
    components/FloorMap/       IET and Deeksha Bhawan maps
    pages/                     Admin, faculty, and student screens
```

The bundled room registry and sample accounts provide prototype data. Confirm room details, capacities, facilities, permitted uses, and student records against DDUGU's current official datasets before relying on them for campus operations.
