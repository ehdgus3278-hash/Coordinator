import { Routes, Route, NavLink } from 'react-router-dom'
import PatientRegistration from './components/PatientRegistration'
import PatientScheduleView from './components/PatientScheduleView'
import RoomScheduleView from './components/RoomScheduleView'
import TherapistScheduleView from './components/TherapistScheduleView'
import PrescriptionManagement from './components/PrescriptionManagement'
import TherapistManagement from './components/TherapistManagement'

const NAV = [
  { to: '/',              label: '환자 등록' },
  { to: '/patient-view',  label: '환자별 시간표' },
  { to: '/room-view',     label: '치료실별 시간표' },
  { to: '/therapist-view',label: '치료사별 시간표' },
  { to: '/prescriptions', label: '처방코드 관리' },
  { to: '/therapists',    label: '치료사 관리' },
]

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 text-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <h1 className="text-lg font-bold tracking-wide">재활치료 스케줄링 코디네이터</h1>
        </div>
      </header>

      <nav className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {NAV.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                  isActive
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/"               element={<PatientRegistration />} />
          <Route path="/patient-view"   element={<PatientScheduleView />} />
          <Route path="/room-view"      element={<RoomScheduleView />} />
          <Route path="/therapist-view" element={<TherapistScheduleView />} />
          <Route path="/prescriptions"  element={<PrescriptionManagement />} />
          <Route path="/therapists"     element={<TherapistManagement />} />
        </Routes>
      </main>
    </div>
  )
}
