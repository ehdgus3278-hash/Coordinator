TIME_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
]

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

# 처방코드 표시 라벨에 사용하는 접미사 (예: 홍길동1(301), 홍길동M(102))
LABEL_SUFFIX = {
    "MM301": "1",
    "MM302": "2",
    "MM102": "M",
    "MM10204": "T",
}

PRESCRIPTION_MASTER = {
    "MM105":   {"name": "중추신경계치료",  "duration": 30, "room": BRAIN_ROOM, "zones": ["THERAPIST"]},
    "MM301":   {"name": "보행훈련",        "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM302":   {"name": "보행훈련2(임시명)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM102":   {"name": "신경계운동치료(임시명)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM151":   {"name": "중첩치료(임시명)",  "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301", "MM302"]},
    "MM10204": {"name": "보조치료(임시명)",  "duration": 30, "room": BRAIN_ROOM, "zones": ["T"]},
    "MX112": {"name": "작업치료",     "duration": 15, "room": OT_ROOM},
    "MX115": {"name": "인지작업치료", "duration": 30, "room": OT_ROOM},
    "MS201": {"name": "언어치료",     "duration": 30, "room": ST_ROOM},
}

ROOM_MASTER = {
    BRAIN_ROOM: {"beds": len(ROOM_STATIONS[BRAIN_ROOM])},
    OT_ROOM:    {"beds": 4},
    ST_ROOM:    {"beds": 2},
}
