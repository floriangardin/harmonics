from typing import List, Optional, Union, Tuple, Any

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
# Accompaniment Models (NEW)
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
]

Line = Union[MetadataLine, StatementLine]

# ==============================
# Top-level Document
# ==============================


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
    pitch: Optional[str] = None
    is_silence: bool = False
    voice_name: Optional[str] = None


class TempoItem(BaseModel):
    time: float
    tempo: int
    measure_number: Optional[int] = None
    beat: Optional[float] = None


class TimeSignatureItem(BaseModel):
    time: float
    time_signature: Tuple[int, int]


# This is a new model for rendering accompaniment events.
class AccompanimentItem(BaseModel):
    time: float
    duration: float
    voices: List[AccompanimentVoice]
    chord_index: Optional[int] = None


class InstrumentItem(BaseModel):
    time: float
    voice_name: str
    voice_index: Optional[int] = None
    gm_number: int


class Score(BaseModel):
    chords: List[ChordItem]
    melody: List[NoteItem]
    accompaniment: List[AccompanimentItem] = []  # <-- NEW: Field added to Score
    time_signatures: List[TimeSignatureItem] = []
    tempos: List[TempoItem] = []
    events: List[EventItem] = []
    instruments: List[InstrumentItem] = []


def bar_duration_in_quarters(time_signature: Tuple[int, int]) -> int:
    return 4 * time_signature[0] / time_signature[1]


def beat_to_quarter(beat: float, time_signature: Tuple[int, int]) -> float:
    from harmonics.constants import BEAT_TO_QUARTER_NOTES

    if time_signature in BEAT_TO_QUARTER_NOTES:
        return BEAT_TO_QUARTER_NOTES[time_signature] * (beat - 1)
    else:
        return beat - 1


def get_current_chord_from_time(time: float, chords: List[NoteItem]) -> Optional[str]:
    for chord in chords:
        if chord.time <= time < chord.time + chord.duration:
            return chord
    return None


def get_current_chord_index_from_time(
    time: float, chords: List[NoteItem]
) -> Optional[int]:
    for i, chord in enumerate(chords):
        if chord.time <= time < chord.time + chord.duration:
            return i
    return None


