import music21 as m21
from fractions import Fraction
import re
from typing import Dict, List, Optional, Set, Any
from copy import deepcopy
import os
import shutil
import tempfile
from harmonics.commons import utils_techniques
from harmonics.commons.utils_output import correct_xml_file, convert_musicxml_to_mxl
from harmonics.commons.utils_beat import get_ratio_beat


class PartState:
    """Class to track the state of a part during MusicXML conversion."""

    def __init__(self):
        self.ref_note = {}  # Reference notes for tied notes
        self.crescendo_notes = []  # Notes in a crescendo
        self.diminuendo_notes = []  # Notes in a diminuendo
        self.slur_notes = []  # Notes in a slur
        self.pedal_notes = []  # Notes in a pedal
        self.crescendo_start = False  # Whether a crescendo has started
        self.diminuendo_start = False  # Whether a diminuendo has started
        self.slur_start = False  # Whether a slur has started
        self.pedal_start = False  # Whether a pedal has started
        self.last_chord = None  # Last chord for comparison
        self.last_key = None  # Last key for comparison

        self.slur_notes = []  # Notes in a slur
        self.pedal_notes = []  # Notes in a pedal
        self.crescendo_start = False  # Whether a crescendo has started
        self.diminuendo_start = False  # Whether a diminuendo has started
        self.slur_start = False  # Whether a slur has started
        self.last_chord = None  # Last chord for comparison
        self.last_key = None  # Last key for comparison


def to_mxl(filepath, score):
    """
    Convert a score to a MusicXML file.

    Args:
        filepath: Path to save the MusicXML file
        score: Score object containing notes, chords, time signatures, etc.
    """
    # Initialize music21 score and parts
    m21_score, parts = _init_m21_score(score)

    # Find max measure number
    max_measure = _find_max_measure_number(score)

    # Create time signature map and calculate measure durations
    time_sig_map, measure_durations = _create_time_sig_map(score, max_measure)

    # Create all measures for all parts
    first_instrument_measures, all_measures = _create_all_measures(
        score, parts, max_measure, time_sig_map, measure_durations
    )

    # Process comments, harmony, events, time signatures, and clefs
    _write_comments_and_harmony(score, time_sig_map, first_instrument_measures)
    _apply_events(score, time_sig_map, first_instrument_measures)
    _apply_time_signatures(m21_score, score, all_measures, first_instrument_measures)
    _apply_clefs(m21_score, score)
    _apply_key_signatures(m21_score, score)
    _add_phrase_boundaries(m21_score, score.measure_boundaries)
    # Write to file
    _correct_xml_and_compress(m21_score, filepath)


