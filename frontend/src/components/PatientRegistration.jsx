import { useState, useEffect } from 'react'
import { api, TIME_SLOTS, slotEndTime, today } from '../api'

const SLOT_OPTIONS = TIME_SLOTS.map(t => ({ value: t, label: t }))
const END_OPTIONS = TIME_SLOTS.map(t => ({ value: slotEndTime(t), label: slotEndTime(t) }))

export default function PatientRegistration() {
  const [name, setName] = useState('')
  const [date, setDate] = useState(today())
  const [availStart, setAvailStart] = useState('08:00')
  const [availEnd, setAvailEnd] = useState('17:00')
  const [orders, setOrders] = useState([{ room: '', code: '' }])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [prescriptions, setPrescriptions] = useState([])
  const [rooms, setRooms] = useState([])

  useEffect(() => {
    api.prescriptions.list().then(r => setPrescriptions(r.data)).catch(() => {})
    api.rooms.list().then(r => setRooms(r.data)).catch(() => {})
  }, [])

  const addOrder = () => setOrders(prev => [...prev, { room: '', code: '' }])
  const removeOrder = i => setOrders(prev => prev.filter((_, idx) => idx !== i))
  const updateOrderRoom = (i, room) => setOrders(prev => prev.map((o, idx) => idx === i ? { room, code: '' } : o))
  const updateOrderCode = (i, code) => setOrders(prev => prev.map((o, idx) => idx === i ? { ...o, code } : o))

  const handleSubmit = async () => {
    if (!name.trim()) { setError('환자명을 입력해주세요.'); return }
    const validOrders = orders.map(o => o.code).filter(Boolean)
    if (validOrders.length === 0) { setError('처방코드를 1개 이상 입력해주세요.'); return }

    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await api.schedules.autoAssign({
        name: name.trim(),
        available_start: availStart,
        available_end: availEnd,
        orders: validOrders,
        date,
      })
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || '배정 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setName('')
    setOrders([{ room: '', code: '' }])
    setResult(null)
    setError('')
  }

  const roomColor = (room) => {
    if (room.includes('뇌재활')) return 'bg-indigo-50 border-l-4 border-indigo-400'
    if (room.includes('작업')) return 'bg-green-50 border-l-4 border-green-400'
    if (room.includes('언어')) return 'bg-orange-50 border-l-4 border-orange-400'
    return 'bg-gray-50 border-l-4 border-gray-400'
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold text-gray-800 mb-6">환자 등록 및 자동 배정</h2>

      <div className="bg-white rounded-xl shadow p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">환자명</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="홍길동"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">배정 날짜</label>
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">가능 시간</label>
          <div className="flex items-center gap-2">
            <select value={availStart} onChange={e => setAvailStart(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
              {SLOT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <span className="text-gray-500">~</span>
            <select value={availEnd} onChange={e => setAvailEnd(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">
              {END_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">처방코드</label>
          <div className="space-y-2">
            {orders.map((order, i) => {
              const roomCodes = prescriptions.filter(rx => rx.room_name === order.room)
              return (
                <div key={i} className="flex gap-2 items-center">
                  <select
                    value={order.room}
                    onChange={e => updateOrderRoom(i, e.target.value)}
                    className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    <option value="">치료실 선택</option>
                    {rooms.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
                  </select>
                  <select
                    value={order.code}
                    onChange={e => updateOrderCode(i, e.target.value)}
                    disabled={!order.room}
                    className="flex-1 border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-50 disabled:text-gray-400"
                  >
                    <option value="">{order.room ? '처방코드 선택' : '먼저 치료실을 선택하세요'}</option>
                    {roomCodes.map(rx => (
                      <option key={rx.code} value={rx.code}>{rx.code} - {rx.name}</option>
                    ))}
                  </select>
                  {orders.length > 1 && (
                    <button onClick={() => removeOrder(i)}
                      className="text-red-400 hover:text-red-600 text-lg leading-none px-1">×</button>
                  )}
                </div>
              )
            })}
          </div>
          <button onClick={addOrder}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1">
            + 처방코드 추가
          </button>
        </div>

        {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">{error}</p>}

        <div className="flex gap-3">
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium py-2.5 rounded-lg transition-colors"
          >
            {loading ? '배정 중...' : '자동 배정'}
          </button>
          <button onClick={reset}
            className="px-4 py-2.5 border rounded-lg text-gray-600 hover:bg-gray-50 text-sm">
            초기화
          </button>
        </div>
      </div>

      {result && (
        <div className="mt-6 bg-white rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-800">
              배정 결과 — <span className="text-blue-700">{result.patient_name}</span>
              <span className="text-sm font-normal text-gray-500 ml-2">({result.date})</span>
            </h3>
            <span className="text-xs text-gray-400">환자 ID: {result.patient_id}</span>
          </div>

          {result.warnings.length > 0 && (
            <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              {result.warnings.map((w, i) => (
                <p key={i} className="text-sm text-yellow-800">⚠ {w}</p>
              ))}
            </div>
          )}

          {result.schedules.length === 0 ? (
            <p className="text-gray-500 text-sm">배정된 스케줄이 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {result.schedules.map(s => (
                <div key={s.id} className={`flex items-center justify-between p-3 rounded-lg ${roomColor(s.room_name)}`}>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-gray-700 w-24">
                      {s.slot_time}~{slotEndTime(s.slot_time)}
                    </span>
                    <span className="font-mono text-sm text-blue-700 font-semibold">
                      {s.prescription_code}{s.overlay_code ? `+${s.overlay_code}` : ''}
                    </span>
                    <span className="text-sm text-gray-700">
                      {s.prescription_name}{s.overlay_name ? ` + ${s.overlay_name}` : ''}
                    </span>
                    <span className="text-xs text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded font-mono">{s.label}</span>
                  </div>
                  <span className="text-xs text-gray-500 bg-white/60 px-2 py-0.5 rounded">
                    {s.room_name} · {s.station}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
