# CampusSync AI
> **Smart Campus. Smarter Scheduling.**  
> *Official Intelligent Classroom Allocation & Academic Scheduling Platform for GDG on Campus "BUILD WITH AI: DevOps 2026", Deen Dayal Upadhyaya Gorakhpur University (DDUGU).*

---

## 🏛️ 1. Executive Summary & Problem Solved

Deen Dayal Upadhyaya Gorakhpur University (DDUGU) faces recurring classroom allocation and academic scheduling challenges:
- **Classroom Contention**: Faculty struggle to locate vacant lecture halls during peak hours.
- **Booking Overlaps**: Multiple departments inadvertently book the same hall for overlapping exam or lecture slots.
- **Communication Breakdown**: Examination venue shifts are not communicated instantly to students, leading to missed examinations.
- **Physical Blueprint Discrepancies**: The Deeksha Bhawan blueprint visibly includes rooms **LH13** and **LH14**, while the written syllabus registry historically identified only **LH01–LH12**.

**CampusSync AI** eliminates these bottlenecks through a centralized, intelligent platform featuring:
1. **Interactive SVG Architectural Blueprint Maps** for both the **IET Building** (Ground, 1st, and 2nd Floors) and **Deeksha Bhawan** (Ground and 1st Floors).
2. **Mathematical Interval Conflict Engine** (`existing_start < new_end AND existing_end > new_start`) enforced at both database and application levels.
3. **Deeksha Bhawan Discrepancy Resolution**: LH13/LH14 are isolated under a `PENDING_ADMIN_VERIFICATION` state with dedicated inspection and authorization controls.
4. **Natural Language AI Assistant**: Parses plain-English queries, queries live database availability, and computes multi-attribute utility recommendation scores (0–100%) with transparent explanations and alternative time slot suggestions.
5. **Role-Based Portals**: Distinct, permission-enforced interfaces for **Admin**, **Faculty**, and **Student**.
6. **Immutable Audit Trail & Versioned Examination Circulars**: Tracks every change and preserves prior notices for institutional accountability.

---

## 🛠️ 2. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Framer Motion, Lucide React, Recharts |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy ORM, Uvicorn, WebSockets |
| **Database** | PostgreSQL 16 (Production/Docker) with transparent fallback to SQLite for local development |
| **Security** | JWT (JSON Web Tokens), Direct Bcrypt Salted Password Hashing, Role-Based Access Control |
| **AI Engine** | Natural Language Parameter Extraction + Database Validation Engine (Gemini API ready + Offline Rule-Based Fallback) |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions CI/CD Pipeline |

---

## 🔑 3. Demo Credentials (Clearly Labeled Test Accounts)

The application includes pre-configured, realistic DDUGU test accounts with a **1-Click Quick Login Bar** available directly on the login and public pages:

| Role | Email | Password | Name & Department |
|---|---|---|---|
| **ADMIN** | `admin@ddugu.ac.in` | `Admin@123` | **Prof. Arvind Kumar** (Dean Office & Academic Planning) |
| **FACULTY** | `prof.sharma@ddugu.ac.in` | `Faculty@123` | **Dr. Ramesh Sharma** (Professor & HOD, Computer Science) |
| **FACULTY 2** | `dr.verma@ddugu.ac.in` | `Faculty@123` | **Dr. Sunita Verma** (Associate Professor, AI & ML) |
| **STUDENT** | `rahul.cse23@ddugu.ac.in` | `Student@123` | **Rahul Singh** (Roll: `23001CSE045`, CSE Year 3 Section A) |
| **STUDENT 2** | `priya.aiml24@ddugu.ac.in` | `Student@123` | **Priya Maurya** (Roll: `24001AIML012`, AI ML Year 2 Section B) |

---

## 🏢 4. Actual Campus Infrastructure Model

### A. Institute of Engineering & Technology (IET)
- **Academic Cohorts**:
  - **CSE**: ~150 students (Sections A & B)
  - **AI & ML**: ~150 students (Sections A & B)
  - **AI & DS**: ~75 students (Section A)
  - **ECE**: ~75 students (Section A)
  - **ME**: ~75 students (Section A)
  - **IT**: ~75 students (Section A)
  - Across 1st, 2nd, 3rd, and 4th academic years.
- **Ground Floor**:
  - `Library` (Capacity: 180 students)
  - `Teachers' Office` (Faculty Lounge & Cabins)
  - `Director's Office` (Executive Directorate)
  - `Administrative Office` (Academic Registrar & Student Affairs)
  - `Placement Cell` (Training & Placement Cell)
- **First Floor**:
  - `CSE Laboratory` (40 computers, AC, projector)
  - `ME Laboratory` (40 capacity, instruments, projector)
  - `ECE Laboratory` (40 capacity, circuit kits, projector)
  - `IT Laboratory` (40 computers, AC, projector)
  - `IET17`, `IET18`, `IET19`, `IET20` (Capacity: 75 students each, equipped with projectors & smartboards)
- **Second Floor**:
  - `Seminar Hall IET32` (Capacity: 200 students, audio system, dual projectors, conference stage)
  - `IET24`, `IET25`, `IET28`, `IET29`, `IET30` (Capacity: 75 students each)