def _apply_techniques(note, m21_note, measure, part_state, ts):
    """
    Apply techniques to a note and update the part state.

    Args:
        note: The note object from the score
        m21_note: The music21 note object
        measure: The current measure
        part_state: The state of the part

    Returns:
        The updated music21 note
    """
    # Add techniques/articulations
    techniques = note.global_techniques + note.techniques
    # Resolve techniques
    techniques = utils_techniques.resolve_techniques(techniques)

    if techniques:
        for technique in techniques:
            if technique.replace("!", "") in [
                "crescendo",
                "cresc",
                "cresc.",
                "crescendo.",
            ]:
                if not technique.startswith("!"):
                    part_state.crescendo_start = True
                    part_state.crescendo_notes.append(m21_note)
                else:
                    part_state.crescendo_notes.append(m21_note)
                    part_state.crescendo_start = False
                    crescendo = m21.dynamics.Crescendo()
                    crescendo.addSpannedElements(part_state.crescendo_notes)
                    measure.insert(0, crescendo)
                    part_state.crescendo_notes = []
            elif technique.replace("!", "") in [
                "diminuendo",
                "dim",
                "decrescendo",
                "decresc",
                "decresc.",
                "dim.",
            ]:
                if not technique.startswith("!"):
                    part_state.diminuendo_start = True
                    part_state.diminuendo_notes.append(m21_note)
                else:
                    part_state.diminuendo_notes.append(m21_note)
                    part_state.diminuendo_start = False
                    diminuendo = m21.dynamics.Diminuendo()
                    diminuendo.addSpannedElements(part_state.diminuendo_notes)
                    measure.insert(0, diminuendo)
                    part_state.diminuendo_notes = []
            elif technique.replace("!", "") in ["legato", "slur"]:
                if not technique.startswith("!"):
                    part_state.slur_start = True
                    # Add the current note to slur notes
                    part_state.slur_notes.append(m21_note)
                else:
                    # For slurs, we want to include the last note in the slur
                    # so we add the current note before ending the slur
                    part_state.slur_notes.append(m21_note)
                    part_state.slur_start = False
                    slur = m21.spanner.Slur()
                    slur.addSpannedElements(part_state.slur_notes)
                    measure.insert(0, slur)
                    part_state.slur_notes = []
            elif technique.replace("!", "") in [
                "pedal",
                "ped",
                "sustain",
                "ped.",
                "pedal.",
            ]:
                if not technique.startswith("!"):
                    # Add pedal down marking (as a text comment)
                    text = m21.expressions.TextExpression("$pedal_start")
                    text.positionVertical = 20
                    text.style.fontStyle = "italic"
                    measure.insert(_get_offset(note.beat, ts), text)
                else:
                    text = m21.expressions.TextExpression("$pedal_stop")
                    text.positionVertical = 20
                    text.style.fontStyle = "italic"
                    measure.insert(_get_offset(note.beat, ts), text)
            else:
                technique_obj, technique_type = _create_technique(technique)
                if technique_obj:
                    if technique_type == "articulations":
                        m21_note.articulations.append(technique_obj)
                    elif technique_type == "dynamics":
                        measure.insert(_get_offset(note.beat, ts), technique_obj)
                    elif technique_type == "expressions":
                        m21_note.expressions.append(technique_obj)
                else:
                    # Create comment with the technique name
                    text = m21.expressions.TextExpression(technique)
                    text.positionVertical = 20
                    text.style.fontStyle = "italic"
                    measure.insert(_get_offset(note.beat, ts), text)

    # Only add to slur_notes if we're in a slur and haven't already added this note
    # (we already add the note when the slur starts or ends)
    if part_state.slur_start and m21_note not in part_state.slur_notes:
        part_state.slur_notes.append(m21_note)

    if part_state.crescendo_start and m21_note not in part_state.crescendo_notes:
        part_state.crescendo_notes.append(m21_note)
    if part_state.diminuendo_start and m21_note not in part_state.diminuendo_notes:
        part_state.diminuendo_notes.append(m21_note)
    if part_state.pedal_start and m21_note not in part_state.pedal_notes:
        part_state.pedal_notes.append(m21_note)

    return m21_note


def _add_key_signature_to_measure(measure, key_signature_item, current_ts):
    """
    Add a key signature to a measure.

    Args:
        measure: The music21 measure to add the key signature to
        key_signature_item: The KeySignatureItem containing key signature information
    """
    if key_signature_item is None:
        return

    # Count sharps/flats in the key signature string
    sharps_count = key_signature_item.key_signature.count("#")
    flats_count = key_signature_item.key_signature.count("b")

    # If sharps, use positive number; if flats, use negative number
    sharps = sharps_count if sharps_count > 0 else -flats_count

    # Create the key signature
    m21_key = m21.key.KeySignature(sharps)

    # Insert at the appropriate offset
    offset = 0.0
    if key_signature_item.beat is not None and key_signature_item.beat > 1.0:
        offset = _get_offset(key_signature_item.beat, current_ts)
    measure.insert(offset, m21_key)


def _find_max_measure_number(score):
    """Find the maximum measure number in the score."""
    return max(
        note.measure_number for note in score.notes if note.measure_number is not None
    )


def _create_time_sig_map(score, max_measure):
    """Create a time signature map and calculate measure durations for all measures."""
    time_sig_map = _get_time_sig_map(score.time_signatures, max_measure)

    # Calculate duration for each measure
    measure_durations = {}
    for measure_num in range(1, max_measure + 1):
        current_ts = time_sig_map[measure_num]
        measure_durations[measure_num] = 4 * current_ts[0] / current_ts[1]

    return time_sig_map, measure_durations


