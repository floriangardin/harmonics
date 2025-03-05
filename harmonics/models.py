from typing import List, Optional, Union, Tuple, Any, Dict, Set

from pydantic import BaseModel
from .notes_utils import getPitchFromIntervalFromMinimallyModifiedScale

# ==============================
# Melody Lines
# ==============================


class MelodyNote(BaseModel):
    beat: float
    note: str
    octave: int = 0


class Silence(MelodyNote):
    beat: float
    note: str = "R"
    octave: int = 0


class AbsoluteMelodyNote(MelodyNote):
    pass


class Instrument(BaseModel):
    voice_name: str
    gm_number: int


class Melody(BaseModel):
    measure_number: int
    notes: List[MelodyNote]
    voice_name: str


# ==================================
# Metadata Lines
# ==================================


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
    measure_number: Optional[int] = None


class Tempo(BaseModel):
    tempo: int


class KeySignature(BaseModel):
    key_signature: str


class MinorMode(BaseModel):
    minor_mode: str


class Event(BaseModel):
    measure_number: int
    beat: float
    event_type: str
    event_value: Any


class Events(BaseModel):
    events: List[Event]
    measure_number: int


class EventItem(BaseModel):
    time: float
    measure_number: int
    beat: float
    event_type: str
    event_value: Any


class Instruments(BaseModel):
    instruments: List[Instrument]


# New models for techniques
class TechniqueRange(BaseModel):
    start_measure: int
    start_beat: float
    end_measure: int
    end_beat: float


class Technique(BaseModel):
    voice_names: List[str]
    technique_range: TechniqueRange
    techniques: List[str]


class TechniqueItem(BaseModel):
    time_start: float
    time_end: float
    voice_name: str
    technique: str


class TimeSignatureItem(BaseModel):
    measure_number: int
    time_signature: Tuple[int, int]


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
    Tempo,
    Instruments,
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


# ------------------------------
# Accompaniment Models
# ------------------------------


class AccompanimentVoice(BaseModel):
    voice: int
    octave: Optional[int] = 0
    alteration: Optional[int] = 0


class AccompanimentBeat(BaseModel):
    beat: float
    voices: List[AccompanimentVoice]


class AccompanimentBeatSilence(BaseModel):
    beat: float
    voices: List[AccompanimentVoice] = []


class Accompaniment(BaseModel):
    measure_number: int
    beats: List[AccompanimentBeat]
    voice_name: Optional[str] = "V1"


class VariableDeclaration(BaseModel):
    variable_name: str
    variable_value: str


class VariableCalling(BaseModel):
    variable_name: str


# A statement line can be any of the following:
StatementLine = Union[
    Measure,
    Repeat,
    Pedal,
    Form,
    Comment,
    Melody,
    Accompaniment,  # <-- NEW: Added accompaniment as a statement line
    Events,
    VariableDeclaration,
    Technique,
]

Line = Union[MetadataLine, StatementLine]
