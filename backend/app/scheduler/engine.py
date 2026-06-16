import math
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from ..constants import LABEL_SUFFIX, TIME_SLOTS


def _slot_index(time_str: str) -> int:
    try:
        return TIME_SLOTS.index(time_str)
    except ValueError:
        return -1


def _first_slot_ge(time_str: str) -> int:
    for i, t in enumerate(TIME_SLOTS):
        if t >= time_str:
            return i
    return len(TIME_SLOTS)


def _last_slot_lt(time_str: str) -> int:
    result = -1
    for i, t in enumerate(TIME_SLOTS):
        if t < time_str:
            result = i
    return result


def _slots_needed(duration_minutes: int) -> int:
    return max(1, math.ceil(duration_minutes / 30))


def make_label(patient_name: str, code: str, overlay_code: Optional[str] = None) -> str:
    """예: 홍길동1(301), 홍길동2(302), 홍길동1F(301+151), 홍길동M(102), 홍길동T(10204)."""
    suffix = LABEL_SUFFIX.get(code)
    if suffix is None:
        return patient_name
    code_num = code[2:] if code.startswith("MM") else code
    if overlay_code:
        overlay_num = overlay_code[2:] if overlay_code.startswith("MM") else overlay_code
        return f"{patient_name}{suffix}F({code_num}+{overlay_num})"
    return f"{patient_name}{suffix}({code_num})"


def room_station_list(room_name: str, room_stations_map: Dict, room_capacity_map: Dict) -> List[Dict]:
    """해당 치료실의 스테이션 목록을 반환. 명명된 스테이션이 없으면 번호 베드를 합성한다."""
    stations = room_stations_map.get(room_name)
    if stations:
        return stations
    beds = room_capacity_map.get(room_name, 1)
    return [{"name": str(i), "zone": None} for i in range(1, beds + 1)]


def _eligible_station_names(zones: Optional[List[str]], stations: List[Dict]) -> List[str]:
    if not zones:
        return [s["name"] for s in stations]
    return [s["name"] for s in stations if s.get("zone") in zones]


def _build_units(
    orders: List[str], prescription_map: Dict, warnings: List[str]
) -> List[Dict]:
    """
    중첩 사용 코드(예: MM151)를 대상 코드(예: MM301/MM302)와 짝지어
    하나의 스케줄링 단위로 묶는다. 짝을 찾지 못하면 경고만 남기고 버린다.
    반환: [{"code", "overlay", "rx"}, ...] (원래 순서 유지)
    """
    n = len(orders)
    consumed = [False] * n
    overlay_for: List[Optional[str]] = [None] * n

    for i, code in enumerate(orders):
        rx = prescription_map.get(code)
        if not rx or not rx.get("overlay_targets"):
            continue
        targets = rx["overlay_targets"]
        paired = False
        for j, other in enumerate(orders):
            if j == i or consumed[j] or overlay_for[j] is not None:
                continue
            if other in targets:
                overlay_for[j] = code
                consumed[i] = True
                paired = True
                break
        if not paired:
            warnings.append(f"{code}: 중첩 대상({'/'.join(targets)})이 없어 배정하지 못했습니다.")
            consumed[i] = True

    units = []
    for i, code in enumerate(orders):
        if consumed[i]:
            continue
        rx = prescription_map.get(code)
        if not rx:
            continue
        units.append({"code": code, "overlay": overlay_for[i], "rx": rx})
    return units


def _group_units_by_room(units: List[Dict]) -> List[Tuple[str, List[Dict]]]:
    room_first_seen: Dict[str, int] = {}
    room_groups: Dict[str, List[Dict]] = {}

    for u in units:
        room = u["rx"]["room_name"]
        if room not in room_groups:
            room_first_seen[room] = len(room_first_seen)
            room_groups[room] = []
        room_groups[room].append(u)

    sorted_rooms = sorted(room_groups, key=lambda r: room_first_seen[r])
    return [(r, room_groups[r]) for r in sorted_rooms]