def _create_all_measures(score, parts, max_measure, time_sig_map, measure_durations):
    """Create measures for all parts and populate them with notes."""
    first_instrument_measures = {}
    all_measures = {}
    first_voice_of_track = {track_name: True for track_name, _ in parts.keys()}
    idx = -1
    for (track_name, voice_name), part in parts.items():
        idx += 1
        # Create part state to track ongoing musical elements
        part_state = PartState()

        key_signatures = sorted(
            score.key_signatures, key=lambda ks: (ks.time, ks.measure_number)
        )
        current_key_sig_idx = 0

        # Create measures for this part
        _create_measures_for_part(
            score,
            part,
            track_name,
            voice_name,
            part_state,
            max_measure,
            time_sig_map,
            measure_durations,
            first_instrument_measures,
            all_measures,
            idx,
        )

        # Mark this voice as processed
        first_voice_of_track[track_name] = False

    return first_instrument_measures, all_measures


def _create_measures_for_part(
    score,
    part,
    track_name,
    voice_name,
    part_state,
    max_measure,
    time_sig_map,
    measure_durations,
    first_instrument_measures,
    all_measures,
    part_idx,
):
    """Create and populate measures for a specific part."""
    for measure_num in range(1, max_measure + 1):
        current_ts = time_sig_map[measure_num]
        # Create measure with time signature
        measure = m21.stream.Measure(number=measure_num, timeSignature=current_ts)

        # Store measure in collections
        all_measures[measure_num] = all_measures.get(measure_num, []) + [measure]
        if part_idx == 0:
            first_instrument_measures[measure_num] = measure

        # Add notes for this voice and measure
        _add_notes_to_measure(
            score,
            measure,
            track_name,
            voice_name,
            measure_num,
            current_ts,
            part_state,
            measure_durations,
        )

        # Add measure to part
        part.append(measure)


def _add_notes_to_measure(
    score,
    measure,
    track_name,
    voice_name,
    measure_num,
    current_ts,
    part_state,
    measure_durations,
):
    """Add notes to a measure for a specific voice."""
    # Get notes for this voice and measure
    measure_notes = [
        note
        for note in score.notes
        if note.track_name == track_name
        and note.voice_name == voice_name
        and note.measure_number == measure_num
    ]

    # If no notes, add a full measure rest
    if len(measure_notes) == 0:
        m21_note = m21.note.Rest()
        m21_note.quarterLength = measure_durations[measure_num]
        measure.append(m21_note)
        return

    # Process each note in order
    for note in sorted(measure_notes, key=lambda n: n.time):
        _add_note_to_measure(
            score, note, measure, current_ts, part_state, track_name, voice_name
        )


def _add_note_to_measure(
    score, note, measure, current_ts, part_state, track_name, voice_name
):
    """Create and add a music21 note object to a measure."""
    # Convert duration to fraction
    duration = note.duration * get_ratio_beat(current_ts)

    # Create note or rest
    if note.is_silence:
        m21_note = m21.note.Rest()
        m21_note.quarterLength = duration
    elif note.is_continuation:
        # Handle continuation notes (tied notes)
        m21_note_original = part_state.ref_note.get(
            (note.track_name, note.voice_name), None
        )
        m21_note = deepcopy(m21_note_original)
        if m21_note is None:
            return

        m21_note_original.tie = m21.tie.Tie("start")
        m21_note.tie = m21.tie.Tie("stop")
        m21_note.articulations = []
        m21_note.duration = m21.duration.Duration(duration)
    else:
        # Create new note or chord
        m21_note = _create_new_note(note, duration)

        # Check if this note is tied to the next note
        next_notes = [
            n
            for n in score.notes
            if n.track_name == note.track_name
            and n.voice_name == note.voice_name
            and n.beat == note.beat + note.duration
            and n.is_continuation
        ]

        if next_notes:
            part_state.ref_note[(note.track_name, note.voice_name)] = m21_note

    # Apply techniques
    m21_note = _apply_techniques(note, m21_note, measure, part_state, current_ts)

    # Insert note at the correct offset
    offset = _get_offset(note.beat, current_ts)
    if m21_note.duration.quarterLength > 0:
        measure.insert(offset, m21_note)

    # Add text comment if present
    if note.text_comment is not None:
        _add_text_comment(measure, note.text_comment, offset)


