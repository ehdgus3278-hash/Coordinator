import { useState, useEffect } from 'react'
import { api, TIME_SLOTS, today } from '../api'

export default function RoomScheduleView() {
  const [rooms, setRooms] = useState([])
  const [roomName, setRoomName] = useState('')
  const [date, setDate] = useState(today())
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.rooms.list().then(r => {
      setRooms(r.data)
      if (r.data.length > 0) setRoomName(r.data[0].name)
    })
  }, [])

  useEffect(() => {
    if (!roomName) return
    setError('')
    api.schedules.forRoom(roomName, date)
      .then(r => setData(r.data))
      .catch(e => { setError(e.response?.data?.detail || '조회 실패'); setData(null) })
  }, [roomName, date])

  const bedAt = (slot, bed) => data?.slots.find(s => s.slot_time === slot && s.bed_number === bed)

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 mb-6">치료실별 시간표</h2>

      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex gap-2 mb-6 border-b pb-4">
          {rooms.map(r => (
            <button
              key={r.name}
              onClick={() => setRoomName(r.name)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                roomName === r.name ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {r.name}
            </button>
          ))}
          <div className="ml-auto">
            <input type="date" value={date} onChange={e => setDate(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        {data && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse min-w-[600px]">
              <thead>
                <tr className="bg-gray-50 text-gray-600">
                  <th className="border px-3 py-2">시간</th>
                  {Array.from({ length: data.beds }, (_, i) => i + 1).map(bed => (
                    <th key={bed} className="border px-3 py-2">베드{bed}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TIME_SLOTS.map(slot => (
                  <tr key={slot} className="hover:bg-blue-50">
                    <td className="border px-3 py-2 font-mono text-gray-600">{slot}</td>
                    {Array.from({ length: data.beds }, (_, i) => i + 1).map(bed => {
                      const s = bedAt(slot, bed)
                      return (
                        <td key={bed} className="border px-3 py-2">
                          {s ? (
                            <div>
                              <div className="font-medium text-gray-800">{s.patient_name}</div>
                              <div className="text-xs text-blue-600 font-mono">{s.prescription_code}</div>
                            </div>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
