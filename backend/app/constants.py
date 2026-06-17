TIME_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
]

# AM/PM 코드(예: MM301AM/MM301PM)가 배정 가능한 슬롯 범위.
AM_SLOTS = [t for t in TIME_SLOTS if t < "12:00"]
PM_SLOTS = [t for t in TIME_SLOTS if t >= "12:00"]

# 다른 슬롯이 다 찬 뒤에만 채워지는 후순위 타임.
LAST_PRIORITY_SLOTS = {"08:00", "11:30", "16:30"}

BRAIN_ROOM = "뇌재활치료실"
OT_ROOM = "작업치료실"
ST_ROOM = "언어치료실"

# 뇌재활치료실 전용 스테이션(슬롯) 구성.
# zone: "M"(매트) / "B"(자전거) / "T"(틸트) / "THERAPIST"(치료사 1:1 전담 슬롯)
BRAIN_THERAPISTS = ["황병훈", "문승현", "이진용", "김동현"]

ROOM_STATIONS = {
    BRAIN_ROOM: (
        [{"name": f"M{i}", "zone": "M"} for i in range(1, 5)]
        + [{"name": f"B{i}", "zone": "B"} for i in range(1, 3)]
        + [{"name": f"T{i}", "zone": "T"} for i in range(1, 4)]
        + [{"name": name, "zone": "THERAPIST"} for name in BRAIN_THERAPISTS]
    ),
}

# 분배를 위한 "한 타임당 최대 인원" 제한. 물리적 스테이션 수보다 적게 설정하면
# 일부 스테이션은 항상 비워두고 다음 시간대로 자동 분산된다.
# 예: M구역은 M1~M4 4칸이 있지만 한 타임에 최대 3명까지만 배정.
# THERAPIST구역("1:1치료실" = 치료사별 전담 시간)은 4인이 있지만 한 타임 최대 2명까지만 배정.
ZONE_CAPACITY = {
    BRAIN_ROOM: {"M": 3, "B": 1, "T": 2, "THERAPIST": 2},
}

# zone 구분이 없는(번호 베드) 치료실의 한 타임당 최대 인원 제한.
ROOM_CAPACITY_OVERRIDE = {
    OT_ROOM: 2,
    ST_ROOM: 2,
}

# 처방코드 표시 라벨에 사용하는 접미사 (예: 홍길동1(301), 홍길동M(102))
LABEL_SUFFIX = {
    "MM301AM": "1",
    "MM301PM": "1",
    "MM302AM": "2",
    "MM302PM": "2",
    "MM102":   "M",
    "MM10204": "T",
}

# AM/PM 전용 코드. 존 제한은 처방코드가 아닌 환자 프로필의 zone_restriction으로 관리한다.
PRESCRIPTION_MASTER = {
    "MM105AM": {"name": "중추신경계치료(오전)", "duration": 30, "room": BRAIN_ROOM, "zones": ["THERAPIST"], "time_window": "AM"},
    "MM105PM": {"name": "중추신경계치료(오후)", "duration": 30, "room": BRAIN_ROOM, "zones": ["THERAPIST"], "time_window": "PM"},
    "MM301AM": {"name": "보행훈련(오전)",       "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "AM"},
    "MM301PM": {"name": "보행훈련(오후)",       "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "PM"},
    "MM302AM": {"name": "보행훈련2(임시명)(오전)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "AM"},
    "MM302PM": {"name": "보행훈련2(임시명)(오후)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "PM"},
    "MM102":   {"name": "신경계운동치료(임시명)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM151":   {"name": "중첩치료(임시명)",       "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301AM", "MM302AM", "MM301PM", "MM302PM"]},
    "MM151AM": {"name": "중첩치료(임시명)(오전)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301AM", "MM302AM"], "time_window": "AM"},
    "MM151PM": {"name": "중첩치료(임시명)(오후)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301PM", "MM302PM"], "time_window": "PM"},
    "MM10204": {"name": "보조치료(임시명)", "duration": 30, "room": BRAIN_ROOM, "zones": ["T"]},
    "MX112": {"name": "작업치료",     "duration": 15, "room": OT_ROOM},
    "MX115": {"name": "인지작업치료", "duration": 30, "room": OT_ROOM},
    "MS201": {"name": "언어치료",     "duration": 30, "room": ST_ROOM},
}

ROOM_MASTER = {
    BRAIN_ROOM: {"beds": len(ROOM_STATIONS[BRAIN_ROOM])},
    OT_ROOM:    {"beds": 4},
    ST_ROOM:    {"beds": 2},
}