### B. Deeksha Bhawan (~100m from IET)
- **Ground Floor**:
  - `LH01` to `LH07` (Capacity: 90 students each, tiered lecture seating)
- **First Floor**:
  - `LH08` to `LH12` (Official bookable lecture halls, 90 capacity each)
  - **LH13 & LH14 Blueprint Discrepancy**: Flagged with `verification_status="PENDING_ADMIN_VERIFICATION"` and visually indicated with hatched warning overlays on the interactive floor map. Administrators can verify or restrict these rooms with inspection notes and audit logging.

---

## 🗺️ 5. Interactive Floor Map Indicators

The interactive SVG blueprint highlights room states in real time based on date and time parameters:
- 🟢 **Green (`#10B981`)**: Available for immediate booking.
- 🔴 **Red (`#EF4444`)**: Booked / Occupied by an academic lecture or examination.
- 🔵 **Blue (`#2563EB`)**: Currently selected room.
- 🟡 **Yellow (`#F59E0B`)**: Pending administrative approval.
- ⚫ **Grey / Hatched (`#6B7280`)**: Maintenance, restricted, or unverified discrepancy room.

---

## ⚡ 6. Conflict Prevention Engine

Bookings are checked using the strict non-overlapping mathematical interval theorem:
```sql
existing_start < new_end AND existing_end > new_start
```
For every prospective booking, the engine validates:
1. `start_time < end_time` and reasonable duration (15 min – 8 hours).
2. Non-maintenance and active room status.
3. Administrative verification status (`PENDING_ADMIN_VERIFICATION` spaces cannot be booked directly).
4. Room capacity (`expected_students <= room.capacity`).
5. Overlapping active reservations (`CONFIRMED`, `APPROVED`, `PENDING_APPROVAL`).
6. Overlapping recurring weekly academic timetable lectures in that room.

---

## 🤖 7. CampusSync AI Assistant

Natural language room finder and recommendation engine:
- **Example 1**: *"Find an IET classroom for 70 students tomorrow between 11 AM and 12 PM."*
  - Extracted: `date=tomorrow`, `time=11:00-12:00`, `capacity=70`, `building=IET`.
  - Validates real database records via `ConflictEngine`.
  - Explains: *"Verified available on Fri, Nov 07 between 11:00 AM and 12:00 PM. Accommodates 75 students (perfect fit for your 70 expected count, with 5 buffer seats). Located in IET on the First Floor. Equipped with: PROJECTOR, SMART_BOARD, AC."*
- **Example 2**: *"Find a laboratory for an IT practical session tomorrow at 2 PM."*
  - Automatically identifies IT Laboratory, checks schedule, and matches computing terminals.
- **Alternative Slots**: If a requested room is congested, the assistant automatically probes and surfaces alternative unoccupied time slots (+1 hr, +2 hrs) and alternative rooms.

---

## 🚀 8. Quick Start Guide

### Option A: Local Development (Fastest)

#### 1. Backend Setup
```bash
cd "campus management system"

# Create and activate python venv
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations and seed data
PYTHONPATH=. python -m backend.app.seed

# Start FastAPI backend server
PYTHONPATH=. python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be accessible at: `http://127.0.0.1:8000/docs`

#### 2. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```
Open web browser at: `http://localhost:3000`

---

### Option B: Docker Compose (Production Stack)