class RomanTextDocument(BaseModel):
    lines: List[Line]

    @property
    def data(self) -> Tuple[List[ChordItem], List[TimeSignatureItem], List[TempoItem]]:
        results = []
        bar_start_time = 0  # In quarter (not in beat !)
        current_bar_index = 1  # Start at bar 1
        current_time_signature = (4, 4)
        next_current_time_signature = (4, 4)
        current_key = None
        time_signatures = []
        tempos = []
        instruments = []

        for line in self.lines:
            if isinstance(line, Measure):
                delta_bar = line.measure_number - current_bar_index
                current_bar_index = line.measure_number
                bar_start_time += delta_bar * bar_duration_in_quarters(
                    current_time_signature
                )
                for beat_item in line.beat_items:
                    beat_start_time = beat_to_quarter(
                        beat_item.beat, next_current_time_signature
                    )
                    duration = 0
                    if beat_item.key is not None:
                        current_key = beat_item.key
                    results.append(
                        ChordItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            chord=beat_item.chord,
                            time_signature=current_time_signature,
                            key=current_key,
                        )
                    )
                current_time_signature = next_current_time_signature
            elif isinstance(line, TimeSignature):
                next_current_time_signature = (line.numerator, line.denominator)
                time_signatures.append(
                    TimeSignatureItem(
                        time=bar_start_time, time_signature=next_current_time_signature
                    )
                )
            elif isinstance(line, Instruments):
                for instrument in line.instruments:
                    voice_index = 1
                    if instrument.voice_name.startswith("V"):
                        voice_index = int(instrument.voice_name[1:])
                        voice_cat = "V"
                    else:
                        voice_cat = instrument.voice_name
                    instruments.append(
                        InstrumentItem(
                            time=bar_start_time,
                            voice_name=voice_cat,
                            voice_index=voice_index,
                            gm_number=instrument.gm_number,
                        )
                    )
            elif isinstance(line, Tempo):
                tempos.append(
                    TempoItem(
                        time=bar_start_time,
                        measure_number=current_bar_index,
                        beat=1,
                        tempo=line.tempo,
                    )
                )
        # Fill the durations (using delta between next time)
        if len(results) > 0:
            for i in range(len(results) - 1):
                results[i].duration = results[i + 1].time - results[i].time
            results[-1].duration = (
                bar_start_time
                + bar_duration_in_quarters(current_time_signature)
                - results[-1].time
            )
        return results, time_signatures, tempos, instruments

    @property
    def chords(self) -> List[ChordItem]:
        return self.data[0]

    @property
    def melody(self) -> List[NoteItem]:
        # Loop trough all lines to get all voice_names
        voice_names = {}
        for line in self.lines:
            if isinstance(line, Melody):
                voice_names[line.voice_name] = []
        # Now loop trough all lines again to group the melody by voice_name, with time signature elements
        for line in self.lines:
            if isinstance(line, TimeSignature):
                # Append the time signature to all voice_names
                for key in voice_names.keys():
                    voice_names[key].append(line)
            elif isinstance(line, Melody):
                voice_names[line.voice_name].append(line)
        # Now return the melody grouped by voice_name

        all_results = []
        chords = self.chords
        for key in voice_names.keys():
            all_results.extend(self.melody_group(chords, voice_names[key]))
        # Sort the results by time
        all_results.sort(key=lambda x: x.time)
        return all_results

    def melody_group(self, chords, lines) -> List[NoteItem]:
        results = []
        current_chord = None
        previous_current_chord = None
        bar_start_time = 0  # In quarter (not in beat !)
        current_bar_index = 1
        current_time_signature = (4, 4)
        next_current_time_signature = (4, 4)
        for line in lines:
            if isinstance(line, TimeSignature):
                next_current_time_signature = (line.numerator, line.denominator)
            elif isinstance(line, Melody):
                delta_bar = line.measure_number - current_bar_index
                bar_start_time += delta_bar * bar_duration_in_quarters(
                    current_time_signature
                )
                current_bar_index = line.measure_number
                bar_notes = []
                for note in line.notes:
                    beat_start_time = beat_to_quarter(
                        note.beat, next_current_time_signature
                    )
                    duration = 0
                    time = beat_start_time + bar_start_time
                    previous_current_chord = current_chord
                    current_chord = get_current_chord_from_time(time, chords)

                    is_silence = False
                    if isinstance(note, Silence):
                        pitch = None
                        is_silence = True
                    elif isinstance(note, AbsoluteMelodyNote):
                        pitch = note.note
                    else:
                        if current_chord is None:
                            raise Exception(
                                "No chord found for measure {} at beat {}, while using an interval note".format(
                                    current_bar_index, note.beat
                                )
                            )
                        current_chord_to_use = (
                            current_chord
                            if current_chord.chord not in ["NC", "R", "r"]
                            else previous_current_chord
                        )

                        pitch = getPitchFromIntervalFromMinimallyModifiedScale(
                            current_chord_to_use.chord,
                            current_chord_to_use.key,
                            note.note,
                            note.octave,
                        )

                    if current_chord is None:
                        current_chord = ChordItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            chord="NC",
                            time_signature=current_time_signature,
                            key=None,
                        )
                    bar_notes.append(
                        NoteItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            chord=current_chord.chord,
                            key=current_chord.key,
                            time_signature=current_time_signature,
                            pitch=pitch,
                            is_silence=is_silence,
                            voice_name=line.voice_name,
                        )
                    )

                if len(bar_notes) > 0:
                    for i in range(len(bar_notes) - 1):
                        bar_notes[i].duration = (
                            bar_notes[i + 1].time - bar_notes[i].time
                        )
                    bar_notes[-1].duration = (
                        bar_start_time
                        + bar_duration_in_quarters(current_time_signature)
                        - bar_notes[-1].time
                    )
                    results.extend(bar_notes)
                current_time_signature = next_current_time_signature

        return results

    @property
    def events(self) -> List[EventItem]:
        results = []
        bar_start_time = 0  # In quarter (not in beat !)
        current_bar_index = 1
        current_time_signature = (4, 4)
        next_current_time_signature = (4, 4)
        for line in self.lines:
            if isinstance(line, TimeSignature):
                next_current_time_signature = (line.numerator, line.denominator)
            elif isinstance(line, Events):
                delta_bar = line.measure_number - current_bar_index
                current_bar_index = line.measure_number
                bar_start_time += delta_bar * bar_duration_in_quarters(
                    current_time_signature
                )

                for event in line.events:
                    # We use the next time signature because the event is in the next bar
                    beat_start_time = beat_to_quarter(
                        event.beat, next_current_time_signature
                    )
                    time = beat_start_time + bar_start_time
                    results.append(
                        EventItem(
                            time=time,
                            measure_number=event.measure_number,
                            beat=event.beat,
                            event_type=event.event_type,
                            event_value=event.event_value,
                        )
                    )
                current_time_signature = next_current_time_signature

        return results

    @property
    def accompaniment(self) -> List[AccompanimentItem]:
        results = []
        chords = self.chords
        bar_start_time = 0  # In quarter (not in beat !)
        current_bar_index = 1
        current_time_signature = (4, 4)
        next_current_time_signature = (4, 4)
        for line in self.lines:
            if isinstance(line, TimeSignature):
                next_current_time_signature = (line.numerator, line.denominator)
            elif isinstance(line, Accompaniment):
                delta_bar = line.measure_number - current_bar_index
                current_bar_index = line.measure_number
                bar_start_time += delta_bar * bar_duration_in_quarters(
                    current_time_signature
                )
                for beat in line.beats:
                    beat_start_time = beat_to_quarter(
                        beat.beat, next_current_time_signature
                    )
                    duration = 0
                    time = beat_start_time + bar_start_time
                    current_chord_index = get_current_chord_index_from_time(
                        time, chords
                    )
                    results.append(
                        AccompanimentItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            voices=beat.voices,
                            chord_index=current_chord_index,
                        )
                    )

                current_time_signature = next_current_time_signature

        if len(results) > 0:
            for i in range(len(results) - 1):
                results[i].duration = results[i + 1].time - results[i].time
            results[-1].duration = (
                bar_start_time
                + bar_duration_in_quarters(current_time_signature)
                - results[-1].time
            )

        return results
