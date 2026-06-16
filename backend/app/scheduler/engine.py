import math
from datetime import date
from typing import Dict, List, Set, Tuple

from ..constants import TIME_SLOTS


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


def _group_by_room(
    orders: List[str], prescription_map: Dict
) -> List[Tuple[str, List[str]]]:
    """
    Stable-sort orders so same-room codes are consecutive,
    preserving first-appearance order of each room.
    """
    room_first_seen: Dict[str, int] = {}
    room_groups: Dict[str, List[str]] = {}

    for order in orders:
        if order not in prescription_map:
            continue
        room = prescription_map[order]["room_name"]
        if room not in room_groups:
            room_first_seen[room] = len(room_first_seen)
            room_groups[room] = []
        room_groups[room].append(order)

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
) -> Tuple[List[Dict], List[str]]:
    """
    Greedy scheduler implementing the four priorities:
    1. Group same-room orders together
    2. Minimize room transitions
    3. Minimize waiting time (earliest consecutive slot)
    4. Respect room capacity

    Returns (schedule_items, warnings).
    """
    results: List[Dict] = []
    warnings: List[str] = []

    # Build per-room bed-occupancy: room -> slot -> set of used bed numbers
    slot_beds: Dict[str, Dict[str, Set[int]]] = {
        room: {slot: set() for slot in TIME_SLOTS}
        for room in room_capacity_map
    }
    for s in existing_schedules:
        room, slot, bed = s["room_name"], s["slot_time"], s.get("bed_number", 1)
        if room in slot_beds and slot in slot_beds[room]:
            slot_beds[room][slot].add(bed)

    start_idx = _first_slot_ge(available_start)
    end_idx = _last_slot_lt(available_end)

    if start_idx > end_idx or end_idx < 0:
        warnings.append("배정 가능한 시간 슬롯이 없습니다.")
        return results, warnings

    unknown = [o for o in orders if o not in prescription_map]
    for o in unknown:
        warnings.append(f"알 수 없는 처방코드: {o}")

    room_groups = _group_by_room(orders, prescription_map)
    current_idx = start_idx

    for _room, room_orders in room_groups:
        for order_code in room_orders:
            rx = prescription_map[order_code]
            n_slots = _slots_needed(rx["duration"])
            room_name = rx["room_name"]
            capacity = room_capacity_map.get(room_name, 1)

            assigned = False
            for i in range(current_idx, len(TIME_SLOTS)):
                if i + n_slots - 1 > end_idx:
                    break

                # Priority 4: check capacity at every needed slot
                full = False
                for j in range(n_slots):
                    if len(slot_beds.get(room_name, {}).get(TIME_SLOTS[i + j], set())) >= capacity:
                        full = True
                        break
                if full:
                    continue

                # Find the lowest-numbered free bed across all needed slots
                occupied: Set[int] = set()
                for j in range(n_slots):
                    occupied |= slot_beds.get(room_name, {}).get(TIME_SLOTS[i + j], set())

                # Also count beds already committed in this scheduling run
                for res in results:
                    if res["room_name"] != room_name or not res.get("bed_number"):
                        continue
                    res_i = _slot_index(res["slot_time"])
                    res_n = _slots_needed(
                        prescription_map.get(res["prescription_code"], {}).get("duration", 30)
                    )
                    if res_i < i + n_slots and res_i + res_n > i:
                        occupied.add(res["bed_number"])

                bed = next((b for b in range(1, capacity + 1) if b not in occupied), None)
                if bed is None:
                    continue

                item = {
                    "prescription_code": order_code,
                    "prescription_name": rx["name"],
                    "room_name": room_name,
                    "slot_time": TIME_SLOTS[i],
                    "bed_number": bed,
                }
                results.append(item)

                for j in range(n_slots):
                    slot_beds.setdefault(room_name, {}).setdefault(TIME_SLOTS[i + j], set()).add(bed)

                current_idx = i + n_slots
                assigned = True
                break

            if not assigned:
                warnings.append(f"{order_code}({rx['name']}): 가용 슬롯이 없어 배정하지 못했습니다.")

    return results, warnings
