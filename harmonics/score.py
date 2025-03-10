from typing import List, Optional, Union, Tuple, Any, Dict, Set

from pydantic import BaseModel
from .notes_utils import getPitchFromIntervalFromMinimallyModifiedScale
import harmonics.models as models
import harmonics.exceptions as exceptions

# ==================================
# Top-level Document & Parsed Items
# ==================================


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
    voice_name: Optional[str] = None
    techniques: Optional[List[str]] = None  # Add techniques field


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
    voices: List[models.AccompanimentVoice]
    chord_index: Optional[int] = None
    voice_name: Optional[str] = "V1"
    techniques: Optional[List[str]] = None  # Add techniques field


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
    events: List[models.EventItem] = []
    instruments: List[InstrumentItem] = []
    techniques: List[models.TechniqueItem] = []  # Add techniques to Score


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


def get_measure_map(lines: List[models.Line]) -> Dict[int, models.Line]:
    measure_map = {}
    tss = []

    # First pass collect max measure number
    max_measure = 0
    for line in lines:
        if isinstance(line, (models.Accompaniment, models.Melody, models.Events)):
            max_measure = max(max_measure, line.measure_number)

    # First pass: collect all time signatures
    previous_measure_number = 0
    already_declared_measures = set()

    # Are measures sorted
    measure_numbers = [
        l.measure_number
        for l in lines
        if isinstance(l, (models.Accompaniment, models.Melody, models.Events))
    ]
    are_measures_sorted = measure_numbers == sorted(measure_numbers)

    for line in lines:
        if isinstance(line, (models.Accompaniment, models.Melody, models.Events)):
            previous_measure_number = line.measure_number
        elif isinstance(line, models.TimeSignature):
            if line.measure_number is None:
                if not are_measures_sorted and previous_measure_number > 0:
                    raise exceptions.TimeSignatureMeasureMustBeDeclared(
                        f"Time signature measure number must be declared when measures are not sorted"
                    )
                line.measure_number = (
                    previous_measure_number + 1
                )  # Time signature valid for next measure
            if line.measure_number in already_declared_measures:
                raise exceptions.TimeSignatureAlreadyDeclared(
                    f"Time signature for measure {line.measure_number} already declared"
                )
            tss.append(line)
            already_declared_measures.add(line.measure_number)

    # Calculate measure start time for each measure from 1 to max_measure
    current_time_in_quarters = 0
    current_ts = None
    for i in range(1, max_measure + 1):
        for ts in tss:
            if ts.measure_number == i:
                current_ts = ts
        if current_ts is None:
            raise exceptions.TimeSignatureNotDeclared(
                f"No time signature found for measure {i}"
            )
        start_time = current_time_in_quarters
        bar_duration = bar_duration_in_quarters(
            (current_ts.numerator, current_ts.denominator)
        )
        current_time_in_quarters += bar_duration
        end_time = current_time_in_quarters
        measure_map[i] = (
            start_time,
            end_time,
            (current_ts.numerator, current_ts.denominator),
        )

    return measure_map


