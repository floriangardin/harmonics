import music21
import harmonics.score_models as models
from fractions import Fraction
import re
from typing import Dict, List, Optional, Set, Tuple
import logging
from harmonics.chord_parser import ChordParser
import shutil
import copy
import os
import tempfile
from harmonics.commons.utils_output import inverse_correct_xml_file


class MxlParserState:
    """
    Container class to hold the state of MusicXML parsing.
    Used to pass data between subfunctions during parsing.
    """

    def __init__(self):
        self.notes = []
        self.chords = []
        self.time_signatures = []
        self.tempos = []
        self.instruments = []
        self.events = []
        self.clefs = []
        self.techniques = []
        self.key_signatures = []
        self.instrument_dict = {}
        self.note_to_techniques_map = {}
        self.staff_groups = {}  # A dictionary mapping group name to list of track names

        # Metadata
        self.title = None
        self.composer = "Unknown"


def prepare_mxl(filepath):
    """
    Prepare a MusicXML file for parsing by:
    - Inverting the voice numbering
    - Removing pedal direction
    """
    suffix = "." + filepath.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_filepath = temp_file.name
        shutil.copy(filepath, temp_filepath)
        inverse_correct_xml_file(temp_filepath)
        return temp_filepath


def from_mxl(filepath):
    """
    Convert a MusicXML file to a Score object.

    Args:
        filepath: Path to the MusicXML file to parse

    Returns:
        models.Score: Score object containing all extracted information
    """

    filepath = prepare_mxl(filepath)

    # Parse the MusicXML file using music21
    m21_score = music21.converter.parse(filepath)

    # Remove the temporary file
    os.remove(filepath)

    # Initialize parser state
    state = MxlParserState()

    # Extract metadata
    extract_metadata(m21_score, state)

    # Extract staff groups
    extract_staff_groups(m21_score, state)

    # Process each part in the score
    process_parts(m21_score, state)

    # Extract default clefs
    extract_default_clefs(m21_score, state)

    # Extract default key signature
    extract_default_key_signature(m21_score, state)

    # Create and return the score
    score = create_score(state)
    score.notes = refactor_voices(score.notes)
    return score


def extract_metadata(m21_score, state):
    """Extract title, movement name, and composer from the score metadata."""
    metadata = m21_score.metadata

    state.title = metadata.title if metadata and metadata.title else None
    movementName = (
        metadata.movementName if metadata and metadata.movementName else "Untitled"
    )
    state.composer = metadata.composer if metadata and metadata.composer else "Unknown"

    # Use movement name as title if title is None
    state.title = state.title if state.title else movementName


def process_parts(m21_score, state):
    """Process each part in the score."""
    for part_idx, part in enumerate(m21_score.parts):
        # Extract and add instrument information
        track_name = process_instrument(part, part_idx, state)

        # Process spanners (crescendo, diminuendo, slurs)
        process_spanners(part, track_name, state)

        # Process measures
        process_measures(part, part_idx, track_name, state)


def process_instrument(part, part_idx, state):
    """Extract instrument information from a part and add it to the state."""
    m21_instrument = part.getInstrument()
    instrument_name = (
        m21_instrument.instrumentName
        if m21_instrument.instrumentName
        else f"Instrument_{part_idx}"
    )

    # Convert instrument name to lowercase with underscores
    name = instrument_name.lower().replace(" ", "_")
    track_name = f"T{part_idx+1}"

    # Get GM number (default to 1 if not specified)
    gm_number = (
        m21_instrument.midiProgram + 1 if m21_instrument.midiProgram is not None else 1
    )

    # Create instrument item
    instrument = models.InstrumentItem(
        time=0,  # We don't care about time
        track_name=track_name,
        track_index=part_idx,
        gm_number=gm_number,
        name=name,
    )

    state.instruments.append(instrument)
    state.instrument_dict[name] = track_name

    return track_name


