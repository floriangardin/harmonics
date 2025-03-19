from typing import List, Optional, Union, Tuple, Any, Dict, Set
from .models import BaseModel


class ChordItem(BaseModel):
    time: float
    beat: float
    measure_number: int
    duration: float
    chord: Optional[str] = None
    key: Optional[str] = None
    new_key: Optional[bool] = False
    time_signature: Optional[Tuple[int, int]] = None
    pitches: Optional[List[str]] = None


class NoteItem(BaseModel):
    time: Optional[float] = 0
    duration: float
    chord: Optional[str] = None
    key: Optional[str] = None
    time_signature: Optional[Tuple[int, int]] = None
    pitch: Union[Optional[str], List[str]] = None
    is_silence: bool = False
    is_continuation: bool = False
    voice_name: Optional[str] = None
    track_name: Optional[str] = None
    techniques: Optional[List[str]] = None  # Add techniques field
    global_techniques: Optional[List[str]] = None
    measure_number: Optional[int] = None
    beat: Optional[float] = None
    text_comment: Optional[str] = None  # Add text comment field


class TempoItem(BaseModel):
    time: float
    tempo: int
    figure: Optional[str] = "quarter"
    text: Optional[str] = None
    measure_number: Optional[int] = None
    beat: Optional[float] = None


class TimeSignatureItem(BaseModel):
    time: float
    measure_number: int
    time_signature: Tuple[int, int]


class InstrumentItem(BaseModel):
    time: float
    track_name: str
    track_index: Optional[int] = None
    gm_number: int
    name: str


class EventItem(BaseModel):
    time: float
    measure_number: int
    beat: float
    event_type: str
    event_value: Any


class TechniqueItem(BaseModel):
    time_start: float
    time_end: float
    measure_number_start: int
    beat_start: float
    measure_number_end: int
    beat_end: float
    voice_name: Optional[str] = None
    track_name: Optional[str] = None
    technique: str


class MetadataItem(BaseModel):
    title: str
    composer: str


class ClefItem(BaseModel):
    time: float
    track_name: str
    clef_name: str  # treble, bass, alto, etc.
    octave_change: Optional[int] = None  # +1, -1, etc.
    measure_number: Optional[int] = None
    beat: Optional[float] = None


class KeySignatureItem(BaseModel):
    time: float
    measure_number: int
    beat: Optional[float] = None
    key_signature: (
        str  # String of accidentals, e.g. "bbb" for 3 flats or "###" for 3 sharps
    )


class Score(BaseModel):
    chords: List[ChordItem]
    notes: List[NoteItem]
    time_signatures: List[TimeSignatureItem] = []
    tempos: List[TempoItem] = []
    events: List[EventItem] = []
    instruments: List[InstrumentItem] = []
    techniques: List[TechniqueItem] = []  # Add techniques to Score
    clefs: List[ClefItem] = []  # Add clefs to Score
    key_signatures: List[KeySignatureItem] = []  # Add key signatures to Score
    title: str
    composer: str
