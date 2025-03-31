from typing import List, Optional, Union, Tuple, Any, Dict, Set
from fractions import Fraction
from pydantic import BaseModel as RawBaseModel, Field
from .notes_utils import getPitchFromIntervalFromMinimallyModifiedScale


# Base model for all classes
class BaseModel(RawBaseModel):
    def __hash__(self):  # make hashable BaseModel subclass
        return hash(self.model_dump_json())


class Line(BaseModel):
    """Base class for all lines in the document"""

    line_number: Optional[int] = Field(default=None)


# ==============================
# Melody Lines
# ==============================


class MelodyNote(BaseModel):
    beat: Fraction
    techniques: List[str] = []
    text_comment: Optional[str] = None
    is_exact: bool = False


class TextComment(MelodyNote):
    text: str


class AbsoluteMelodyNote(MelodyNote):
    note: str


class ChordMelodyNote(MelodyNote):
    notes: List[MelodyNote]


class Silence(MelodyNote):
    note: str = "R"
    octave: int = 0


class Continuation(MelodyNote):
    note: str = "L"
    octave: int = 0


class Instrument(BaseModel):
    track_name: str
    name: str
    gm_number: int


class AccompanimentVoice(BaseModel):
    voice: int
    octave: Optional[int] = 0
    alteration: Optional[int] = 0


class AccompanimentBeat(MelodyNote):
    voices: List[AccompanimentVoice]


class Melody(Line):
    measure_number: int
    notes: List[MelodyNote]
    track_name: str = "T1"
    voice_name: str = "v1"
    measure_boundary: Optional[str] = None


# ==================================
# Metadata Line Classes
# ==================================


class Composer(Line):
    composer: str


class Title(Line):
    title: str


class Analyst(Line):
    analyst: str


class Proofreader(Line):
    proofreader: str


class Movement(Line):
    movement: str


class TimeSignature(Line):
    numerator: int
    denominator: int
    measure_number: Optional[int] = None


class StaffGroup(Line):
    group_name: str
    track_names: List[str]


class Tempo(Line):
    tempo: int


class KeySignature(Line):  # Changed to Line based on its usage
    key_signature: str
    measure_number: Optional[int] = None


class MinorMode(Line):
    minor_mode: str


class Event(BaseModel):
    measure_number: int
    beat: Fraction
    event_type: str
    event_value: Any


class Events(Line):
    events: List[Event]
    measure_number: int


class Instruments(Line):
    instruments: List[Instrument]


# Clef models
class ClefType(BaseModel):
    name: str  # treble, bass, alto, etc.
    octave_change: Optional[int] = None  # +1, -1, etc. for octave displacement


class Clef(Line):
    track_name: str
    clef_type: ClefType
    measure_number: Optional[int] = None


class ClefChange(Line):
    measure_number: int
    beat: Fraction
    track_name: str
    clef_type: ClefType


# New models for techniques
class TechniqueRange(BaseModel):
    start_measure: int
    start_beat: float
    end_measure: int
    end_beat: float


class Technique(Line):
    track_names: List[str]
    technique_range: TechniqueRange
    techniques: List[str]


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
BeatItem = Chord | Key  # Updated syntax for Python 3.10+

# ==============================
# Statement Line Classes
# ==============================


class BeatAndPitchClasses(BaseModel):
    beat: float
    pitch_classes: List[int]
    roman_numeral: str
    key_name: str


class Measure(Line):
    # measure_line: MEASURE_INDICATOR (chord_beat_1)? (beat_chord | key_change)+ PHRASE_BOUNDARY? NEWLINE
    measure_number: int
    beat_items: List[BeatItem]
    phrase_boundary: Optional[str] = None


class MeasureRange(BaseModel):
    # measure_range: MEASURE_INDICATOR ( "-" MEASURE_INDICATOR )+
    measures: List[str]


class Repeat(Line):
    # repeat_line: measure_range WS "=" WS measure_range NEWLINE
    start_range: MeasureRange
    equals: str
    end_range: MeasureRange


class Note(BaseModel):
    # note: NOTELETTER ACCIDENTAL?
    noteletter: str
    accidental: Optional[str] = None
    techniques: List[str] = []


class PedalEntry(BaseModel):
    # pedal_entry: MEASURE_INDICATOR WS BEAT_INDICATOR
    measure_indicator: str
    beat_indicator: str


class Pedal(Line):
    # pedal_line: "Pedal:" WS note WS pedal_entries NEWLINE
    note: Note
    pedal_entries: List[PedalEntry]


class Form(Line):
    # form_line: "Form:" WS REST_LINE NEWLINE
    form: str


class Comment(Line):
    # note_line: "Note:" WS REST_LINE NEWLINE
    comment: str


# ------------------------------
# Accompaniment Models
# ------------------------------


class VariableDeclaration(Line):
    variable_name: str
    variable_value: str


class VariableCalling(BaseModel):
    variable_name: str


# The Union types are no longer needed as we're using inheritance
# All Line subclasses are now Line
# All Line subclasses are now Line
# A Line can be either a Line or Line
