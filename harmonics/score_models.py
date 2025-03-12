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
    time: float
    duration: float
    chord: Optional[str] = None
    key: Optional[str] = None
    time_signature: Optional[Tuple[int, int]] = None
    pitch: Union[Optional[str], List[str]] = None
    is_silence: bool = False
    is_continuation: bool = False
    voice_name: Optional[str] = None
    techniques: Optional[List[str]] = None  # Add techniques field
    global_techniques: Optional[List[str]] = None
    measure_number: Optional[int] = None
    beat: Optional[float] = None


class TempoItem(BaseModel):
    time: float
    tempo: int
    measure_number: Optional[int] = None
    beat: Optional[float] = None


class TimeSignatureItem(BaseModel):
    time: float
    time_signature: Tuple[int, int]


class InstrumentItem(BaseModel):
    time: float
    voice_name: str
    voice_index: Optional[int] = None
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
    voice_name: str
    technique: str


class TimeSignatureItem(BaseModel):
    time: float
    measure_number: int
    time_signature: Tuple[int, int]


class MetadataItem(BaseModel):
    title: str
    composer: str


class Score(BaseModel):
    chords: List[ChordItem]
    notes: List[NoteItem]
    time_signatures: List[TimeSignatureItem] = []
    tempos: List[TempoItem] = []
    events: List[EventItem] = []
    instruments: List[InstrumentItem] = []
    techniques: List[TechniqueItem] = []  # Add techniques to Score
    title: str
    composer: str
