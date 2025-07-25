from .element import Chart, Tap, ArcTap, Hold, Arc
from .model import ChartBpmDescription
from typing import Optional


class BeatNote:
    def __init__(self) -> None:
        self.time_point = 0
        self.duration = 0
        self.divide = -1
        self.beyond_full_note = False
        self.has_dot = False
        self.is_triplet = False
        
    @staticmethod
    def _is_double_equal(a: float, b: float, threshold: float):
        return abs(a - b) <= threshold
    
    # original implementation from https://github.com/Arcaea-Infinity/Aff2Preview/blob/774b759bab250d6043b2bf6d71971c48593d8513/Aff2Preview/AffTools/AffAnalyzer/Note.cs#L45
    def analyze_note(self, timing: int, length: int, bpm: float) -> bool:
        self.time_point = timing
        self.duration = length
        if bpm == 0:
            return False
        threshold = 3.5
        time_full_note = 60 * 1000 * 4 / bpm
        if length > time_full_note:
            self.beyond_full_note = True
            return True
        if BeatNote._is_double_equal(length, time_full_note, threshold):
            self.divide = 1
            return True
        i = 2
        best_dis = length + time_full_note
        any_match = False
        while i <= 64:
            t_len = time_full_note / i
            t_dot_len = t_len * 1.5
            if BeatNote._is_double_equal(length, t_len, threshold) and (not any_match or abs(length - t_len) < best_dis):
                self.divide = i
                self.has_dot = False
                any_match = True
                best_dis = abs(length - t_len)
            if BeatNote._is_double_equal(length, t_dot_len, threshold) and (not any_match or abs(length - t_dot_len) < best_dis):
                self.divide = i
                self.has_dot = True
                any_match = True
                best_dis = abs(length - t_dot_len)
            if i < 4:
                i += 1
            elif i < 28:
                i += 2
            elif i < 32:
                i += 4
            elif i <= 64:
                i += 8
            else:
                i += 1
        if any_match and self.has_dot and self.divide * 2 % 3 == 0:
            self.divide = self.divide * 2 // 3
            self.has_dot = False
        return any_match


def _preprocess_bpm_description(bpm_description: ChartBpmDescription) -> ChartBpmDescription:
    """Preprocess the bpm description segments"""
    result = [x.copy() for x in bpm_description.items]
    result.sort(key=lambda x: x.start_time)
    for i in range(len(result)):
        if i + 1 < len(result):
            next_start = result[i + 1].start_time
        else:
            next_start = 2 ** 63 - 1 # int64 max
        curr_end = result[i].end_time
        if curr_end is None:
            result[i].end_time = next_start
        else:
            result[i].end_time = min(curr_end, next_start) if i + 1 < len(result) else curr_end # can be over int64 max
    desc = bpm_description.copy()
    desc.items = result
    return desc


def _get_override_bpm_by_time(t: int, bpm_description: ChartBpmDescription) -> float | None:
    """Get override bpm from a preprocessed bpm description by time"""
    for item in bpm_description.items:
        end_time = item.end_time
        if end_time is None:
            continue
        if item.start_time <= t < end_time:
            return item.bpm
        if item.start_time > t:
            break
    if bpm_description.base_bpm_override is not None:
        return bpm_description.base_bpm_override
    return None


# original implementation from https://github.com/Arcaea-Infinity/Aff2Preview/blob/774b759bab250d6043b2bf6d71971c48593d8513/Aff2Preview/AffTools/AffAnalyzer/Analyzer.cs#L143
def analyze_notes(chart: Chart, base_bpm: float, bpm_description: Optional[ChartBpmDescription] = None) -> list[BeatNote]:
    time_points: list[int] = []
    bpm_description = _preprocess_bpm_description(bpm_description) if bpm_description else None
    base_bpm_override = bpm_description.base_bpm_override if bpm_description else None
    base_bpm = base_bpm_override or base_bpm
    for arc in chart._connected_arc_list: #TODO Suspective: arcs in timing groups ignored?
        if arc.has_head:
            time_points.append(arc.t1)
    for arc in chart.get_command_list_for_type(Arc, search_in_timing_group=True, exclude_noinput=True):
        if arc.color.value == 3 and arc.t1 == arc.t2 and arc.y1 == arc.y2 and not arc.is_skyline:
            time_points.append(arc.t1)
    for note in chart.get_command_list_for_type(Tap, True, True):
        time_points.append(note.t)
    for note in chart.get_command_list_for_type(Hold, True, True):
        time_points.append(note.t1)
    for note in chart.get_command_list_for_type(ArcTap, True, True):
        time_points.append(note.tn)
    time_points.sort()
    result = []
    fake_note = Tap(0, 0)
    for i in range(len(time_points) - 1):
        delta_time = time_points[i + 1] - time_points[i]
        if delta_time <= 3:
            continue
        fake_note.t = time_points[i]
        curr_bpm_override = _get_override_bpm_by_time(fake_note.t, bpm_description) if bpm_description else None
        curr_bpm = chart._get_note_bpm(fake_note).bpm if curr_bpm_override is None else curr_bpm_override
        note = BeatNote()
        if not note.analyze_note(time_points[i], delta_time, curr_bpm):
            note.analyze_note(time_points[i], delta_time, base_bpm)
        result.append(note)
    return result
