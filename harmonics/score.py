from functools import lru_cache
from typing import List, Optional, Union, Tuple, Any, Dict, Set

from .models import BaseModel
from .notes_utils import getPitchFromIntervalFromMinimallyModifiedScale
import harmonics.models as models
import harmonics.exceptions as exceptions
import harmonics.commons.utils_techniques as utils_techniques
from harmonics.commons.utils_beat import to_beat_fraction

from harmonics.score_models import (
    NoteItem,
    ChordItem,
    TimeSignatureItem,
    TempoItem,
    InstrumentItem,
    EventItem,
    TechniqueItem,
    ClefItem,
    KeySignatureItem,
)

# ==================================
# Top-level Document & Parsed Items
# ==================================


def bar_duration_in_quarters(time_signature: Tuple[int, int]) -> int:
    return 4 * time_signature[0] / time_signature[1]


def bar_duration_in_beats(time_signature: Tuple[int, int]) -> int:
    return time_signature[0]


def beat_to_quarter(beat: float, time_signature: Tuple[int, int]) -> float:
    return (beat - 1) * 4 / time_signature[1]


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
        if isinstance(line, (models.Melody, models.Events)):
            max_measure = max(max_measure, line.measure_number)

    # First pass: collect all time signatures
    previous_measure_number = 0
    already_declared_measures = set()

    # Are measures sorted
    measure_numbers = [
        l.measure_number for l in lines if isinstance(l, (models.Melody, models.Events))
    ]
    are_measures_sorted = measure_numbers == sorted(measure_numbers)

    for line in lines:
        if isinstance(line, (models.Melody, models.Events)):
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


class ScoreData(BaseModel):
    chords: List[ChordItem]
    time_signatures: List[TimeSignatureItem]
    tempos: List[TempoItem]
    instruments: List[InstrumentItem]
    title: str
    composer: str
    clefs: List[ClefItem]
    key_signatures: List[KeySignatureItem]
    measure_boundaries: Dict[int, str]  # Measure number -> measure boundary


