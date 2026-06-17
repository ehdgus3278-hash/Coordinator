TIME_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
]

# AM/PM 코드(예: MM301AM/MM301PM)가 배정 가능한 슬롯 범위.
AM_SLOTS = [t for t in TIME_SLOTS if t < "12:00"]
PM_SLOTS = [t for t in TIME_SLOTS if t >= "12:00"]

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
    "MM301":    "1",
    "MM301AM":  "1",
    "MM301PM":  "1",
    "MM301B":   "1",
    "MM301BAM": "1",
    "MM301BPM": "1",
    "MM302":    "2",
    "MM302AM":  "2",
    "MM302PM":  "2",
    "MM302B":   "2",
    "MM302BAM": "2",
    "MM302BPM": "2",
    "MM102":  "M",
    "MM102B": "M",
    "MM10204": "T",
}

# 기본 코드(시간 무관)와 AM/PM 전용 코드, B존 전용 코드가 함께 존재한다.
# 기본 코드: 오전·오후 관계없이 환자 가능 시간에 자동 배정.
# AM/PM 코드: 해당 시간대에만 배정.
# B코드: 자전거(B1/B2) 스테이션에만 배정 (기능 수준이 높은 환자).
PRESCRIPTION_MASTER = {
    "MM105":   {"name": "중추신경계치료",         "duration": 30, "room": BRAIN_ROOM, "zones": ["THERAPIST"]},
    "MM105AM": {"name": "중추신경계치료(오전)",    "duration": 30, "room": BRAIN_ROOM, "zones": ["THERAPIST"], "time_window": "AM"},
    "MM105PM": {"name": "중추신경계치료(오후)",    "duration": 30, "room": BRAIN_ROOM, "zones": ["THERAPIST"], "time_window": "PM"},
    "MM301":    {"name": "보행훈련",               "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM301AM":  {"name": "보행훈련(오전)",          "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "AM"},
    "MM301PM":  {"name": "보행훈련(오후)",          "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "PM"},
    "MM301B":   {"name": "보행훈련(B존)",           "duration": 30, "room": BRAIN_ROOM, "zones": ["B"]},
    "MM301BAM": {"name": "보행훈련(B존)(오전)",     "duration": 30, "room": BRAIN_ROOM, "zones": ["B"], "time_window": "AM"},
    "MM301BPM": {"name": "보행훈련(B존)(오후)",     "duration": 30, "room": BRAIN_ROOM, "zones": ["B"], "time_window": "PM"},
    "MM302":    {"name": "보행훈련2(임시명)",        "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM302AM":  {"name": "보행훈련2(임시명)(오전)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "AM"},
    "MM302PM":  {"name": "보행훈련2(임시명)(오후)", "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"], "time_window": "PM"},
    "MM302B":   {"name": "보행훈련2(임시명)(B존)",  "duration": 30, "room": BRAIN_ROOM, "zones": ["B"]},
    "MM302BAM": {"name": "보행훈련2(임시명)(B존)(오전)", "duration": 30, "room": BRAIN_ROOM, "zones": ["B"], "time_window": "AM"},
    "MM302BPM": {"name": "보행훈련2(임시명)(B존)(오후)", "duration": 30, "room": BRAIN_ROOM, "zones": ["B"], "time_window": "PM"},
    "MM102":   {"name": "신경계운동치료(임시명)",        "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"]},
    "MM102B":  {"name": "신경계운동치료(임시명)(B존)",   "duration": 30, "room": BRAIN_ROOM, "zones": ["B"]},
    "MM151":   {"name": "중첩치료(임시명)",              "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301", "MM302"]},
    "MM151AM": {"name": "중첩치료(임시명)(오전)",        "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301AM", "MM302AM"], "time_window": "AM"},
    "MM151PM": {"name": "중첩치료(임시명)(오후)",        "duration": 30, "room": BRAIN_ROOM, "zones": ["M", "B", "T"],
                "overlay_targets": ["MM301PM", "MM302PM"], "time_window": "PM"},
    "MM151B":   {"name": "중첩치료(임시명)(B존)",        "duration": 30, "room": BRAIN_ROOM, "zones": ["B"],
                 "overlay_targets": ["MM301B", "MM302B"]},
    "MM151BAM": {"name": "중첩치료(임시명)(B존)(오전)",  "duration": 30, "room": BRAIN_ROOM, "zones": ["B"],
                 "overlay_targets": ["MM301BAM", "MM302BAM"], "time_window": "AM"},
    "MM151BPM": {"name": "중첩치료(임시명)(B존)(오후)",  "duration": 30, "room": BRAIN_ROOM, "zones": ["B"],
                 "overlay_targets": ["MM301BPM", "MM302BPM"], "time_window": "PM"},
    "MM10204": {"name": "보조치료(임시명)",              "duration": 30, "room": BRAIN_ROOM, "zones": ["T"]},
    "MX112": {"name": "작업치료",     "duration": 15, "room": OT_ROOM},
    "MX115": {"name": "인지작업치료", "duration": 30, "room": OT_ROOM},
    "MS201": {"name": "언어치료",     "duration": 30, "room": ST_ROOM},
}

ROOM_MASTER = {
    BRAIN_ROOM: {"beds": len(ROOM_STATIONS[BRAIN_ROOM])},
    OT_ROOM:    {"beds": 4},
    ST_ROOM:    {"beds": 2},
}
