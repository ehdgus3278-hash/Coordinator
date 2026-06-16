import { useState, useEffect } from 'react'
import { api, slotEndTime, today } from '../api'

export default function PatientScheduleView() {
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const [date, setDate] = useState(today())
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const loadPatients = () => api.patients.list().then(r => { setPatients(r.data); return r.data })

  useEffect(() => {
    loadPatients().then(list => {
      if (list.length > 0) setPatientId(String(list[0].id))
    })
  }, [])

  useEffect(() => {
    if (!patientId) { setData(null); return }
    setError('')
    api.schedules.forPatient(patientId, date)
      .then(r => setData(r.data))
      .catch(e => { setError(e.response?.data?.detail || '조회 실패'); setData(null) })
  }, [patientId, date])

  const handleDelete = async () => {
    if (!patientId) return
    const patient = patients.find(p => String(p.id) === String(patientId))
    if (!window.confirm(`${patient?.name ?? '이 환자'}를 삭제하시겠습니까?\n모든 스케줄에서 함께 삭제되며 되돌릴 수 없습니다.`)) return
    setDeleting(true)
    setError('')
    try {
      await api.patients.remove(patientId)
      const list = await loadPatients()
      setPatientId(list.length > 0 ? String(list[0].id) : '')
      setData(null)
    } catch (e) {
      setError(e.response?.data?.detail || '삭제 중 오류가 발생했습니다.')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-bold text-gray-800 mb-6">환자별 시간표</h2>

      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex gap-4 mb-6 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">환자 선택</label>
            <select value={patientId} onChange={e => setPatientId(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm min-w-[160px]">
              <option value="">선택하세요</option>
              {patients.map(p => (
                <option key={p.id} value={p.id}>{p.name} (#{p.id})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">날짜</label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button onClick={handleDelete} disabled={!patientId || deleting}
            className="px-3 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed">
            {deleting ? '삭제 중...' : '환자 삭제(퇴원)'}
          </button>
        </div>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        {data && (
          <>
            <h3 className="font-bold text-gray-800 mb-3">{data.patient_name}님의 시간표</h3>
            {data.schedules.length === 0 ? (
              <p className="text-gray-500 text-sm">해당 날짜에 배정된 스케줄이 없습니다.</p>
            ) : (
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 text-left">
                    <th className="border px-3 py-2">시간</th>
                    <th className="border px-3 py-2">처방코드</th>
                    <th className="border px-3 py-2">치료명</th>
                    <th className="border px-3 py-2">치료실</th>
                    <th className="border px-3 py-2">스테이션</th>
                    <th className="border px-3 py-2">표시</th>
                  </tr>
                </thead>
                <tbody>
                  {data.schedules.map(s => (
                    <tr key={s.id} className="hover:bg-blue-50">
                      <td className="border px-3 py-2 font-mono">{s.slot_time}~{slotEndTime(s.slot_time)}</td>
                      <td className="border px-3 py-2 font-mono text-blue-700">
                        {s.prescription_code}{s.overlay_code ? `+${s.overlay_code}` : ''}
                      </td>
                      <td className="border px-3 py-2">
                        {s.prescription_name}{s.overlay_name ? ` + ${s.overlay_name}` : ''}
                      </td>
                      <td className="border px-3 py-2">{s.room_name}</td>
                      <td className="border px-3 py-2">{s.station}</td>
                      <td className="border px-3 py-2 font-mono text-indigo-700">{s.label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  )
}