def _create_new_note(note, duration):
    """Create a new music21 note or chord object."""

    def replace_flats_to_minus(pitch):
        if isinstance(pitch, list):
            return [replace_flats_to_minus(n) for n in pitch]
        if "b" in pitch:
            return pitch.replace("b", "-")
        return pitch

    if isinstance(note.pitch, list):
        # Create chord
        m21_note = m21.chord.Chord(replace_flats_to_minus(note.pitch))
        m21_note.quarterLength = duration
    else:
        # Create single note
        m21_note = m21.note.Note(note.pitch)
        m21_note.quarterLength = duration
    return m21_note


def _add_text_comment(measure, text, offset):
    """Add a text comment to a measure."""
    text_expression = m21.expressions.TextExpression(text)
    text_expression.positionVertical = 20  # Position above the staff
    text_expression.style.fontStyle = "italic"  # Make it italic
    measure.insert(offset, text_expression)


def _add_phrase_boundaries(m21_score, measure_boundaries):
    """
    Add phrase boundaries (like repeat signs) to the score.

    Args:
        m21_score: The music21 score object
        measure_boundaries: Dictionary mapping measure numbers to boundary types (:||=repeat, coda=coda, etc.)
    """
    if not measure_boundaries:
        return

    # Process each boundary marker
    for measure_num, boundary_type in measure_boundaries.items():
        # Find all measures with this number across all parts
        for part in m21_score.parts:
            measures = part.getElementsByClass("Measure")
            measure = None

            # Find the specific measure in this part
            for m in measures:
                if m.number == measure_num:
                    measure = m
                    break

            if measure is None:
                continue

            # Handle different boundary types
            if boundary_type in ["repeat_start", "|:", "start_repeat"]:
                # Add repeat barline at the start of the measure
                repeat_obj = m21.bar.Repeat(direction="start")
                measure.leftBarline = repeat_obj

            elif boundary_type in ["repeat_end", ":|", "end_repeat"]:
                # Add repeat barline at the end of the measure
                repeat_obj = m21.bar.Repeat(direction="end")
                measure.rightBarline = repeat_obj

            elif boundary_type in ["repeat_both", ":|:", ":||:"]:
                # Add repeat barlines at both ends
                measure.leftBarline = m21.bar.Repeat(direction="start")
                measure.rightBarline = m21.bar.Repeat(direction="end")

            elif boundary_type.startswith("repeat_end_times="):
                # Extract repeat count
                try:
                    times = int(boundary_type.split("=")[1])
                    repeat_obj = m21.bar.Repeat(direction="end")
                    repeat_obj.times = times
                    measure.rightBarline = repeat_obj

                    # Add text expression to indicate the repeat count
                    text_expr = repeat_obj.getTextExpression()
                    measure.append(text_expr)
                except (ValueError, IndexError):
                    # If parsing fails, just add a normal end repeat
                    measure.rightBarline = m21.bar.Repeat(direction="end")

            elif boundary_type == "final":
                # Add final barline
                measure.rightBarline = m21.bar.Barline("final")

            elif boundary_type == "double":
                # Add double barline
                measure.rightBarline = m21.bar.Barline("double")

            elif boundary_type == "dashed":
                # Add dashed barline
                measure.rightBarline = m21.bar.Barline("dashed")

            elif boundary_type in ["coda", "segno"]:
                # Add coda or segno as text expressions
                expr = m21.expressions.TextExpression(boundary_type)
                expr.style.fontWeight = "bold"
                expr.style.fontSize = 14
                measure.insert(0, expr)

            elif boundary_type == "fine":
                # Add 'Fine' text
                expr = m21.expressions.TextExpression("Fine")
                expr.style.fontStyle = "italic"
                expr.style.fontWeight = "bold"
                measure.insert(0, expr)

            elif boundary_type.startswith("dc") or boundary_type.startswith("ds"):
                # Handle da capo and dal segno markings
                expr = m21.expressions.TextExpression(boundary_type.upper())
                expr.style.fontStyle = "italic"
                expr.style.fontWeight = "bold"
                measure.insert(0, expr)


