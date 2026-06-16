import { useState, useEffect } from 'react'
import { api } from '../api'

export default function TherapistManagement() {
  const [list, setList] = useState([])
  const [rooms, setRooms] = useState([])
  const [name, setName] = useState('')
  const [roomName, setRoomName] = useState('')
  const [error, setError] = useState('')

  const load = () => api.therapists.list().then(r => setList(r.data))

  useEffect(() => {
    load()
    api.rooms.list().then(r => {
      setRooms(r.data)
      setRoomName(r.data[0]?.name || '')
    })
  }, [])

  const submit = async () => {
    if (!name.trim() || !roomName) { setError('이름과 치료실을 입력해주세요.'); return }
    setError('')
    try {
      await api.therapists.create({ name: name.trim(), room_name: roomName })
      setName('')
      load()
    } catch (e) {
      setError(e.response?.data?.detail || '저장 실패')
    }
  }

  const remove = async (id) => {
    await api.therapists.remove(id)
    load()
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold text-gray-800 mb-6">치료사 관리</h2>

      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <h3 className="font-medium text-gray-700 mb-4">새 치료사 등록</h3>
        <div className="flex gap-3 mb-3">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="치료사명"
            className="flex-1 border rounded-lg px-3 py-2 text-sm" />
          <select value={roomName} onChange={e => setRoomName(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm">
            {rooms.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
          </select>
          <button onClick={submit} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
            등록
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-left">
              <th className="px-4 py-3">이름</th>
              <th className="px-4 py-3">담당 치료실</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {list.map(t => (
              <tr key={t.id} className="border-t hover:bg-blue-50">
                <td className="px-4 py-3 font-medium">{t.name}</td>
                <td className="px-4 py-3">{t.room_name}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => remove(t.id)} className="text-red-500 hover:underline text-xs">삭제</button>
                </td>
              </tr>
            ))}
            {list.length === 0 && (
              <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-400">등록된 치료사가 없습니다.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