class RomanTextDocument(BaseModel):
    lines: List[models.Line]

    @property
    def time_signatures(self) -> List[TimeSignatureItem]:
        pass

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
            if isinstance(line, models.Measure):
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
            elif isinstance(line, models.TimeSignature):
                next_current_time_signature = (line.numerator, line.denominator)
                time_signatures.append(
                    TimeSignatureItem(
                        time=bar_start_time, time_signature=next_current_time_signature
                    )
                )
            elif isinstance(line, models.Instruments):
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
            elif isinstance(line, models.Tempo):
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
        results = []
        chords = self.chords
        current_chord = None
        previous_current_chord = None
        measure_map = get_measure_map(self.lines)
        for line in self.lines:
            if isinstance(line, models.Melody):
                bar_start_time, bar_end_time, current_time_signature = measure_map[
                    line.measure_number
                ]
                current_bar_index = line.measure_number
                bar_notes = []
                for note in line.notes:
                    beat_start_time = beat_to_quarter(note.beat, current_time_signature)
                    duration = 0
                    time = beat_start_time + bar_start_time
                    previous_current_chord = current_chord
                    current_chord = get_current_chord_from_time(time, chords)

                    is_silence = False
                    if isinstance(note, models.Silence):
                        pitch = None
                        is_silence = True
                    elif isinstance(note, models.AbsoluteMelodyNote):
                        pitch = note.note
                    elif isinstance(note, models.ChordMelodyNote):
                        pitch = [n.note for n in note.notes]
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
                            techniques=self.get_techniques_for_note(
                                time, line.voice_name, self.techniques
                            ),
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

        return results

    @property
    def events(self) -> List[models.EventItem]:
        results = []
        bar_start_time = 0  # In quarter (not in beat !)
        measure_map = get_measure_map(self.lines)
        for line in self.lines:
            if isinstance(line, models.Events):
                bar_start_time, bar_end_time, current_time_signature = measure_map[
                    line.measure_number
                ]
                for event in line.events:
                    # We use the next time signature because the event is in the next bar
                    beat_start_time = beat_to_quarter(
                        event.beat, current_time_signature
                    )
                    time = beat_start_time + bar_start_time
                    results.append(
                        models.EventItem(
                            time=time,
                            measure_number=event.measure_number,
                            beat=event.beat,
                            event_type=event.event_type,
                            event_value=event.event_value,
                        )
                    )
        return results

    @property
    def accompaniment(self) -> List[AccompanimentItem]:
        chords = self.chords
        all_results = self._accompaniment(chords, self.lines)
        # Sort the results by time
        all_results.sort(key=lambda x: x.time)
        techniques = self.techniques
        for item in all_results:
            item.techniques = self.get_techniques_for_note(
                item.time, item.voice_name, techniques
            )

        return all_results

    def _accompaniment(self, chords, lines) -> List[AccompanimentItem]:
        results = []
        bar_start_time = 0  # In quarter (not in beat !)
        measure_map = get_measure_map(lines)
        for line in lines:
            if isinstance(line, models.Accompaniment):
                bar_start_time, bar_end_time, current_time_signature = measure_map[
                    line.measure_number
                ]
                bar_notes = []
                for beat in line.beats:
                    beat_start_time = beat_to_quarter(beat.beat, current_time_signature)
                    duration = 0
                    time = beat_start_time + bar_start_time
                    current_chord_index = get_current_chord_index_from_time(
                        time, chords
                    )
                    bar_notes.append(
                        AccompanimentItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            voices=beat.voices,
                            chord_index=current_chord_index,
                            voice_name=line.voice_name,
                            techniques=self.get_techniques_for_note(
                                time, line.voice_name, self.techniques
                            ),
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

        return results

    def get_bar_info(
        self,
        measure_number: int,
        measure_map: Dict[int, Tuple[float, float, Tuple[int, int]]],
    ) -> Tuple[float, float, Tuple[int, int]]:
        start_bar_time, end_bar_time, time_signature = measure_map[
            min(measure_number, max(measure_map.keys()))
        ]
        delta_bar = measure_number - max(measure_map.keys())
        if delta_bar > 0:
            start_bar_time += delta_bar * bar_duration_in_quarters(time_signature)
            end_bar_time += delta_bar * bar_duration_in_quarters(time_signature)
        return start_bar_time, end_bar_time, time_signature

    @property
    def techniques(self) -> List[models.TechniqueItem]:
        results = []
        measure_map = get_measure_map(self.lines)
        for i, line in enumerate(self.lines):
            if isinstance(line, models.Technique):
                start_start_bar_time, _, start_time_signature = self.get_bar_info(
                    line.technique_range.start_measure, measure_map
                )
                end_end_bar_time, _, end_time_signature = self.get_bar_info(
                    line.technique_range.end_measure, measure_map
                )

                start_time = start_start_bar_time + beat_to_quarter(
                    line.technique_range.start_beat, start_time_signature
                )
                end_time = end_end_bar_time + beat_to_quarter(
                    line.technique_range.end_beat, end_time_signature
                )
                for voice_name in line.voice_names:
                    for technique in line.techniques:
                        results.append(
                            models.TechniqueItem(
                                time_start=start_time,
                                time_end=end_time,
                                voice_name=voice_name,
                                technique=technique,
                            )
                        )
        return results

    def get_techniques_for_note(
        self, time: float, voice_name: str, techniques: List[models.TechniqueItem]
    ) -> List[str]:
        """Get all techniques that apply to a note at a specific time for a specific voice"""
        active_techniques = []
        for technique in techniques:
            if (
                technique.voice_name == voice_name
                and technique.time_start <= time < technique.time_end
            ):
                active_techniques.append(technique.technique)
        return active_techniques