def _init_m21_score(score):
    # Create a music21 score
    m21_score = m21.stream.Score()
    m21_score.insert(0, m21.metadata.Metadata())
    # Set the title and composer using music 21 framework
    # Set the title and composer
    m21_score.metadata.title = score.title
    m21_score.metadata.composer = score.composer

    # Add metadata
    m21_score.insert(0, m21.metadata.Metadata())

    # Create a dictionary to store parts by voice name
    parts = {}

    # Add instrument to part
    # instrument = score.instruments[0]

    # Create instruments and parts
    for idx, instrument in enumerate(score.instruments):
        # Create a part for each voice
        part = m21.stream.PartStaff()
        m21_instrument = m21.instrument.Instrument()
        m21_instrument.midiProgram = (
            instrument.gm_number - 1
        )  # music21 uses 0-127, GM uses 1-128
        m21_instrument.instrumentName = instrument.name.capitalize().replace("_", " ")
        part.insert(0, m21_instrument)

        all_voices_for_instrument = list(
            sorted(
                set(
                    [
                        note.voice_name
                        for note in score.notes
                        if note.track_name == instrument.track_name
                    ]
                )
            )
        )
        voices = []
        for idx, voice_name in enumerate(all_voices_for_instrument):
            voice = m21.stream.Voice()
            voices.append(voice)
            parts[(instrument.track_name, voice_name)] = voice

        for voice in voices:
            part.append(voice)
        # Add part to score
        m21_score.insert(0, part)

    # Group instruments by staff_group
    staff_group_map = {}
    for idx, instrument in enumerate(score.instruments):
        if instrument.staff_group is None:
            continue
        if instrument.staff_group not in staff_group_map:
            staff_group_map[instrument.staff_group] = []
        staff_group_map[instrument.staff_group].append(idx)

    # Create staff groups and add them to the score
    for group_name, part_indices in staff_group_map.items():
        if not part_indices:
            continue

        # Get the parts that belong to this group
        group_parts = []
        for idx in part_indices:
            if idx < len(m21_score.parts):
                group_parts.append(m21_score.parts[idx])

        if group_parts:
            # Create a staff group with appropriate symbol (brace for piano/keyboard, bracket for others)
            symbol = "brace" if len(group_parts) == 2 else "bracket"
            staff_group = m21.layout.StaffGroup(
                group_parts, name=f"Group {group_name}", symbol=symbol, barTogether=True
            )
            m21_score.insert(0, staff_group)

    return m21_score, parts


def _write_comments_and_harmony(score, time_sig_map, first_instrument_measures):
    last_key = None
    for chord in score.chords:
        if chord.measure_number in first_instrument_measures:
            key = None
            if chord.key != last_key:
                key = chord.key
                last_key = chord.key
            _write_comment(
                first_instrument_measures[chord.measure_number],
                chord.beat,
                key=key,
                chord=chord.chord,
                current_ts=time_sig_map[chord.measure_number],
            )


def _apply_events(score, time_sig_map, first_instrument_measures):
    for event in score.events:
        if event.event_type == "tempo":
            # Find the measure where the tempo event should be placed
            if event.measure_number in first_instrument_measures:
                measure = first_instrument_measures[event.measure_number]
                current_ts = time_sig_map[event.measure_number]
                # Create a tempo mark
                tempo_mark = m21.tempo.MetronomeMark(
                    number=event.event_value, referent=m21.note.Note(type="quarter")
                )
                # Calculate offset based on beat position
                offset = _get_offset(event.beat, current_ts)
                # Insert tempo mark at the correct offset within the measure
                measure.insert(offset, tempo_mark)


def _apply_time_signatures(m21_score, score, all_measures, first_instrument_measures):
    """
    Apply time signatures to the appropriate measures in the score.
    """
    for time_signature in score.time_signatures:
        if time_signature.measure_number in first_instrument_measures:
            measures = all_measures[time_signature.measure_number]
            for measure in measures:
                num = time_signature.time_signature[0]
                den = time_signature.time_signature[1]
                time_signature_mark = m21.meter.TimeSignature(f"{num}/{den}")
                measure.insert(0, time_signature_mark)

    m21_score.makeMeasures(inPlace=True)


