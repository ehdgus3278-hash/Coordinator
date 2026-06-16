import { useState, useEffect } from 'react'
import { api } from '../api'

const emptyForm = { code: '', name: '', duration: 30, room_name: '' }

export default function PrescriptionManagement() {
  const [list, setList] = useState([])
  const [rooms, setRooms] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')

  const load = () => api.prescriptions.list().then(r => setList(r.data))

  useEffect(() => {
    load()
    api.rooms.list().then(r => {
      setRooms(r.data)
      setForm(f => ({ ...f, room_name: r.data[0]?.name || '' }))
    })
  }, [])

  const submit = async () => {
    if (!form.code.trim() || !form.name.trim() || !form.room_name) {
      setError('모든 필드를 입력해주세요.')
      return
    }
    setError('')
    try {
      if (editing) {
        await api.prescriptions.update(form.code, form)
      } else {
        await api.prescriptions.create({ ...form, code: form.code.toUpperCase().trim() })
      }
      setForm({ ...emptyForm, room_name: rooms[0]?.name || '' })
      setEditing(false)
      load()
    } catch (e) {
      setError(e.response?.data?.detail || '저장 실패')
    }
  }

  const edit = (rx) => { setForm(rx); setEditing(true); setError('') }
  const cancelEdit = () => { setForm({ ...emptyForm, room_name: rooms[0]?.name || '' }); setEditing(false); setError('') }

  const remove = async (code) => {
    await api.prescriptions.remove(code)
    load()
  }

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-bold text-gray-800 mb-6">처방코드 관리</h2>

      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <h3 className="font-medium text-gray-700 mb-4">{editing ? '처방코드 수정' : '새 처방코드 추가'}</h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">코드</label>
            <input value={form.code} disabled={editing}
              onChange={e => setForm({ ...form, code: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono disabled:bg-gray-100" placeholder="MM105AM" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">치료명</label>
            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="중추신경계치료" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">시간(분)</label>
            <input type="number" value={form.duration} min={5} step={5}
              onChange={e => setForm({ ...form, duration: Number(e.target.value) })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">치료실</label>
            <select value={form.room_name} onChange={e => setForm({ ...form, room_name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              {rooms.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
            </select>
          </div>
        </div>
        {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
        <div className="flex gap-2">
          <button onClick={submit} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
            {editing ? '수정 완료' : '추가'}
          </button>
          {editing && (
            <button onClick={cancelEdit} className="border px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
              취소
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-left">
              <th className="px-4 py-3">코드</th>
              <th className="px-4 py-3">치료명</th>
              <th className="px-4 py-3">시간</th>
              <th className="px-4 py-3">치료실</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {list.map(rx => (
              <tr key={rx.code} className="border-t hover:bg-blue-50">
                <td className="px-4 py-3 font-mono text-blue-700">{rx.code}</td>
                <td className="px-4 py-3">{rx.name}</td>
                <td className="px-4 py-3">{rx.duration}분</td>
                <td className="px-4 py-3">{rx.room_name}</td>
                <td className="px-4 py-3 text-right space-x-2">
                  <button onClick={() => edit(rx)} className="text-blue-600 hover:underline text-xs">수정</button>
                  <button onClick={() => remove(rx.code)} className="text-red-500 hover:underline text-xs">삭제</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
