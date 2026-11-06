import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { FloorMapContainer } from './components/FloorMap/FloorMapContainer';
import { BookingPrefill, Room } from './types';

// Public Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { AboutPage } from './pages/AboutPage';

// Admin Pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { BuildingsRoomsPage } from './pages/admin/BuildingsRoomsPage';
import { AdminReconciliationPage } from './pages/admin/AdminReconciliationPage';
import { BookingsManagementPage } from './pages/admin/BookingsManagementPage';
import { AnnouncementsPage } from './pages/admin/AnnouncementsPage';
import { StudentReportsPage } from './pages/admin/StudentReportsPage';
import { AuditLogsPage } from './pages/admin/AuditLogsPage';
import { AnalyticsPage } from './pages/admin/AnalyticsPage';

// Faculty Pages
import { FacultyDashboard } from './pages/faculty/FacultyDashboard';
import { RoomFinderPage } from './pages/faculty/RoomFinderPage';
import { CreateBookingPage } from './pages/faculty/CreateBookingPage';
import { MyBookingsPage } from './pages/faculty/MyBookingsPage';
import { AIAssistantPage } from './pages/faculty/AIAssistantPage';

// Student Pages
import { StudentDashboard } from './pages/student/StudentDashboard';
import { TimetablePage } from './pages/student/TimetablePage';
import { ExamSchedulePage } from './pages/student/ExamSchedulePage';
import { ReportIssuePage } from './pages/student/ReportIssuePage';

export const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentView, setCurrentView] = useState<string>('landing');
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [prefilledBookingRoom, setPrefilledBookingRoom] = useState<Room | null>(null);
  const [prefilledBooking, setPrefilledBooking] = useState<BookingPrefill | null>(null);

  // Auto-redirect to dashboard when logged in and currently on public landing/login
  React.useEffect(() => {
    if (user) {
      if (currentView === 'landing' || currentView === 'login') {
        if (user.role === 'ADMIN') setCurrentView('admin-dashboard');
        else if (user.role === 'FACULTY') setCurrentView('faculty-dashboard');
        else if (user.role === 'STUDENT') setCurrentView('student-dashboard');
      }
    } else {
      if (currentView !== 'login' && currentView !== 'about') {
        setCurrentView('landing');
      }
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center text-xs font-semibold text-slate-500">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          <span>Synchronizing CampusSync AI...</span>
        </div>
      </div>
    );
  }

  // Handle booking quick action from map or search
  const handleInitiateBooking = (room: Room, booking?: BookingPrefill) => {
    setPrefilledBookingRoom(room);
    setPrefilledBooking(booking || null);
    setCurrentView('create-booking');
  };

  // Render view router
  const renderCurrentView = () => {
    switch (currentView) {
      // Public views
      case 'landing':
        return (
          <LandingPage
            onGetStarted={() => setCurrentView('login')}
            onExploreMap={() => setCurrentView('interactive-map')}
          />
        );
      case 'login':
        return (
          <LoginPage
            onLoginSuccess={() => {
              // Redirect handled by useEffect
            }}
          />
        );
      case 'about':
        return <AboutPage />;

      // Interactive Map
      case 'interactive-map':
        return (
          <FloorMapContainer
            onBookRoom={handleInitiateBooking}
            userRole={user?.role}
          />
        );

      // Admin views
      case 'admin-dashboard':
        return <AdminDashboard onNavigate={(v) => setCurrentView(v)} />;
      case 'admin-buildings':
        return <BuildingsRoomsPage />;
      case 'admin-reconciliation':
        return <AdminReconciliationPage />;
      case 'admin-bookings':
        return <BookingsManagementPage />;
      case 'admin-schedules':
        return <TimetablePage />;
      case 'admin-announcements':
        return <AnnouncementsPage />;
      case 'admin-reports':
        return <StudentReportsPage />;
      case 'admin-audit':
        return <AuditLogsPage />;
      case 'admin-analytics':
        return <AnalyticsPage />;

      // Faculty views
      case 'faculty-dashboard':
        return <FacultyDashboard onNavigate={(v) => setCurrentView(v)} />;
      case 'room-finder':
        return <RoomFinderPage onBookRoom={handleInitiateBooking} />;
      case 'create-booking':
        return (
          <CreateBookingPage
            initialRoom={prefilledBookingRoom}
            initialBooking={prefilledBooking}
            onBookingSuccess={() => setCurrentView('my-bookings')}
          />
        );
      case 'my-bookings':
        return (
          <MyBookingsPage
            onNewBookingClick={() => {
              setPrefilledBookingRoom(null);
              setPrefilledBooking(null);
              setCurrentView('create-booking');
            }}
          />
        );
      case 'faculty-schedule':
        return <TimetablePage />;
      case 'ai-assistant':
        return <AIAssistantPage onBookRoom={handleInitiateBooking} />;
      case 'announcements-view':
        return <AnnouncementsPage />;

      // Student views
      case 'student-dashboard':
        return <StudentDashboard onNavigate={(v) => setCurrentView(v)} />;
      case 'student-timetable':
        return <TimetablePage />;
      case 'student-exams':
        return <ExamSchedulePage />;
      case 'student-announcements':
        return <AnnouncementsPage />;
      case 'student-report':
        return <ReportIssuePage />;

      default:
        return (
          <LandingPage
            onGetStarted={() => setCurrentView('login')}
            onExploreMap={() => setCurrentView('interactive-map')}
          />
        );
    }
  };

  const isPublicStandalone = !user && (currentView === 'landing' || currentView === 'login');

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex flex-col font-sans">
      <Navbar
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onNavigateLanding={() => setCurrentView(user ? (user.role === 'ADMIN' ? 'admin-dashboard' : user.role === 'FACULTY' ? 'faculty-dashboard' : 'student-dashboard') : 'landing')}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Render Sidebar only when authenticated or viewing map/about */}
        {user && (
          <Sidebar
            currentView={currentView}
            onNavigate={(v) => setCurrentView(v)}
            isOpen={sidebarOpen}
            onCloseMobile={() => setSidebarOpen(false)}
          />
        )}

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {renderCurrentView()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return <AppContent />;
}