def _apply_clefs(m21_score, score):
    """
    Apply clefs to the appropriate measures in the score.

    Args:
        m21_score: The music21 score to add clefs to
        score: The harmonics score object containing clef information
    """
    # Early return if no clefs
    if not score.clefs:
        return

    # Sort clefs by time, measure, and beat for consistent application
    sorted_clefs = sorted(
        score.clefs, key=lambda c: (c.time, c.measure_number or 0, c.beat or 0)
    )

    # Find parts by track name
    track_to_part = {}
    for idx, part in enumerate(m21_score.parts):
        track_name = score.instruments[idx].track_name
        track_to_part[track_name] = part

    # Apply each clef to the appropriate part and measure
    for clef_item in sorted_clefs:
        # Find the part this clef belongs to
        part = track_to_part.get(clef_item.track_name)
        if not part:
            continue

        # Skip clefs without measure numbers
        if clef_item.measure_number is None:
            continue

        # Find the measure
        measure = None
        for m in part.getElementsByClass("Measure"):
            if m.number == clef_item.measure_number:
                measure = m
                break

        if not measure:
            continue

        # Calculate offset
        offset = 0.0
        if clef_item.beat is not None and clef_item.beat > 1.0:
            # Get the current time signature for this measure
            ts = None
            for ts_obj in measure.getElementsByClass("TimeSignature"):
                ts = (ts_obj.numerator, ts_obj.denominator)
                break

            if ts:
                offset = _get_offset(clef_item.beat, ts)

        # Remove any existing clefs at the same offset
        # This is particularly important for the first measure which often has a default clef
        existing_clefs = measure.getElementsByClass("Clef")
        clefs_to_remove = []
        for existing_clef in existing_clefs:
            if (
                abs(existing_clef.offset - offset) < 0.001
            ):  # Using a small threshold for floating point comparison
                clefs_to_remove.append(existing_clef)

        # Remove the conflicting clefs
        for clef_to_remove in clefs_to_remove:
            measure.remove(clef_to_remove)

        # Now add our new clef
        _add_clef_to_measure(measure, clef_item, offset)


def _apply_key_signatures(m21_score, score):
    """
    Apply key signatures to the appropriate measures in the score.
    """
    if not score.key_signatures:
        return

    # Sort key signatures by time, measure, and beat for consistent application
    sorted_key_signatures = sorted(
        score.key_signatures,
        key=lambda ks: (ks.time, ks.measure_number or 0, ks.beat or 0),
    )

    # Apply each key signature to the appropriate part and measure
    for key_sig_item in sorted_key_signatures:
        for part in m21_score.parts:
            if not part:
                continue

            # Skip key signatures without measure numbers
            if key_sig_item.measure_number is None:
                continue

            # Find the measure
            measure = None
            for m in part.getElementsByClass("Measure"):
                if m.number == key_sig_item.measure_number:
                    measure = m
                    break

            if not measure:
                continue

            # Calculate offset
            offset = 0.0
            if key_sig_item.beat is not None and key_sig_item.beat > 1.0:
                # Get the current time signature for this measure
                ts = None
                for ts_obj in measure.getElementsByClass("TimeSignature"):
                    ts = (ts_obj.numerator, ts_obj.denominator)
                    break

                if ts:
                    offset = _get_offset(key_sig_item.beat, ts)

            # Remove any existing key signatures at the same offset
            existing_key_sigs = measure.getElementsByClass("KeySignature")
            key_sigs_to_remove = []
            for existing_key_sig in existing_key_sigs:
                if (
                    abs(existing_key_sig.offset - offset) < 0.001
                ):  # Small threshold for floating point comparison
                    key_sigs_to_remove.append(existing_key_sig)

            # Remove the conflicting key signatures
            for key_sig_to_remove in key_sigs_to_remove:
                measure.remove(key_sig_to_remove)

            # Now add our new key signature
            _add_key_signature_to_measure(measure, key_sig_item, offset)