def process_spanners(part, track_name, state):
    """Process spanners like crescendo, diminuendo, and slurs."""
    for spanner in part.recurse().getElementsByClass("Spanner"):
        spanner_type = type(spanner).__name__.lower()
        technique_name = map_spanner_type_to_technique(spanner_type)

        if technique_name and hasattr(spanner, "getSpannedElements"):
            spanned_elements = spanner.getSpannedElements()
            if spanned_elements:
                first_note = spanned_elements[0]
                last_note = spanned_elements[-1]

                # Calculate measure and beat for first and last notes
                first_measure = first_note.measureNumber
                last_measure = last_note.measureNumber

                # Get the offset within the measure (1-indexed)
                first_beat = first_note.offset + 1.0
                last_beat = last_note.offset + 1.0

                # Create a technique item for spanning techniques
                technique_item = models.TechniqueItem(
                    time_start=0,  # We don't care about time
                    time_end=0,  # We don't care about time
                    measure_number_start=first_measure,
                    beat_start=first_beat,
                    measure_number_end=last_measure,
                    beat_end=last_beat,
                    track_name=track_name,
                    technique=technique_name,
                )
                state.techniques.append(technique_item)

                # Add the technique start to the first note
                note_key = (track_name, first_measure, first_beat)
                if note_key not in state.note_to_techniques_map:
                    state.note_to_techniques_map[note_key] = []
                state.note_to_techniques_map[note_key].append(technique_name)

                # Add the technique end to the last note (prefixed with !)
                note_key = (track_name, last_measure, last_beat)
                if note_key not in state.note_to_techniques_map:
                    state.note_to_techniques_map[note_key] = []
                state.note_to_techniques_map[note_key].append(f"!{technique_name}")


def map_spanner_type_to_technique(spanner_type):
    """Map spanner type to technique name."""
    if spanner_type == "crescendo":
        return "crescendo"
    elif spanner_type in ["diminuendo", "decrescendo"]:
        return "diminuendo"
    elif spanner_type == "slur":
        return "legato"
    return None


def process_measures(part, part_idx, track_name, state):
    """Process all measures in a part."""
    current_ts = None
    for measure in part.recurse().getElementsByClass("Measure"):
        measure_notes = []
        measure_number = measure.number if measure.number is not None else 1
        if measure.timeSignature is not None:
            current_ts = (
                measure.timeSignature.numerator,
                measure.timeSignature.denominator,
            )

        # Process key signatures (only process once per measure, on the first part)
        if part_idx == 0:
            process_key_signatures(measure, measure_number, state)

        # Process clefs
        process_clefs(measure, measure_number, track_name, state)

        # Process time signatures
        process_time_signatures(measure, measure_number, state)

        # Process tempo markings
        process_tempo_markings(measure, measure_number, state, current_ts)

        # Process voices and notes
        measure_notes = process_voices(measure, measure_number, track_name, state)

        # Process comments and chord symbols
        process_comments_and_chords(measure, measure_number, measure_notes, state)

        state.notes.extend(measure_notes)


def process_key_signatures(measure, measure_number, state):
    """Process key signatures in a measure."""
    for ks in measure.getElementsByClass("KeySignature"):
        # Get the count of sharps or flats
        sharps = ks.sharps

        # Convert to string of accidentals ('bbb' for 3 flats, '###' for 3 sharps)
        ks_string = ""
        if sharps > 0:
            ks_string = "#" * sharps
        elif sharps < 0:
            ks_string = "b" * abs(sharps)

        # Get beat position (1-indexed)
        beat = ks.offset + 1.0

        # Create KeySignatureItem
        ks_item = models.KeySignatureItem(
            time=0,  # We don't care about time
            measure_number=measure_number,
            beat=beat,
            key_signature=ks_string,
        )
        state.key_signatures.append(ks_item)


def process_clefs(measure, measure_number, track_name, state):
    """Process clefs in a measure."""
    for clef_element in measure.getElementsByClass("Clef"):
        # Map music21 clef names to our clef names
        clef_name = map_clef_name(clef_element)

        # Get octave change if any
        octave_change = clef_element.octaveChange

        # Get beat position (1-indexed)
        beat = clef_element.offset + 1.0

        # Create ClefItem
        clef_item = models.ClefItem(
            time=0,  # We don't care about time
            track_name=track_name,
            clef_name=clef_name,
            octave_change=octave_change,
            measure_number=measure_number,
            beat=beat,
        )
        state.clefs.append(clef_item)


def map_clef_name(clef_element):
    """Map music21 clef names to our clef format."""
    clef_name = clef_element.sign.lower()
    if clef_name == "g":
        clef_name = "treble"
    elif clef_name == "f":
        clef_name = "bass"
    elif clef_name == "c":
        # Determine specific C clef type (alto, tenor, etc.) based on line
        if clef_element.line == 3:
            clef_name = "alto"
        elif clef_element.line == 4:
            clef_name = "tenor"
        else:
            clef_name = "C"  # Generic C clef
    return clef_name


def process_time_signatures(measure, measure_number, state):
    """Process time signatures in a measure."""
    for ts in measure.getElementsByClass("TimeSignature"):
        time_signature = models.TimeSignatureItem(
            time=0,  # We don't care about time
            measure_number=measure_number,
            time_signature=(ts.numerator, ts.denominator),
        )
        state.time_signatures.append(time_signature)