@lru_cache(maxsize=10)
def get_data(self) -> ScoreData:
    chords = []
    bar_start_time = 0  # In quarter (not in beat !)
    current_bar_index = 1  # Start at bar 1
    current_time_signature = (4, 4)
    next_current_time_signature = (4, 4)
    current_key = None
    time_signatures = []
    tempos = []
    instruments = []
    clefs = []
    all_tracks = []
    key_signatures = []
    measure_boundaries = {}  # Measure number -> measure boundary
    title = ""
    composer = ""
    groups = {}

    for line in self.lines:
        if isinstance(line, models.StaffGroup):
            groups[line.group_name] = line.track_names
    # Invert the dict to have a dict of track_name -> group_name
    groups_inv = {
        track_name: group_name
        for group_name, track_names in groups.items()
        for track_name in track_names
    }

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
                chords.append(
                    ChordItem(
                        time=beat_start_time + bar_start_time,
                        measure_number=line.measure_number,
                        beat=to_beat_fraction(beat_item.beat),
                        duration=duration,
                        chord=beat_item.chord,
                        time_signature=current_time_signature,
                        key=current_key,
                        new_key=beat_item.key is not None,
                        line_number=line.line_number,
                    )
                )
            current_time_signature = next_current_time_signature
        elif isinstance(line, models.Title):
            title = line.title
        elif isinstance(line, models.Composer):
            composer = line.composer
        elif isinstance(line, models.TimeSignature):
            next_current_time_signature = (line.numerator, line.denominator)
            time_signatures.append(
                TimeSignatureItem(
                    time=bar_start_time,
                    time_signature=next_current_time_signature,
                    measure_number=(
                        current_bar_index
                        if line.measure_number is None
                        else line.measure_number
                    ),
                )
            )
        elif isinstance(line, models.Instruments):
            for track_index, instrument in enumerate(line.instruments):
                instruments.append(
                    InstrumentItem(
                        time=bar_start_time,
                        track_name=instrument.track_name,
                        track_index=track_index,
                        gm_number=instrument.gm_number,
                        name=instrument.name,
                        staff_group=groups_inv.get(instrument.track_name, None),
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
        elif isinstance(line, models.ClefLine):
            # Initial clef specifications at the beginning of the score
            for clef in line.clefs:
                clefs.append(
                    ClefItem(
                        time=bar_start_time,
                        track_name=clef.track_name,
                        clef_name=clef.clef_type.name,
                        octave_change=clef.clef_type.octave_change,
                        measure_number=(
                            clef.measure_number
                            if clef.measure_number is not None
                            else current_bar_index
                        ),
                        beat=1,  # Default to first beat of the measure
                    )
                )
        elif isinstance(line, models.KeySignature):
            # Add key signature to the list
            key_signatures.append(
                KeySignatureItem(
                    time=bar_start_time,
                    measure_number=(
                        line.measure_number
                        if line.measure_number is not None
                        else current_bar_index
                    ),
                    beat=1.0,  # Default to first beat of the measure
                    key_signature=line.key_signature,
                )
            )
        elif isinstance(line, models.Melody):
            if line.track_name not in all_tracks:
                all_tracks.append(line.track_name)
            if line.measure_boundary is not None:
                measure_boundaries[line.measure_number] = line.measure_boundary
    # Fill the durations (using delta between next time)
    if len(chords) > 0:
        for i in range(len(chords) - 1):
            chords[i].duration = chords[i + 1].beat - chords[i].beat
        chords[-1].duration = (
            +bar_duration_in_beats(current_time_signature) + 1 - chords[-1].beat
        )

    self.get_progression(chords)
    instrument_tracks = [i.track_name for i in instruments]
    missing_tracks = set(all_tracks) - set(instrument_tracks)
    for track_name in missing_tracks:
        instruments.append(
            InstrumentItem(
                time=0,
                track_name=track_name,
                track_index=len(instruments),
                gm_number=0,
                name="piano",
        ))
    return ScoreData(
        chords=chords,
        time_signatures=time_signatures,
        tempos=tempos,
        instruments=instruments,
        title=title,
        composer=composer,
        clefs=clefs,
        key_signatures=key_signatures,
        measure_boundaries=measure_boundaries,
    )


class ScoreDocument(BaseModel):
    lines: List[models.Line]

    @property
    def time_signatures(self) -> List[TimeSignatureItem]:
        pass

    def get_progression(self, chords: List[ChordItem]) -> List[str]:
        from music21.pitch import Pitch
        from harmonics.romanyh import generateBestHarmonization

        if len(chords) > 0:
            progression = generateBestHarmonization(
                chords,
                closePosition=False,
                firstVoicing=None,
                lastVoicing=None,
                allowedUnisons=0,
            )
        else:
            progression = []

        for chord, pitches in zip(chords, progression):
            pitches = [Pitch(p).nameWithOctave for p in pitches]
            chord.pitches = pitches

    @property
    def data(self) -> ScoreData:
        return get_data(self)

    @property
    def chords(self) -> List[ChordItem]:
        return self.data.chords

    @property
    def notes(self) -> List[NoteItem]:
        import time as tt

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
                bar_notes = []
                for note in line.notes:
                    beat_start_time = beat_to_quarter(note.beat, current_time_signature)
                    duration = 0
                    time = beat_start_time + bar_start_time
                    current_chord = get_current_chord_from_time(time, chords)
                    voices = None
                    is_silence = False
                    is_continuation = False

                    if isinstance(note, models.Silence):
                        pitch = None
                        is_silence = True
                    elif isinstance(note, models.Continuation):
                        pitch = None
                        is_continuation = True
                    elif isinstance(note, models.AbsoluteMelodyNote):
                        pitch = note.note
                    elif isinstance(note, models.ChordMelodyNote):
                        pitch = [n.note for n in note.notes]
                    elif isinstance(note, models.AccompanimentBeat):
                        voices = note.voices
                        pitch = [current_chord.pitches[v.voice - 1] for v in voices]

                    if current_chord is None:
                        current_chord = ChordItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            chord="NC",
                            time_signature=current_time_signature,
                            key=None,
                            beat=note.beat,
                            measure_number=line.measure_number,
                        )
                    # global_techniques = self.get_techniques_for_note(
                    #     time, line.track_name, self.techniques
                    # )
                    global_techniques = []
                    bar_notes.append(
                        NoteItem(
                            time=beat_start_time + bar_start_time,
                            duration=duration,
                            chord=current_chord.chord,
                            key=current_chord.key,
                            time_signature=current_time_signature,
                            pitch=pitch,
                            voices=voices,
                            is_silence=is_silence,
                            is_continuation=is_continuation,
                            voice_name=line.voice_name,
                            track_name=line.track_name,
                            techniques=note.techniques,
                            global_techniques=global_techniques,
                            measure_number=line.measure_number,
                            beat=note.beat,
                            is_exact=note.is_exact,
                            text_comment=note.text_comment,
                        )
                    )
                if len(bar_notes) > 0:
                    for i in range(len(bar_notes) - 1):
                        if bar_notes[i].is_exact and bar_notes[i + 1].is_exact:
                            bar_notes[i].duration = (
                                bar_notes[i + 1].beat - bar_notes[i].beat
                            )
                        else:
                            bar_notes[i].duration = to_beat_fraction(
                                bar_notes[i + 1].beat - bar_notes[i].beat
                            )
                    if bar_notes[-1].is_exact:
                        bar_notes[-1].duration = (
                            bar_duration_in_beats(current_time_signature)
                            - bar_notes[-1].beat
                            + 1
                        )
                    else:
                        bar_notes[-1].duration = to_beat_fraction(
                            bar_duration_in_beats(current_time_signature)
                            - bar_notes[-1].beat
                            + 1
                        )
                    results.extend(bar_notes)
        results = sorted(results, key=lambda r: (r.measure_number, r.beat))
        return results

    @property
    def events(self) -> List[EventItem]:
        results = []
        bar_start_time = 0  # In quarter (not in beat !)
        measure_map = get_measure_map(self.lines)
        # Add first tempo to events
        first_tempo = self.data.tempos[0] if len(self.data.tempos) > 0 else None
        if first_tempo is not None:
            results.append(
                EventItem(
                    time=first_tempo.time,
                    measure_number=first_tempo.measure_number,
                    beat=1.0,
                    event_type="tempo",
                    event_value=first_tempo.tempo,
                )
            )

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
                        EventItem(
                            time=time,
                            measure_number=event.measure_number,
                            beat=to_beat_fraction(event.beat),
                            event_type=event.event_type,
                            event_value=event.event_value,
                        )
                    )
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
    def techniques(self) -> List[TechniqueItem]:
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
                for track_name in line.track_names:
                    for technique in line.techniques:
                        results.append(
                            TechniqueItem(
                                time_start=start_time,
                                time_end=end_time,
                                measure_number_start=line.technique_range.start_measure,
                                beat_start=line.technique_range.start_beat,
                                measure_number_end=line.technique_range.end_measure,
                                beat_end=line.technique_range.end_beat,
                                track_name=track_name,
                                technique=technique,
                            )
                        )
        return results

    @property
    def key_signatures(self) -> List[KeySignatureItem]:
        """Get all key signatures from the document data."""
        return self.data.key_signatures

    def get_techniques_for_note(
        self, time: float, track_name: str, techniques: List[TechniqueItem]
    ) -> List[str]:
        """Get all techniques that apply to a note at a specific time for a specific voice"""
        active_techniques = []
        for technique in techniques:
            if (
                technique.track_name == track_name
                and technique.time_start <= time < technique.time_end
            ):
                active_techniques.append(technique.technique)
        return active_techniques

    @property
    def clefs(self) -> List[ClefItem]:
        results = []
        measure_map = get_measure_map(self.lines)

        # First add any clefs declared as metadata
        for line in self.lines:
            if isinstance(line, models.Clef):
                measure_number = (
                    line.measure_number if line.measure_number is not None else 1
                )
                bar_start_time, _, current_time_signature = measure_map.get(
                    measure_number, (0, 0, (4, 4))
                )
                results.append(
                    ClefItem(
                        time=bar_start_time,
                        track_name=line.track_name,
                        clef_name=line.clef_type.name,
                        octave_change=line.clef_type.octave_change,
                        measure_number=measure_number,
                        beat=1.0,  # Default to first beat
                    )
                )

        # Then add clef changes within the score
        for line in self.lines:
            if isinstance(line, models.ClefChange):
                bar_start_time, _, current_time_signature = measure_map.get(
                    line.measure_number, (0, 0, (4, 4))
                )
                beat_start_time = beat_to_quarter(line.beat, current_time_signature)
                time = beat_start_time + bar_start_time

                results.append(
                    ClefItem(
                        time=time,
                        track_name=line.track_name,
                        clef_name=line.clef_type.name,
                        octave_change=line.clef_type.octave_change,
                        measure_number=line.measure_number,
                        beat=to_beat_fraction(line.beat),
                    )
                )

        # Sort clefs by time for proper processing
        results.sort(key=lambda c: (c.time, c.measure_number, c.beat))
        return results
