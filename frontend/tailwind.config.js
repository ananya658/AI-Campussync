/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        campus: {
          navy: '#0B132B',
          dark: '#1C2541',
          blue: '#1D4ED8',
          accent: '#3B82F6',
          violet: '#6366F1',
          surface: '#F8FAFC',
          card: '#FFFFFF',
          border: '#E2E8F0',
          textDark: '#0F172A',
          textMuted: '#64748B',
          available: '#10B981', // Green
          booked: '#EF4444',    // Red
          selected: '#2563EB',  // Blue
          pending: '#F59E0B',   // Yellow
          maintenance: '#6B7280'// Grey
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