def _get_beat_from_offset(offset, current_ts):
    ratio_beat = Fraction(4, current_ts[1])
    return (offset / ratio_beat) + 1


def process_tempo_markings(measure, measure_number, state, current_ts):
    """Process tempo markings in a measure."""
    for tempo_mark in measure.getElementsByClass("MetronomeMark"):

        real_tempo = (
            tempo_mark.number
            if tempo_mark.number is not None
            else tempo_mark._numberSounding
        )
        offset = tempo_mark.offset
        beat = _get_beat_from_offset(offset, current_ts)
        tempo = models.TempoItem(
            time=0,  # We don't care about time
            tempo=real_tempo,
            measure_number=measure_number,
            beat=beat,
            figure=tempo_mark.referent.type,
        )
        state.tempos.append(tempo)

        # Add as an event also
        event = models.EventItem(
            time=0,  # We don't care about time
            measure_number=measure_number,
            beat=beat,
            event_type="tempo",
            event_value=real_tempo,
        )
        state.events.append(event)


def process_voices(measure, measure_number, track_name, state):
    """Process voices and notes in a measure."""
    measure_notes = []
    if len(measure.recurse().getElementsByClass("Voice")) == 0:
        for note_element in measure.recurse().getElementsByClass(
            ["Note", "Chord", "Rest", "Continuation"]
        ):
            note = process_note(note_element, measure_number, track_name, "v1", state)
            measure_notes.append(note)
    else:
        for voice in measure.recurse().getElementsByClass("Voice"):
            voice_name = "v" + str(voice._id)
            for note_element in voice.recurse().getElementsByClass(
                ["Note", "Chord", "Rest", "Continuation"]
            ):
                note = process_note(
                    note_element, measure_number, track_name, voice_name, state
                )
                measure_notes.append(note)

    # Extract dynamics and attach to nearest notes
    process_dynamics(measure, measure_notes, track_name)

    return measure_notes


def process_dynamics(measure, measure_notes, track_name):
    """Process dynamics in a measure and attach them to the nearest note."""
    if not measure_notes:
        return

    for dynamic in measure.getElementsByClass("Dynamic"):
        # Get the dynamic text
        dynamic_text = dynamic.value.lower()
        dynamic_offset = dynamic.offset + 1.0  # Convert to 1-indexed beat

        # Find the nearest note
        attach_dynamic_to_nearest_note(dynamic_text, dynamic_offset, measure_notes)


def attach_dynamic_to_nearest_note(dynamic_text, dynamic_offset, measure_notes):
    """Attach a dynamic marking to the nearest note in the measure."""
    nearest_note = None
    min_distance = float("inf")

    for note in measure_notes:
        distance = abs(note.beat - dynamic_offset)
        if distance < min_distance:
            min_distance = distance
            nearest_note = note

    if nearest_note and not nearest_note.is_silence:
        # Add the dynamic to the note's techniques
        if dynamic_text not in nearest_note.techniques:
            nearest_note.techniques.append(dynamic_text)


def refactor_voices(notes):
    """
    Refactor the voices to start with v1 and be contiguous.
    This grouping of voices is done grouped by track_name.
    """
    # Group notes by track_name
    notes_by_track = {}
    for note in notes:
        if note.track_name not in notes_by_track:
            notes_by_track[note.track_name] = []
        notes_by_track[note.track_name].append(note)

    # For each track, refactor voice names
    for track_name, track_notes in notes_by_track.items():
        # Get unique voice names in this track
        voice_names = sorted(set(note.voice_name for note in track_notes))

        # Create mapping from old voice names to new voice names
        voice_mapping = {old_name: f"v{i+1}" for i, old_name in enumerate(voice_names)}

        # Apply the mapping to all notes in this track
        for note in track_notes:
            note.voice_name = voice_mapping[note.voice_name]
    return notes


def process_note(note_element, measure_number, track_name, voice_name, state):
    """Process a single note element."""
    # Calculate beat position (1-indexed)
    beat = note_element.offset + 1.0

    # Get duration
    duration = float(note_element.quarterLength)

    # Check if it's a rest
    is_silence = note_element.isRest

    # Get pitch or pitches
    pitch = extract_pitch(note_element, is_silence)

    # Check for ties
    is_continuation = check_for_tie(note_element)

    # Get techniques (articulations, expressions, dynamics)
    note_techniques, global_techniques = extract_techniques(
        note_element, measure_number, beat, track_name, state
    )

    # Create note item
    note_item = models.NoteItem(
        time=0,  # We don't care about time
        duration=duration,
        pitch=pitch,
        is_silence=is_silence,
        is_continuation=is_continuation,
        track_name=track_name,
        voice_name=voice_name,
        techniques=note_techniques,
        global_techniques=global_techniques,
        measure_number=measure_number,
        beat=beat,
    )

    return note_item


