from typing import List, Optional, Union, Tuple
from pydantic import BaseModel

# ==============================
# Metadata Lines
# ==============================

class Composer(BaseModel):
    composer: str

class Piece(BaseModel):
    piece: str

class Analyst(BaseModel):
    analyst: str

class Proofreader(BaseModel):
    proofreader: str

class Movement(BaseModel):
    movement: str

class TimeSignature(BaseModel):
    numerator: int
    denominator: int

class KeySignature(BaseModel):
    key_signature: str

class MinorMode(BaseModel):
    minor_mode: str

# A metadata line is one of the above types.
MetadataLine = Union[
    Composer,
    Piece,
    Analyst,
    Proofreader,
    Movement,
    TimeSignature,
    KeySignature,
    MinorMode,
]

# ==============================
# Chord-related models
# ==============================

class Key(BaseModel):
    key: str

class PitchClassesAndRomanNumeral(BaseModel):
    pitch_classes: List[int]
    roman_numeral: str
    key_name: str

class Chord(BaseModel):
    # beat_chord: WS BEAT_INDICATOR (WS key)? WS chord
    beat: float
    key: Optional[str] = None
    chord: str


# In a measure line we have a sequence of beat "items" which can be a beat_chord OR a key_change:
BeatItem = Union[Chord, Key]

# ==============================
# Statement Lines
# ==============================


class BeatAndPitchClasses(BaseModel):
    beat: float
    pitch_classes: List[int]
    roman_numeral: str
    key_name: str

class Measure(BaseModel):
    # measure_line: MEASURE_INDICATOR (chord_beat_1)? (beat_chord | key_change)+ PHRASE_BOUNDARY? NEWLINE
    measure_number: int
    beat_items: List[BeatItem]
    phrase_boundary: Optional[str] = None

class MeasureRange(BaseModel):
    # measure_range: MEASURE_INDICATOR ( "-" MEASURE_INDICATOR )+
    measures: List[str]

class Repeat(BaseModel):
    # repeat_line: measure_range WS "=" WS measure_range NEWLINE
    start_range: MeasureRange
    equals: str
    end_range: MeasureRange

class Note(BaseModel):
    # note: NOTELETTER ACCIDENTAL?
    noteletter: str
    accidental: Optional[str] = None

class PedalEntry(BaseModel):
    # pedal_entry: MEASURE_INDICATOR WS BEAT_INDICATOR
    measure_indicator: str
    beat_indicator: str

class Pedal(BaseModel):
    # pedal_line: "Pedal:" WS note WS pedal_entries NEWLINE
    note: Note
    pedal_entries: List[PedalEntry]

class Form(BaseModel):
    # form_line: "Form:" WS REST_LINE NEWLINE
    form: str

class Comment(BaseModel):
    # note_line: "Note:" WS REST_LINE NEWLINE
    comment: str

# A statement line can be any of the following:
StatementLine = Union[
    Measure,
    Repeat,
    Pedal,
    Form,
    Comment,
]

Line = Union[MetadataLine, StatementLine]

# ==============================
# Top-level Document
# ==============================

class NoteItem(BaseModel):
    time: float
    duration: float
    chord: str
    key: str
    pitches: Optional[List[int]] = None

class RomanTextDocument(BaseModel):
    lines: List[Line]

    @property
    def chords(self) -> List[Note]:
        def bar_duration_in_quarters(time_signature: Tuple[int, int]) -> int:
            return 4 * time_signature[0] / time_signature[1]
        
        def beat_to_quarter(beat: float, time_signature: Tuple[int, int]) -> float:
            return 4 * (beat - 1) / time_signature[1]
        
        results = []
        bar_start_time = 0 # In quarter (not in beat !)
        current_bar_index = 0
        current_time_signature = (4, 4)
        current_key = None
        for line in self.lines:
            if isinstance(line, Measure):
                delta_bar = line.measure_number - current_bar_index
                current_bar_index = line.measure_number
                for beat_item in line.beat_items:
                    beat_start_time = beat_to_quarter(beat_item.beat, current_time_signature)
                    duration = 0
                    if beat_item.key is not None:
                        current_key = beat_item.key
                    results.append(NoteItem(time=beat_start_time+bar_start_time, duration=duration, 
                                                   chord=beat_item.chord,
                                                   key=current_key))
                bar_start_time += delta_bar * bar_duration_in_quarters(current_time_signature)
            elif isinstance(line, TimeSignature):
                print(line.numerator, line.denominator)
                current_time_signature = (line.numerator, line.denominator)

        # Fill the durations (using delta between next time)
        for i in range(len(results)-1):
            results[i].duration = results[i+1].time - results[i].time
        results[-1].duration = bar_start_time - results[-1].time
        return results