def _get_time_sig_map(time_signatures, max_measure):
    time_sig_map = {}
    current_ts = None
    for idx in range(1, max_measure + 1):
        for ts in time_signatures:
            if ts.measure_number == idx:
                current_ts = ts.time_signature
                break
        time_sig_map[idx] = current_ts
    return time_sig_map


def _correct_xml_and_compress(m21_score, filepath):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as temp_file:
        m21_score.write("musicxml", temp_file.name)
        correct_xml_file(
            temp_file.name
        )  # TEMP : To fix 0-indexed voice issue in musescore, is there a better solution ?
        if filepath.endswith(".mxl"):
            new_filepath = convert_musicxml_to_mxl(temp_file.name)
        else:
            new_filepath = temp_file.name

    # Copy the new file to the final filepath
    shutil.copy(new_filepath, filepath)
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)
    if os.path.exists(new_filepath):
        os.remove(new_filepath)


def _write_comment(measure, beat, key=None, chord=None, current_ts=None):
    chord_text = ""
    if key is not None:
        chord_text += f"{key}: "
    if chord is not None:
        chord_text += f"{chord}"

    if key is None and chord is None:
        return

    comment_text = chord_text
    # Create a comment object
    comment = m21.expressions.TextExpression(comment_text)
    comment.style.fontStyle = "normal"
    comment.style.fontSize = 10
    # Add padding top
    comment.style.relativeY = 0.5
    comment.placement = "below"
    measure.insert(_get_offset(beat, current_ts), comment)


def _get_offset(beat, current_ts):
    offset = (beat - 1) * get_ratio_beat(current_ts)
    return offset


def _create_technique(technique):
    """Create a music21 articulation object based on the technique name."""
    # Articulations
    if technique == "staccato":
        return m21.articulations.Staccato(), "articulations"
    elif technique == "staccatissimo":
        return m21.articulations.Staccatissimo(), "articulations"
    elif technique == "marcato":
        return m21.articulations.StrongAccent(), "articulations"
    elif technique == "pizzicato":
        return m21.articulations.Pizzicato(), "articulations"

    # Accents
    elif technique == "accent":
        return m21.articulations.Accent(), "articulations"
    elif technique == "ghost_note":
        return m21.articulations.Unstress(), "articulations"

    # Dynamics
    elif technique in ["pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]:
        return m21.dynamics.Dynamic(technique), "dynamics"

    # Note effects
    elif technique == "mordent":
        return m21.expressions.Mordent(), "expressions"
    elif technique == "upper_mordent":
        return m21.expressions.InvertedMordent(), "expressions"
    elif technique == "trill":
        return m21.expressions.Trill(), "expressions"
    elif technique == "turn":
        return m21.expressions.Turn(), "expressions"
    elif technique == "tremolo":
        return m21.expressions.Tremolo(), "expressions"

    # Return None for unsupported techniques
    return None, None


def _add_clef_to_measure(measure, clef_item, offset):
    """
    Add a clef to a measure at the specified offset.

    Args:
        measure: The music21 measure to add the clef to
        clef_item: The ClefItem containing clef information
        offset: The offset within the measure to add the clef
    """
    if clef_item is None:
        return

    # Map harmonics clef names to music21 clef names
    clef_map = {
        "treble": "treble",
        "G": "treble",
        "bass": "bass",
        "F": "bass",
        "alto": "alto",
        "C": "alto",
        "tenor": "tenor",
        "soprano": "soprano",
        "mezzo-soprano": "mezzosoprano",
        "baritone": "baritone",
        "sub-bass": "subbass",
        "french": "french",
        "treble8vb": "treble8vb",
        "bass8vb": "bass8vb",
    }

    # Create the clef
    clef_name = clef_map.get(clef_item.clef_name, "treble")
    m21_clef = m21.clef.clefFromString(clef_name)
    # Apply octave change if specified
    if clef_item.octave_change is not None:
        m21_clef.octaveChange = clef_item.octave_change
    # Insert clef at the specified offset
    measure.insert(offset, m21_clef)
    return m21_clef