def extract_pitch(note_element, is_silence):
    """Extract pitch information from a note element."""
    if is_silence:
        return None

    if hasattr(note_element, "pitches"):  # It's a chord
        return [p.nameWithOctave.replace("-", "b") for p in note_element.pitches]
    else:  # It's a note
        return note_element.nameWithOctave.replace("-", "b")


def check_for_tie(note_element):
    """Check if a note is tied to a previous note."""
    if hasattr(note_element, "tie") and note_element.tie is not None:
        if note_element.tie.type in ["continue", "stop"]:
            return True
    return False


def extract_techniques(note_element, measure_number, beat, track_name, state):
    """Extract techniques (articulations, expressions, dynamics) from a note."""
    note_techniques = []
    global_techniques = []

    # Add articulations
    for articulation in note_element.articulations:
        technique_name = type(articulation).__name__.lower()
        technique = map_articulation_to_technique(technique_name)
        if technique:
            note_techniques.append(technique)

    # Add expressions
    for expression in note_element.expressions:
        technique_name = type(expression).__name__.lower()
        technique = map_expression_to_technique(technique_name)
        if technique:
            note_techniques.append(technique)

    # Add techniques from spanners (crescendo, diminuendo, legato)
    note_key = (track_name, measure_number, beat)
    if note_key in state.note_to_techniques_map:
        note_techniques.extend(state.note_to_techniques_map[note_key])

    return note_techniques, global_techniques


def map_articulation_to_technique(technique_name):
    """Map music21 articulation names to our technique names."""
    mapping = {
        "accent": "accent",
        "staccato": "staccato",
        "staccatissimo": "staccatissimo",
        "strongaccent": "marcato",
        "pizzicato": "pizzicato",
    }
    return mapping.get(technique_name)


def map_expression_to_technique(technique_name):
    """Map music21 expression names to our technique names."""
    mapping = {
        "trill": "trill",
        "turn": "turn",
        "mordent": "mordent",
        "invertedmordent": "upper_mordent",
        "tremolo": "tremolo",
    }
    return mapping.get(technique_name)


def process_comments_and_chords(measure, measure_number, measure_notes, state):
    """Process text expressions for chord symbols and comments."""
    last_key = None

    for expression in measure.getElementsByClass("TextExpression"):
        # Check if this is a chord/harmony comment
        text = expression.content
        offset = expression.offset + 1.0  # Convert to 1-indexed beat

        is_chord = ChordParser().is_chord(text)

        if is_chord:
            # Process chord symbol
            chord_item = process_chord_symbol(text, offset, measure_number, last_key)
            if chord_item:
                state.chords.append(chord_item)
                # Update last_key if this expression set a new key
                if chord_item.new_key:
                    last_key = chord_item.key
        else:
            # Process text comment
            attach_comment_to_nearest_note(text, offset, measure_notes)


def process_chord_symbol(text, offset, measure_number, last_key):
    """Process a chord symbol text expression."""
    key = None
    chord_symbol = None
    new_key = False

    if ":" in text:
        # Format might be "C: V7/V" or similar
        key, chord_symbol = text.split(":", 1)
        key = key.strip()
        chord_symbol = chord_symbol.strip()
        new_key = True
    else:
        # Just a chord symbol like "iv65"
        chord_symbol = text.strip()
        key = last_key

    if chord_symbol or key:
        return models.ChordItem(
            time=0,  # We don't care about time
            beat=offset,
            measure_number=measure_number,
            duration=0.0,  # Duration doesn't apply to chord symbols
            chord=chord_symbol if chord_symbol else None,
            key=key,
            new_key=new_key,
        )
    return None


def attach_comment_to_nearest_note(text, comment_beat, measure_notes):
    """Attach a text comment to the nearest note in the measure."""
    nearest_note = None
    min_distance = float("inf")

    for note in measure_notes:
        distance = abs(note.beat - comment_beat)
        if distance < min_distance:
            min_distance = distance
            nearest_note = note

    if attach_technique_to_note(nearest_note, text):
        return

    if nearest_note:
        nearest_note.text_comment = text


def attach_technique_to_note(note, technique):
    """Attach a technique to a note."""
    technique_dict = {
        "$pedal_start": "pedal",
        "$pedal_stop": "!pedal",
        # Add common dynamic markings
        "pianissimo": "pp",
        "piano": "p",
        "mezzopiano": "mp",
        "mezzoforte": "mf",
        "forte": "f",
        "fortissimo": "ff",
        "sforzando": "fz",
        "fortepiano": "fp",
    }
    if technique in technique_dict:
        note.techniques.append(technique_dict[technique])
        return True
    return False


