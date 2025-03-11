
from typing import List, Optional, Union, Tuple, Any, Dict, Set
from .models import BaseModel
import harmonics.models as models

class ChordItem(BaseModel):
    time: float
    duration: float
    chord: Optional[str] = None
    key: Optional[str] = None
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


class Score(BaseModel):
    chords: List[ChordItem]
    notes: List[NoteItem]
    time_signatures: List[TimeSignatureItem] = []
    tempos: List[TempoItem] = []
    events: List[models.EventItem] = []
    instruments: List[InstrumentItem] = []
    techniques: List[models.TechniqueItem] = []  # Add techniques to Score
