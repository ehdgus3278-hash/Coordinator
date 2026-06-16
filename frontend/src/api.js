import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

export const api = {
  prescriptions: {
    list: ()              => http.get('/prescriptions'),
    create: (data)        => http.post('/prescriptions', data),
    update: (code, data)  => http.put(`/prescriptions/${code}`, data),
    remove: (code)        => http.delete(`/prescriptions/${code}`),
  },
  rooms: {
    list: ()              => http.get('/rooms'),
    update: (name, data)  => http.put(`/rooms/${encodeURIComponent(name)}`, data),
  },
  therapists: {
    list: ()              => http.get('/therapists'),
    create: (data)        => http.post('/therapists', data),
    update: (id, data)    => http.put(`/therapists/${id}`, data),
    remove: (id)          => http.delete(`/therapists/${id}`),
  },
  patients: {
    list: ()              => http.get('/patients'),
    remove: (id)          => http.delete(`/patients/${id}`),
  },
  schedules: {
    autoAssign: (data)           => http.post('/schedules/auto-assign', data),
    forPatient: (id, date)       => http.get(`/schedules/patient/${id}`, { params: { date } }),
    forRoom: (roomName, date)    => http.get('/schedules/room', { params: { room_name: roomName, date } }),
    forTherapist: (id, date)     => http.get(`/schedules/therapist/${id}`, { params: { date } }),
    remove: (id)                 => http.delete(`/schedules/${id}`),
  },
}

export const TIME_SLOTS = [
  '08:00','08:30','09:00','09:30','10:00','10:30','11:00','11:30',
  '13:30','14:00','14:30','15:00','15:30','16:00','16:30',
]

export function slotEndTime(slotTime) {
  const [h, m] = slotTime.split(':').map(Number)
  const total = h * 60 + m + 30
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

export function today() {
  return new Date().toISOString().split('T')[0]
}
