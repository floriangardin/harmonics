from typing import List, Optional, Union, Tuple, Any, Dict, Set

from pydantic import BaseModel as RawBaseModel, Field
from .notes_utils import getPitchFromIntervalFromMinimallyModifiedScale

# Base model for all classes
class BaseModel(RawBaseModel):
    def __hash__(self):  # make hashable BaseModel subclass
        return hash(self.model_dump_json())

# ==============================
# Base Line Classes
# ==============================

class Line(BaseModel):
    """Base class for all lines in the document"""
    line_number: Optional[int] = Field(default=None)

class MetadataLine(Line):
    """Base class for all metadata lines"""
    pass

class StatementLine(Line):
    """Base class for all statement lines"""
    pass

# ==============================
# Melody Lines
# ==============================

class MelodyNote(BaseModel):
    beat: float
    techniques: List[str] = []
    text_comment: Optional[str] = None


class TextComment(MelodyNote):
    text: str


class AbsoluteMelodyNote(MelodyNote):
    note: str


class ChordMelodyNote(MelodyNote):
    notes: List[MelodyNote]


class Silence(MelodyNote):
    beat: float
    note: str = "R"
    octave: int = 0


class Continuation(MelodyNote):
    beat: float
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


class Melody(StatementLine):
    measure_number: int
    notes: List[MelodyNote]
    track_name: str = "T1"
    voice_name: str = "v1"


# ==================================
# Metadata Line Classes
# ==================================

class Composer(MetadataLine):
    composer: str


class Title(MetadataLine):
    title: str


class Analyst(MetadataLine):
    analyst: str


class Proofreader(MetadataLine):
    proofreader: str


class Movement(MetadataLine):
    movement: str


class TimeSignature(MetadataLine):
    numerator: int
    denominator: int
    measure_number: Optional[int] = None

class StaffGroup(MetadataLine):
    group_name: str
    track_names: List[str]

class Tempo(MetadataLine):
    tempo: int


class KeySignature(StatementLine):  # Changed to StatementLine based on its usage
    key_signature: str
    measure_number: Optional[int] = None


class MinorMode(MetadataLine):
    minor_mode: str


class Event(BaseModel):
    measure_number: int
    beat: float
    event_type: str
    event_value: Any


class Events(StatementLine):
    events: List[Event]
    measure_number: int


class Instruments(MetadataLine):
    instruments: List[Instrument]


# Clef models
class ClefType(BaseModel):
    name: str  # treble, bass, alto, etc.
    octave_change: Optional[int] = None  # +1, -1, etc. for octave displacement


class Clef(MetadataLine):
    track_name: str
    clef_type: ClefType
    measure_number: Optional[int] = None


class ClefChange(StatementLine):
    measure_number: int
    beat: float
    track_name: str
    clef_type: ClefType


# New models for techniques
class TechniqueRange(BaseModel):
    start_measure: int
    start_beat: float
    end_measure: int
    end_beat: float


class Technique(StatementLine):
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


class Measure(StatementLine):
    # measure_line: MEASURE_INDICATOR (chord_beat_1)? (beat_chord | key_change)+ PHRASE_BOUNDARY? NEWLINE
    measure_number: int
    beat_items: List[BeatItem]
    phrase_boundary: Optional[str] = None


class MeasureRange(BaseModel):
    # measure_range: MEASURE_INDICATOR ( "-" MEASURE_INDICATOR )+
    measures: List[str]


class Repeat(StatementLine):
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


class Pedal(StatementLine):
    # pedal_line: "Pedal:" WS note WS pedal_entries NEWLINE
    note: Note
    pedal_entries: List[PedalEntry]


class Form(StatementLine):
    # form_line: "Form:" WS REST_LINE NEWLINE
    form: str


class Comment(StatementLine):
    # note_line: "Note:" WS REST_LINE NEWLINE
    comment: str


# ------------------------------
# Accompaniment Models
# ------------------------------

class VariableDeclaration(StatementLine):
    variable_name: str
    variable_value: str


class VariableCalling(BaseModel):
    variable_name: str

# The Union types are no longer needed as we're using inheritance
# All StatementLine subclasses are now StatementLine
# All MetadataLine subclasses are now MetadataLine
# A Line can be either a MetadataLine or StatementLine
