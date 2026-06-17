import math
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from ..constants import LABEL_SUFFIX, TIME_SLOTS, ZONE_CAPACITY, ROOM_CAPACITY_OVERRIDE, AM_SLOTS, PM_SLOTS


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


def _pool_cap(room_name: str, zone: Optional[str]) -> Optional[int]:
    """분배용 '한 타임당 최대 인원' 제한을 반환. 제한이 없으면 None(물리적 스테이션 수만 적용)."""
    if zone and room_name in ZONE_CAPACITY and zone in ZONE_CAPACITY[room_name]:
        return ZONE_CAPACITY[room_name][zone]
    if not zone and room_name in ROOM_CAPACITY_OVERRIDE:
        return ROOM_CAPACITY_OVERRIDE[room_name]
    return None


def _window_slots(time_window: Optional[str]) -> Optional[Set[str]]:
    """AM/PM 코드가 배정 가능한 슬롯 집합을 반환. 시간대 제한이 없으면 None."""
    if time_window == "AM":
        return set(AM_SLOTS)
    if time_window == "PM":
        return set(PM_SLOTS)
    return None


def _zone_count(occ: Set[str], zone: Optional[str], station_zone: Dict[str, Optional[str]]) -> int:
    """주어진 점유 집합 중 같은 zone(분배 풀)에 속하는 개수. zone이 없으면 전체 점유 수."""
    return sum(1 for s in occ if station_zone.get(s) == zone) if zone else len(occ)


def _build_units(
    orders: List[str], prescription_map: Dict, warnings: List[str]
) -> List[Dict]:
    """
    중첩 사용 코드(예: MM151AM)를 대상 코드(예: MM301AM/MM302AM)와 짝지어
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
    3. Load-balance across the entire available time range (least-occupied slot wins;
       earliest slot is only a tie-breaker), subject to AM/PM time-window restrictions
    4. Respect room/station capacity

    중첩 사용 코드(MM151AM/PM 등)는 대상 코드와 같은 스테이션·슬롯을 공유하며 별도 슬롯을 소비하지 않는다.

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
        station_zone = {s["name"]: s.get("zone") for s in all_stations}

        for unit in room_units:
            code, overlay_code, rx = unit["code"], unit["overlay"], unit["rx"]
            n_slots = _slots_needed(rx["duration"])
            eligible = _eligible_station_names(rx.get("zones"), all_stations)
            window = _window_slots(rx.get("time_window"))

            if not eligible:
                warnings.append(f"{code}({rx['name']}): 배정 가능한 스테이션이 없습니다.")
                continue

            # Priority 4: 전체 가능 시간대를 훑어, 분배 한도를 지키면서 가장 한산한
            # (점유 인원이 가장 적은) 슬롯을 고른다 (로드밸런싱). current_idx는 하한선으로만 사용.
            # Compute total daily usage per eligible station (column load-balancing)
            def _station_usage(name: str) -> int:
                day_cnt = sum(1 for slot in TIME_SLOTS if name in slot_stations.get(room_name, {}).get(slot, set()))
                res_cnt = sum(1 for res in results if res["room_name"] == room_name and res.get("station") == name)
                return day_cnt + res_cnt

            station_usage = {nm: _station_usage(nm) for nm in eligible}

            best: Optional[Tuple[int, int, str, int]] = None  # (load, slot_idx, station, station_usage)
            for i in range(current_idx, len(TIME_SLOTS)):
                if i + n_slots - 1 > end_idx:
                    break
                if window is not None and any(TIME_SLOTS[i + j] not in window for j in range(n_slots)):
                    continue

                slot_occupied: List[Set[str]] = []
                for j in range(n_slots):
                    slot = TIME_SLOTS[i + j]
                    occ = set(slot_stations.get(room_name, {}).get(slot, set()))

                    # 이번 배정 실행 중 이미 점유된 스테이션도 고려
                    for res in results:
                        if res["room_name"] != room_name or not res.get("station"):
                            continue
                        res_i = _slot_index(res["slot_time"])
                        res_n = _slots_needed(
                            prescription_map.get(res["prescription_code"], {}).get("duration", 30)
                        )
                        if res_i <= i + j < res_i + res_n:
                            occ.add(res["station"])

                    slot_occupied.append(occ)

                def _feasible(name: str) -> bool:
                    zone = station_zone.get(name)
                    cap = _pool_cap(room_name, zone)
                    for occ in slot_occupied:
                        if name in occ:
                            return False
                        if cap is not None and _zone_count(occ, zone, station_zone) >= cap:
                            return False
                    return True

                feasible_stns = [nm for nm in eligible if _feasible(nm)]
                if not feasible_stns:
                    continue

                station = min(feasible_stns, key=lambda nm: station_usage[nm])
                zone = station_zone.get(station)
                load = max(_zone_count(occ, zone, station_zone) for occ in slot_occupied)
                stn_u = station_usage[station]
                if best is None or (load, stn_u) < (best[0], best[3]):
                    best = (load, i, station, stn_u)

            if best is None:
                if window is not None and not any(
                    i + n_slots - 1 <= end_idx
                    and all(TIME_SLOTS[i + j] in window for j in range(n_slots))
                    for i in range(current_idx, end_idx + 1)
                ):
                    w = "AM" if window == set(AM_SLOTS) else "PM"
                    s_t = TIME_SLOTS[current_idx] if current_idx < len(TIME_SLOTS) else "?"
                    e_t = TIME_SLOTS[end_idx] if 0 <= end_idx < len(TIME_SLOTS) else "?"
                    warnings.append(
                        f"{code}({rx['name']}): {w} 전용 코드이지만 "
                        f"환자의 가능 시간({s_t}~{e_t})에 {w} 슬롯이 없습니다."
                    )
                else:
                    warnings.append(f"{code}({rx['name']}): 가용 슬롯이 없어 배정하지 못했습니다.")
                continue

            _, i, station, _ = best
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

    return results, warnings
