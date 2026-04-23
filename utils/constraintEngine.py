from typing import List, Dict
from data.instance import CourseSession, SLOT_START_MINUTES, FRIDAY_BREAK_END, FRIDAY_BREAK_START, MINUTES_PER_credit, DAYS

class ConstraintEngine:

    PENALTY_TUESDAY_CLASS        = 100
    PENALTY_SEM24_MONDAY         = 150
    PENALTY_SEM24_TUESDAY        = 150
    PENALTY_FRIDAY_BREAK         = 200
    PENALTY_MKWU_NOT_MONDAY      = 200
    PENALTY_LECTURER_CONFLICT    = 100
    PENALTY_ROOM_CONFLICT        = 100
    PENALTY_CLASS_CONFLICT       = 100
    PENALTY_SLOT_OUT_OF_BOUNDS   = 100

    def evaluate(self, chromosome: List[CourseSession]) -> float:
        penalty = 0.0
        penalty += self._slot_bounds(chromosome)
        penalty += self._time_conflicts(chromosome)
        penalty += self._mkwu_monday(chromosome)
        penalty += self._no_tuesday(chromosome)
        penalty += self._sem24_restrictions(chromosome)
        penalty += self._friday_break(chromosome)
        return penalty


    def violations_for_session(self, target: CourseSession, chrom: List[CourseSession]) -> List[str]:
        violations = []

        if target.slot_index is None or target.day is None or target.room is None:
            violations.append("SLOT_UNASSIGNED")
        else:
            if target.end_slot_index() >= len(SLOT_START_MINUTES):
                violations.append("OUT_OF_BOUNDS")

        if target.tipe == "MKWU" and target.day != "Senin":
            violations.append("MKWU_NOT_MONDAY")

        if target.day == "Selasa":
            violations.append("TUESDAY_CLASS")

        if target.semester in (2, 4):
            if target.day == "Senin":
                violations.append("SEM24_MON")
            if target.day == "Selasa":
                violations.append("SEM24_TUE")

        if target.day == "Jumat" and target.slot_index is not None:
            s_min = target.start_minutes()
            e_min = target.end_minutes()
            if s_min < FRIDAY_BREAK_END and e_min > FRIDAY_BREAK_START:
                violations.append("FRIDAY_BREAK")

        for other in chrom:
            if other is target:
                continue
            if other.day != target.day:
                continue
            if not self._overlaps(target, other):
                continue

            if target.lecturer == other.lecturer:
                violations.append("LECTURER_CONFLICT")
            if target.room == other.room:
                violations.append("ROOM_CONFLICT")
            if (
                    target.classes == other.classes and
                    target.semester == other.semester and
                    target.classes != "MKWU"
                ):
                    violations.append("CLASS_CONFLICT")

        return violations

    def _slot_bounds(self, chrom):
        p = 0
        for s in chrom:
            if s.slot_index is None or s.day is None or s.room is None:
                p += self.PENALTY_SLOT_OUT_OF_BOUNDS
                continue
            end_idx = s.end_slot_index()
            if end_idx >= len(SLOT_START_MINUTES):
                p += self.PENALTY_SLOT_OUT_OF_BOUNDS
        return p

    def _time_conflicts(self, chrom):
        p = 0
        by_day: Dict[str, List[CourseSession]] = {}
        for s in chrom:
            if s.day:
                by_day.setdefault(s.day, []).append(s)

        for day, sessions in by_day.items():
            n = len(sessions)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = sessions[i], sessions[j]
                    if not self._overlaps(a, b):
                        continue
                    if a.lecturer == b.lecturer:
                        p += self.PENALTY_LECTURER_CONFLICT
                    if a.room == b.room:
                        p += self.PENALTY_ROOM_CONFLICT
                    if (
                          a.classes == b.classes and
                          a.semester == b.semester and
                          a.classes != "MKWU"
                       ):
                        p += self.PENALTY_CLASS_CONFLICT
        return p

    def _overlaps(self, a: CourseSession, b: CourseSession) -> bool:
        if a.slot_index is None or b.slot_index is None:
            return False
        a_start, a_end = a.slot_index, a.end_slot_index()
        b_start, b_end = b.slot_index, b.end_slot_index()
        return not (a_end < b_start or b_end < a_start)

    def _mkwu_monday(self, chrom):
        p = 0
        for s in chrom:
            if s.tipe == "MKWU" and s.day != "Senin":
                p += self.PENALTY_MKWU_NOT_MONDAY
        return p

    def _no_tuesday(self, chrom):
        p = 0
        for s in chrom:
            if s.day == "Selasa":
                p += self.PENALTY_TUESDAY_CLASS
        return p

    def _sem24_restrictions(self, chrom):
        p = 0
        for s in chrom:
            if s.semester in (2, 4):
                if s.day == "Senin":
                    p += self.PENALTY_SEM24_MONDAY
                if s.day == "Selasa":
                    p += self.PENALTY_SEM24_TUESDAY
        return p

    def _friday_break(self, chrom):
        p = 0
        for s in chrom:
            if s.day == "Jumat" and s.slot_index is not None:
                s_min = s.start_minutes()
                e_min = s.end_minutes()
                if s_min < FRIDAY_BREAK_END and e_min > FRIDAY_BREAK_START:
                    p += self.PENALTY_FRIDAY_BREAK
        return p

# def allowed_days(session: CourseSession) -> List[str]:
#     if session.tipe == "MKWU":
#         return ["Senin"]
#     if session.semester in (2, 4):
#         return ["Rabu", "Kamis", "Jumat"]
#     return ["Senin", "Rabu", "Kamis", "Jumat"]

def allowed_slots(session: CourseSession, day: str) -> List[int]:
    """Return valid start slot indices for this session on given day."""
    max_start = len(SLOT_START_MINUTES) - session.credit_per_classes
    candidates = list(range(0, max_start + 1))
    if day == "Jumat":
        valid = []
        for idx in candidates:
            s_min = SLOT_START_MINUTES[idx]
            e_min = s_min + session.credit_per_classes * MINUTES_PER_credit
            if not (s_min < FRIDAY_BREAK_END and e_min > FRIDAY_BREAK_START):
                valid.append(idx)
        return valid if valid else candidates
    return candidates

# def biased_day(session: CourseSession, bias_prob=0.8):
#     valid = allowed_days(session)
#     if random.random() < bias_prob:
#         return random.choice(valid)
#     return random.choice(DAYS)