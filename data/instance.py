from dataclasses import dataclass
from typing import List, Dict, Optional

ROOMS = ["101", "102", "103", "104", "105", "106"]
DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
SLOT_START_MINUTES = list(range(8 * 60, 17 * 60 + 10, 50))
MINUTES_PER_credit = 50
FRIDAY_BREAK_START = 12 * 60 + 10
FRIDAY_BREAK_END   = 13 * 60 + 50

def minutes_to_str(m):
    return f"{m // 60:02d}:{m % 60:02d}"

SLOT_STRINGS = [minutes_to_str(m) for m in SLOT_START_MINUTES]

@dataclass
class CourseSession:
    lecturer: str
    course_code: str
    course_name: str
    classes: str
    semester: int
    tipe: str
    credit_per_classes: int
    day: Optional[str] = None
    room: Optional[str] = None
    slot_index: Optional[int] = None

    def end_slot_index(self):
        if self.slot_index is None:
            return None
        return self.slot_index + self.credit_per_classes - 1

    def start_minutes(self):
        if self.slot_index is None:
            return None
        return SLOT_START_MINUTES[self.slot_index]

    def end_minutes(self):
        if self.slot_index is None:
            return None
        return SLOT_START_MINUTES[self.slot_index] + self.credit_per_classes * MINUTES_PER_credit

    def end_str(self):
        return minutes_to_str(self.end_minutes()) if self.end_minutes() else None

    def start_str(self):
        return SLOT_STRINGS[self.slot_index] if self.slot_index is not None else None


def parse_raw_data(raw):
    sessions = []
    for row in raw:
        lecturer, code, name, credit, classes_str, semester, tipe = row
        if tipe == "MKWU":
            klases = ["MKWU"]
        else:
            klases = [k.strip() for k in classes_str.split(",")]

        for k in klases:
            sessions.append(CourseSession(
                lecturer=lecturer,
                course_code=code,
                course_name=name,
                classes=k,
                semester=semester,
                tipe=tipe,
                credit_per_classes=credit,
            ))
    return sessions
