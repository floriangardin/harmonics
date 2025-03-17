import music21
import harmonics.score_models as models
from fractions import Fraction
import re
from typing import Dict, List, Optional, Set, Tuple
import logging
from harmonics.chord_parser import ChordParser


def from_mxl(filepath):
    """
    Convert a MusicXML file to a Score object.

    Args:
        filepath: Path to the MusicXML file to parse

    Returns:
        models.Score: Score object containing all extracted information
    """
    # Parse the MusicXML file using music21
    m21_score = music21.converter.parse(filepath)

    # Initialize lists for score components
    notes = []
    chords = []
    time_signatures = []
    tempos = []
    instruments = []
    events = []
    clefs = []  # Add clefs list
    techniques = []  # Add techniques list for spanners
    key_signatures = []  # Add key signatures list

    # Extract metadata
    metadata = m21_score.metadata
    title = metadata.title if metadata and metadata.title else None
    movementName = (
        metadata.movementName if metadata and metadata.movementName else "Untitled"
    )
    composer = metadata.composer if metadata and metadata.composer else "Unknown"
    title = title if title else movementName

    # Keep track of the last processed time
    current_time = 0

    instrument_dict = {}

    # Process spanners (crescendo, diminuendo, slurs)
    # Create a mapping from note to techniques that will be applied
    note_to_techniques_map = {}

    # Process each part in the score
    for part_idx, part in enumerate(m21_score.parts):
        # Extract instrument information
        m21_instrument = part.getInstrument()
        instrument_name = (
            m21_instrument.instrumentName
            if m21_instrument.instrumentName
            else f"Instrument_{part_idx}"
        )
        instrument_name = instrument_name.lower().replace(" ", "_")
        # Convert instrument name to lowercase with underscores
        name = instrument_name.lower().replace(" ", "_")
        track_name = f"T{part_idx+1}"
        # Get GM number (default to 1 if not specified)
        gm_number = (
            m21_instrument.midiProgram + 1
            if m21_instrument.midiProgram is not None
            else 1
        )

        # Create instrument item
        instrument = models.InstrumentItem(
            time=0,  # We don't care about time
            track_name=track_name,
            track_index=part_idx,
            gm_number=gm_number,
            name=name,
        )
        instruments.append(instrument)
        instrument_dict[name] = track_name
        comment_notes = {} # Indexed by (measure, beat, track)

        # Process spanners (crescendo, diminuendo, slurs)
        for spanner in part.getElementsByClass("Spanner"):
            spanner_type = type(spanner).__name__.lower()
            technique_name = None
            # Map spanner type to technique name
            if spanner_type == "crescendo":
                technique_name = "crescendo"
            elif spanner_type in ["diminuendo", "decrescendo"]:
                technique_name = "diminuendo"
            elif spanner_type == "slur":
                technique_name = "legato"

            if technique_name and hasattr(spanner, "getSpannedElements"):
                spanned_elements = spanner.getSpannedElements()
                if spanned_elements:
                    # Add the technique to the first and last note
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
                    techniques.append(technique_item)

                    # Add the technique start to the first note
                    note_key = (track_name, first_measure, first_beat)
                    if note_key not in note_to_techniques_map:
                        note_to_techniques_map[note_key] = []
                    note_to_techniques_map[note_key].append(technique_name)

                    # Add the technique end to the last note (prefixed with !)
                    note_key = (track_name, last_measure, last_beat)
                    if note_key not in note_to_techniques_map:
                        note_to_techniques_map[note_key] = []
                    note_to_techniques_map[note_key].append(f"!{technique_name}")

        # Process measures
        
        for measure in part.getElementsByClass("Measure"):
            measure_notes = []
            measure_number = measure.number if measure.number is not None else 1

            # Process key signatures (only process once per measure, on the first part)
            if part_idx == 0:
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
                    key_signatures.append(ks_item)

            # Process clefs
            for clef_element in measure.getElementsByClass("Clef"):
                # Map music21 clef names to our clef names
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
                clefs.append(clef_item)

            # Process time signatures
            for ts in measure.getElementsByClass("TimeSignature"):
                time_signature = models.TimeSignatureItem(
                    time=0,  # We don't care about time
                    measure_number=measure_number,
                    time_signature=(ts.numerator, ts.denominator),
                )
                time_signatures.append(time_signature)

            # Process tempo markings
            for tempo_mark in measure.getElementsByClass("MetronomeMark"):
                real_tempo = tempo_mark.number if tempo_mark.number is not None else tempo_mark._numberSounding
                tempo = models.TempoItem(
                    time=0,  # We don't care about time
                    tempo=real_tempo,
                    measure_number=measure_number,
                    beat=1.0,  # Default to first beat if not specified
                    figure=tempo_mark.referent.type,
                )
                tempos.append(tempo)

                # Add as an event also
                event = models.EventItem(
                    time=0,  # We don't care about time
                    measure_number=measure_number,
                    beat=1.0,  # Default to first beat
                    event_type="tempo",
                    event_value=real_tempo,
                )
                events.append(event)
            # Process notes
            for note_element in measure.notesAndRests:
                # Calculate beat position (1-indexed)
                beat = note_element.offset + 1.0

                # Get duration
                duration = float(note_element.quarterLength)

                # Check if it's a rest
                is_silence = note_element.isRest

                # Get pitch or pitches
                pitch = None
                if not is_silence:
                    if hasattr(note_element, "pitches"):  # It's a chord
                        pitch = [
                            p.nameWithOctave.replace("-", "b")
                            for p in note_element.pitches
                        ]
                    else:  # It's a note
                        pitch = note_element.nameWithOctave.replace("-", "b")

                # Check for ties
                is_continuation = False
                if hasattr(note_element, "tie") and note_element.tie is not None:
                    if note_element.tie.type in ["continue", "stop"]:
                        is_continuation = True

                # Get techniques (articulations, expressions, dynamics)
                techniques = []
                global_techniques = []

                # Add articulations
                for articulation in note_element.articulations:
                    technique_name = type(articulation).__name__.lower()
                    # Map music21 articulation names to our technique names
                    if technique_name == "accent":
                        techniques.append("accent")
                    elif technique_name == "staccato":
                        techniques.append("staccato")
                    elif technique_name == "staccatissimo":
                        techniques.append("staccatissimo")
                    elif technique_name == "strongaccent":
                        techniques.append("marcato")
                    elif technique_name == "pizzicato":
                        techniques.append("pizzicato")
                    # Add more mappings as needed

                # Add expressions
                for expression in note_element.expressions:
                    technique_name = type(expression).__name__.lower()
                    if technique_name == "trill":
                        techniques.append("trill")
                    elif technique_name == "turn":
                        techniques.append("turn")
                    elif technique_name == "mordent":
                        techniques.append("mordent")
                    elif technique_name == "invertedmordent":
                        techniques.append("upper_mordent")
                    elif technique_name == "tremolo":
                        techniques.append("tremolo")
                    # Add more mappings as needed

                # Look for dynamics near this note
                for dynamic in measure.getElementsByClass("Dynamic"):
                    if abs(dynamic.offset - note_element.offset) < 0.1:
                        # This dynamic applies to this note
                        dynamic_text = dynamic.value.lower()
                        if dynamic_text in [
                            "pppp",
                            "ppp",
                            "pp",
                            "p",
                            "mp",
                            "mf",
                            "f",
                            "ff",
                            "fff",
                        ]:
                            global_techniques.append(dynamic_text)

                # Add techniques from spanners (crescendo, diminuendo, legato)
                note_key = (track_name, measure_number, beat)
                if note_key in note_to_techniques_map:
                    techniques.extend(note_to_techniques_map[note_key])

                # Create note item
                note_item = models.NoteItem(
                    time=0,  # We don't care about time
                    duration=duration,
                    pitch=pitch,
                    is_silence=is_silence,
                    is_continuation=is_continuation,
                    track_name=track_name,
                    techniques=techniques,
                    global_techniques=global_techniques,
                    measure_number=measure_number,
                    beat=beat,
                )
                measure_notes.append(note_item)

                            # Process comments for chord symbols
            last_key = None
            for expression in measure.getElementsByClass("TextExpression"):
                # Check if this is a chord/harmony comment
                text = expression.content
                offset = expression.offset + 1.0  # Convert to 1-indexed beat

                is_chord = ChordParser().is_chord(text)

                if is_chord:
                    # Try to extract key and chord information
                    key = None
                    chord_symbol = None
                    if ":" in text:
                        # Format might be "C: V7/V" or similar
                        key, chord_symbol = text.split(":", 1)
                        key = key.strip()
                        chord_symbol = chord_symbol.strip()
                        last_key = key
                    else:
                        # Just a chord symbol like "iv65"
                        chord_symbol = text.strip()

                    if chord_symbol or key:
                        chord_item = models.ChordItem(
                            time=0,  # We don't care about time
                            beat=offset,
                            measure_number=measure_number,
                            duration=0.0,  # Duration doesn't apply to chord symbols
                            chord=chord_symbol if chord_symbol else None,
                            key=last_key,
                            new_key=key is not None,
                        )
                        chords.append(chord_item)
                else: # Is a generic comment
                    # If it's not a chord symbol, treat it as a text comment for this part
                    # Find the nearest note to attach this comment to
                    nearest_note = None
                    min_distance = float('inf')
                    comment_beat = expression.offset + 1.0
                    for note in measure_notes:
                        distance = abs(note.beat - comment_beat)
                        if distance < min_distance:
                            min_distance = distance
                            nearest_note = note
                    if nearest_note:
                        nearest_note.text_comment = text
                    
            notes.extend(measure_notes)
    # Extract default clefs from the first measure of each part
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
                    for c in clefs
                )

                if not has_m1_clef:
                    # Map music21 clef to our clef format
                    clef_name = default_clef.sign.lower()
                    if clef_name == "g":
                        clef_name = "treble"
                    elif clef_name == "f":
                        clef_name = "bass"
                    elif clef_name == "c":
                        if default_clef.line == 3:
                            clef_name = "alto"
                        elif default_clef.line == 4:
                            clef_name = "tenor"
                        else:
                            clef_name = "C"

                    # Create default clef at the beginning
                    default_clef_item = models.ClefItem(
                        time=0,
                        track_name=track_name,
                        clef_name=clef_name,
                        octave_change=default_clef.octaveChange,
                        measure_number=1,
                        beat=1.0,
                    )
                    clefs.append(default_clef_item)

    # Extract default key signature from the score if not already found
    if len(key_signatures) == 0:
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
                key_signatures.append(default_ks_item)

    # Create and return the score
    score = models.Score(
        chords=chords,
        notes=notes,
        time_signatures=time_signatures,
        tempos=tempos,
        events=events,
        instruments=instruments,
        techniques=techniques,  # Add techniques to the score
        clefs=clefs,  # Add clefs to score
        key_signatures=key_signatures,  # Add key signatures to score
        title=title,
        composer=composer,
    )

    return score
