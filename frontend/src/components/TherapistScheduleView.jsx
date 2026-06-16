import { useState, useEffect } from 'react'
import { api, slotEndTime, today } from '../api'

export default function TherapistScheduleView() {
  const [therapists, setTherapists] = useState([])
  const [therapistId, setTherapistId] = useState('')
  const [date, setDate] = useState(today())
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.therapists.list().then(r => {
      setTherapists(r.data)
      if (r.data.length > 0) setTherapistId(String(r.data[0].id))
    })
  }, [])

  useEffect(() => {
    if (!therapistId) { setData(null); return }
    setError('')
    api.schedules.forTherapist(therapistId, date)
      .then(r => setData(r.data))
      .catch(e => { setError(e.response?.data?.detail || '조회 실패'); setData(null) })
  }, [therapistId, date])

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-bold text-gray-800 mb-6">치료사별 시간표</h2>

      {therapists.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-6 text-sm text-gray-500">
          등록된 치료사가 없습니다. '치료사 관리'에서 먼저 등록해주세요.
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex gap-4 mb-6">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">치료사 선택</label>
              <select value={therapistId} onChange={e => setTherapistId(e.target.value)}
                className="border rounded-lg px-3 py-2 text-sm min-w-[160px]">
                {therapists.map(t => (
                  <option key={t.id} value={t.id}>{t.name} ({t.room_name})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">날짜</label>
              <input type="date" value={date} onChange={e => setDate(e.target.value)}
                className="border rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>

          {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

          {data && (
            <>
              <h3 className="font-bold text-gray-800 mb-3">
                {data.therapist_name} 치료사 <span className="text-sm font-normal text-gray-500">({data.room_name})</span>
              </h3>
              {data.slots.length === 0 ? (
                <p className="text-gray-500 text-sm">해당 날짜에 배정된 환자가 없습니다.</p>
              ) : (
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="bg-gray-50 text-gray-600 text-left">
                      <th className="border px-3 py-2">시간</th>
                      <th className="border px-3 py-2">환자</th>
                      <th className="border px-3 py-2">처방코드</th>
                      <th className="border px-3 py-2">치료명</th>
                      <th className="border px-3 py-2">표시</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.slots.map((s, i) => (
                      <tr key={i} className="hover:bg-blue-50">
                        <td className="border px-3 py-2 font-mono">{s.slot_time}~{slotEndTime(s.slot_time)}</td>
                        <td className="border px-3 py-2 font-medium">{s.patient_name}</td>
                        <td className="border px-3 py-2 font-mono text-blue-700">{s.prescription_code}</td>
                        <td className="border px-3 py-2">{s.prescription_name}</td>
                        <td className="border px-3 py-2 font-mono text-indigo-700">{s.label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