```bash
cd "campus management system"

# Copy environment variables
cp .env.example .env

# Build and start PostgreSQL, FastAPI, and React Nginx containers
docker compose up --build -d
```
- Web Application: `http://localhost:3000`
- REST APIs: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/health`

---

## 🧪 9. Automated Test Suite (19 Suites / 100% Passing)

Automated tests cover all critical functional, concurrency, and security workflows:
1. `test_01_successful_login`: Validates JWT token issuance and role claims.
2. `test_02_unauthorized_access`: Rejects missing or forged credentials (401).
3. `test_03_room_availability`: Queries live database availability without mock delays.
4. `test_04_successful_booking`: Creates valid classroom reservation.
5. `test_05_overlapping_booking_rejection`: Enforces interval overlap rejection (`409 Conflict`).
6. `test_06_invalid_time_range`: Validates start time strictly before end time.
7. `test_07_insufficient_room_capacity`: Prevents reservations exceeding room capacity.
8. `test_08_cancelled_booking_frees_availability`: Validates that cancelled bookings free up slots immediately.
9. `test_09_student_permission_restrictions`: Confirms students are strictly barred from booking or modifying schedules (403 Forbidden).
10. `test_10_announcement_publishing_and_versions`: Validates notice publication and version history generation.
11. `test_11_student_report_and_resolution`: Tests student discrepancy tickets and administrative resolution notes.
12. `test_12_ai_recommendation_engine`: Validates NLP query extraction, constraint verification, and scoring against the database.
13. `test_13_half_open_interval_back_to_back`: Proves half-open intervals `[start, end)` allow back-to-back bookings (e.g. 17:00–18:00 and 18:00–19:00 in same room).
14. `test_14_dimension2_section_collision_rejection`: Prevents double-booking the same academic section across multiple rooms or timetable slots.
15. `test_15_dimension3_faculty_collision_rejection`: Prevents faculty double-booking in two classrooms simultaneously.
16. `test_16_spaced_examination_capacity_rejection`: Enforces 50% spacing ratio for examinations (rejects 75 candidates in 75-cap hall with 409) and validates split-sitting plan calculation.
17. `test_17_atomic_split_booking`: Creates dual linked bookings (`PRIMARY` and `SECONDARY`) across paired halls atomically.
18. `test_18_concurrency_race_condition_20_threads`: **20 concurrent threads** simultaneously attempt booking the exact same slot; asserts **exactly 1 succeeds** and **19 fail with 409 Conflict**.
19. `test_19_reconciliation_ledger_and_system_settings`: Verifies Table 9 reconciliation ledger and system buffer settings persistence.

Run tests:
```bash
PYTHONPATH=. ./backend/venv/bin/pytest backend/tests/test_campus_sync.py -v
```

---

## 🗄️ 10. PostgreSQL Setup & Database Maintenance (Neon / Supabase)

CampusSync AI supports real PostgreSQL databases out-of-the-box (Neon, Supabase, AWS RDS, Docker) as well as automated fallback to SQLite:

### A. Neon / Supabase Connection
1. Set `DATABASE_URL` in `.env`:
   ```bash
   # Neon PostgreSQL
   DATABASE_URL="postgresql://neondb_owner:password@ep-cool-frost-123456.us-east-2.aws.neon.tech/neondb?sslmode=require"
   
   # Supabase PostgreSQL
   DATABASE_URL="postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
   ```
2. Initialize and seed schema:
   ```bash
   PYTHONPATH=. python -m backend.app.seed --force
   ```

### B. Database Backup & Disaster Recovery
- **Create Backup**:
  ```bash
  # PostgreSQL Dump
  pg_dump "$DATABASE_URL" -F c -b -v -f campussync_backup_$(date +%Y%m%d).dump
  
  # SQLite Backup
  sqlite3 campussync.db ".backup 'campussync_backup_$(date +%Y%m%d).db'"
  ```
- **Rollback / Restore**:
  ```bash
  # PostgreSQL Restore
  pg_restore -d "$DATABASE_URL" -v -c campussync_backup_20261106.dump
  
  # SQLite Restore
  cp campussync_backup_20261106.db campussync.db
  ```

---

## 🌐 11. Vercel Frontend Deployment

Deploy the React Vite frontend to Vercel in 2 minutes:
1. Connect repository to [Vercel](https://vercel.com).
2. Set Root Directory to `./` (or `frontend`).
3. Build Command: `cd frontend && npm run build` (or `npm run build` if Root is `frontend`).
4. Output Directory: `frontend/dist` (or `dist`).
5. Configure Environment Variables:
   - `VITE_API_BASE_URL`: URL of your deployed FastAPI backend (e.g. `https://campussync-backend.onrender.com/api`).
6. The included `vercel.json` automatically manages client-side SPA routing rewrites.

---

## 📄 12. API Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | Service health status | Public |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT | Public |
| `GET` | `/api/auth/me` | Current user profile | Authenticated |
| `GET` | `/api/buildings` | List campus buildings & floors | Authenticated |
| `GET` | `/api/rooms` | Filter rooms & live status | Authenticated |
| `GET` | `/api/rooms/availability` | Query conflict-free room availability | Authenticated |
| `POST` | `/api/rooms/{id}/verify` | Resolve LH13/LH14 discrepancy | Admin |
| `POST` | `/api/bookings` | Book classroom with conflict check | Faculty / Admin |
| `GET` | `/api/bookings` | List active / historical bookings | Authenticated |
| `PATCH` | `/api/bookings/{id}/cancel` | Cancel booking with recorded reason | Faculty / Admin |
| `GET` | `/api/schedules/me` | Personalized student/faculty schedule | Authenticated |
| `GET` | `/api/announcements` | Filtered targeted notices | Authenticated |
| `POST` | `/api/announcements` | Publish notice (v1) | Faculty / Admin |
| `PATCH` | `/api/announcements/{id}` | Update notice & create next version | Faculty / Admin |
| `POST` | `/api/reports` | Submit discrepancy report | Student |
| `PATCH` | `/api/reports/{id}/resolve` | Resolve report with note | Admin |
| `POST` | `/api/ai/search` | Natural language room finder | Authenticated |
| `GET` | `/api/audit-logs` | Immutable audit log stream | Admin |
| `GET` | `/api/analytics/dashboard` | Computed capacity analytics | Admin |
| `WS` | `/ws/notifications/{id}` | Real-time notification WebSocket | Authenticated |

---

## 🎓 Hackathon Project Declaration
- **Project**: CampusSync AI
- **Tagline**: Smart Campus. Smarter Scheduling.
- **Hackathon**: BUILD WITH AI: DevOps 2026
- **Organization**: Google Developer Groups (GDG) on Campus
- **Institution**: Deen Dayal Upadhyaya Gorakhpur University (DDUGU), Gorakhpur, UP, India.