def schedule_patient(
    patient_name: str,
    available_start: str,
    available_end: str,
    orders: List[str],
    prescription_map: Dict,
    room_capacity_map: Dict,
    existing_schedules: List[Dict],
    target_date: date,
    room_stations_map: Optional[Dict] = None,
) -> Tuple[List[Dict], List[str]]:
    """
    Greedy scheduler implementing the four priorities:
    1. Group same-room orders together
    2. Minimize room transitions
    3. Minimize waiting time (earliest consecutive slot)
    4. Respect room/station capacity

    중첩 사용 코드(MM151 등)는 대상 코드와 같은 스테이션·슬롯을 공유하며 별도 슬롯을 소비하지 않는다.

    Returns (schedule_items, warnings).
    """
    room_stations_map = room_stations_map or {}
    results: List[Dict] = []
    warnings: List[str] = []

    # room -> slot -> 사용 중인 스테이션 이름 집합
    slot_stations: Dict[str, Dict[str, Set[str]]] = {
        room: {slot: set() for slot in TIME_SLOTS} for room in room_capacity_map
    }
    for s in existing_schedules:
        room, slot, station = s["room_name"], s["slot_time"], s.get("station")
        if station and room in slot_stations and slot in slot_stations[room]:
            slot_stations[room][slot].add(station)

    start_idx = _first_slot_ge(available_start)
    end_idx = _last_slot_lt(available_end)

    if start_idx > end_idx or end_idx < 0:
        warnings.append("배정 가능한 시간 슬롯이 없습니다.")
        return results, warnings

    unknown = [o for o in orders if o not in prescription_map]
    for o in unknown:
        warnings.append(f"알 수 없는 처방코드: {o}")

    units = _build_units(orders, prescription_map, warnings)
    room_groups = _group_units_by_room(units)
    current_idx = start_idx

    for room_name, room_units in room_groups:
        all_stations = room_station_list(room_name, room_stations_map, room_capacity_map)

        for unit in room_units:
            code, overlay_code, rx = unit["code"], unit["overlay"], unit["rx"]
            n_slots = _slots_needed(rx["duration"])
            eligible = _eligible_station_names(rx.get("zones"), all_stations)

            if not eligible:
                warnings.append(f"{code}({rx['name']}): 배정 가능한 스테이션이 없습니다.")
                continue

            assigned = False
            for i in range(current_idx, len(TIME_SLOTS)):
                if i + n_slots - 1 > end_idx:
                    break

                # Priority 4: 필요한 모든 슬롯에서 해당 zone 의 빈 스테이션이 있는지 확인
                occupied: Set[str] = set()
                for j in range(n_slots):
                    occupied |= slot_stations.get(room_name, {}).get(TIME_SLOTS[i + j], set())

                # 이번 배정 실행 중 이미 점유된 스테이션도 고려
                for res in results:
                    if res["room_name"] != room_name or not res.get("station"):
                        continue
                    res_i = _slot_index(res["slot_time"])
                    res_n = _slots_needed(
                        prescription_map.get(res["prescription_code"], {}).get("duration", 30)
                    )
                    if res_i < i + n_slots and res_i + res_n > i:
                        occupied.add(res["station"])

                station = next((nm for nm in eligible if nm not in occupied), None)
                if station is None:
                    continue

                overlay_name = (
                    prescription_map.get(overlay_code, {}).get("name") if overlay_code else None
                )
                item = {
                    "prescription_code": code,
                    "prescription_name": rx["name"],
                    "overlay_code": overlay_code,
                    "overlay_name": overlay_name,
                    "room_name": room_name,
                    "slot_time": TIME_SLOTS[i],
                    "station": station,
                    "label": make_label(patient_name, code, overlay_code),
                }
                results.append(item)

                for j in range(n_slots):
                    slot_stations.setdefault(room_name, {}).setdefault(TIME_SLOTS[i + j], set()).add(station)

                current_idx = i + n_slots
                assigned = True
                break

            if not assigned:
                warnings.append(f"{code}({rx['name']}): 가용 슬롯이 없어 배정하지 못했습니다.")

    return results, warnings