def extract_default_clefs(m21_score, state):
    """Extract default clefs from the first measure of each part."""
    for part_idx, part in enumerate(m21_score.parts):
        track_name = f"T{part_idx+1}"
        first_measure = part.measure(1)
        if first_measure:
            default_clef = first_measure.getContextByClass("Clef")
            if default_clef:
                # If there's a default clef, add it to measure 1 beat 1 if we don't already have one
                # Check if we already have a clef for this voice in measure 1
                has_m1_clef = any(
                    c.track_name == track_name
                    and c.measure_number == 1
                    and c.beat == 1.0
                    for c in state.clefs
                )

                if not has_m1_clef:
                    # Map music21 clef to our clef format
                    clef_name = map_clef_name(default_clef)

                    # Create default clef at the beginning
                    default_clef_item = models.ClefItem(
                        time=0,
                        track_name=track_name,
                        clef_name=clef_name,
                        octave_change=default_clef.octaveChange,
                        measure_number=1,
                        beat=1.0,
                    )
                    state.clefs.append(default_clef_item)


def extract_default_key_signature(m21_score, state):
    """Extract default key signature from the score if not already found."""
    if len(state.key_signatures) == 0:
        first_part = m21_score.parts[0] if m21_score.parts else None
        if first_part:
            default_key = first_part.getContextByClass("KeySignature")
            if default_key:
                # Convert sharps to string of accidentals
                sharps = default_key.sharps
                ks_string = ""
                if sharps > 0:
                    ks_string = "#" * sharps
                elif sharps < 0:
                    ks_string = "b" * abs(sharps)

                # Add default key signature for the first measure
                default_ks_item = models.KeySignatureItem(
                    time=0, measure_number=1, beat=1.0, key_signature=ks_string
                )
                state.key_signatures.append(default_ks_item)


def extract_staff_groups(m21_score, state):
    """
    Extract staff groups (e.g., piano with treble and bass clefs) from the score.

    Args:
        m21_score: The music21 score
        state: The parser state to update
    """
    # Check for spanners in the score
    spanners = m21_score.spannerBundle
    staff_groups = spanners.getByClass("StaffGroup")

    if not staff_groups:
        # Try alternative method if no StaffGroup found in spannerBundle
        staff_groups = m21_score.recurse().getElementsByClass("StaffGroup")

    # Process each staff group
    for idx, group in enumerate(staff_groups):
        # Get all parts that are part of this group
        spanned_parts = group.getSpannedElements()

        # Generate track names for each part in the group
        track_names = []
        for part_idx, part in enumerate(m21_score.parts):
            if part in spanned_parts:
                track_names.append(f"T{part_idx+1}")

        # Only add the group if there are parts in it
        if track_names:
            # Set a default group name if none provided
            group_name = group.name if group.name else f"group_{idx+1}"
            # Clean the group name to remove spaces and special characters
            group_name = group_name.lower().replace(" ", "_").replace("-", "_")

            # Store the staff group in the state
            state.staff_groups[group_name] = track_names

    # If no staff groups were found but there are exactly two parts, and we recognize
    # them as typical piano parts (treble and bass clef), create a piano group
    if not state.staff_groups and len(m21_score.parts) == 2:
        # Check if the first part has a treble clef and the second has a bass clef
        part1 = m21_score.parts[0]
        part2 = m21_score.parts[1]

        if part1 and part2:
            part1_clef = (
                part1.recurse().getElementsByClass("Clef")[0]
                if part1.recurse().getElementsByClass("Clef")
                else None
            )
            part2_clef = (
                part2.recurse().getElementsByClass("Clef")[0]
                if part2.recurse().getElementsByClass("Clef")
                else None
            )

            # Check if it's a typical piano configuration
            if (
                part1_clef
                and part1_clef.name == "treble"
                and part2_clef
                and part2_clef.name == "bass"
            ):
                state.staff_groups["piano"] = ["T1", "T2"]


def create_score(state):
    """Create a Score object from the parser state."""
    score = models.Score(
        chords=state.chords,
        notes=state.notes,
        time_signatures=state.time_signatures,
        tempos=state.tempos,
        events=state.events,
        instruments=state.instruments,
        techniques=state.techniques,
        clefs=state.clefs,
        key_signatures=state.key_signatures,
        title=state.title or "Untitled",
        composer=state.composer or "Unknown",
        staff_groups=state.staff_groups,  # Add staff groups to the Score
    )
    return score
