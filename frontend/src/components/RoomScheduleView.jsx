import { useState, useEffect, useRef } from 'react'
import { api, TIME_SLOTS, today } from '../api'

export default function RoomScheduleView() {
  const [rooms, setRooms] = useState([])
  const [roomName, setRoomName] = useState('')
  const [date, setDate] = useState(today())
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const draggingId = useRef(null)

  useEffect(() => {
    api.rooms.list().then(r => {
      setRooms(r.data)
      if (r.data.length > 0) setRoomName(r.data[0].name)
    })
  }, [])

  const fetchRoom = () => {
    if (!roomName) return
    setError('')
    api.schedules.forRoom(roomName, date)
      .then(r => setData(r.data))
      .catch(e => { setError(e.response?.data?.detail || '조회 실패'); setData(null) })
  }

  useEffect(() => { fetchRoom() }, [roomName, date])

  const stationAt = (slot, station) => data?.slots.find(s => s.slot_time === slot && s.station === station)

  const handleDrop = async (slot, station) => {
    const id = draggingId.current
    draggingId.current = null
    if (!id) return
    const occupant = stationAt(slot, station)
    if (occupant && occupant.id !== id) return  // occupied by another — ignore
    try {
      await api.schedules.move(id, { slot_time: slot, station })
      fetchRoom()
    } catch (e) {
      setError(e.response?.data?.detail || '이동 실패')
    }
  }

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
            <p className="text-xs text-gray-400 mb-2">셀을 드래그해서 시간/스테이션을 변경할 수 있습니다.</p>
            <table className="w-full text-sm border-collapse min-w-[600px]">
              <thead>
                <tr className="bg-gray-50 text-gray-600">
                  <th className="border px-3 py-2">시간</th>
                  {data.stations.map(st => (
                    <th key={st} className="border px-3 py-2">{st}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TIME_SLOTS.map(slot => (
                  <tr key={slot} className="hover:bg-blue-50">
                    <td className="border px-3 py-2 font-mono text-gray-600 text-xs">{slot}</td>
                    {data.stations.map(st => {
                      const s = stationAt(slot, st)
                      return (
                        <td
                          key={st}
                          className="border px-1 py-1"
                          onDragOver={e => e.preventDefault()}
                          onDrop={() => handleDrop(slot, st)}
                        >
                          {s ? (
                            <div
                              draggable
                              onDragStart={() => { draggingId.current = s.id }}
                              onDragEnd={() => { draggingId.current = null }}
                              className="font-medium text-gray-800 px-2 py-1 rounded cursor-grab select-none hover:bg-white/60"
                            >
                              {s.label}
                            </div>
                          ) : (
                            <span className="text-gray-200 px-2 py-1">-</span>
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
