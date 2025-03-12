import music21
import harmonics.score_models as models
from fractions import Fraction
import re
from typing import Dict, List, Optional, Set, Tuple
import logging


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
        voice_name = f"T{part_idx+1}"
        # Get GM number (default to 1 if not specified)
        gm_number = (
            m21_instrument.midiProgram + 1
            if m21_instrument.midiProgram is not None
            else 1
        )

        # Create instrument item
        instrument = models.InstrumentItem(
            time=0,  # We don't care about time
            voice_name=voice_name,
            voice_index=part_idx,
            gm_number=gm_number,
            name=name,
        )
        instruments.append(instrument)
        instrument_dict[name] = voice_name
        # Process measures
        for measure in part.getElementsByClass("Measure"):
            measure_number = measure.number if measure.number is not None else 1

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
                tempo = models.TempoItem(
                    time=0,  # We don't care about time
                    tempo=int(tempo_mark.number),
                    measure_number=measure_number,
                    beat=1.0,  # Default to first beat if not specified
                )
                tempos.append(tempo)

                # Add as an event also
                event = models.EventItem(
                    time=0,  # We don't care about time
                    measure_number=measure_number,
                    beat=1.0,  # Default to first beat
                    event_type="tempo",
                    event_value=int(tempo_mark.number),
                )
                events.append(event)

            # Process comments for chord symbols
            last_key = None
            for expression in measure.getElementsByClass("TextExpression"):
                # Check if this is a chord/harmony comment
                text = expression.content
                offset = expression.offset + 1.0  # Convert to 1-indexed beat

                # Try to extract key and chord information
                key = None
                chord_symbol = None

                if ":" in text:
                    # Format might be "C: Cmaj7" or similar
                    key, chord_symbol = text.split(":", 1)
                    key = key.strip()
                    chord_symbol = chord_symbol.strip()
                    last_key = key
                else:
                    # Just a chord symbol like "Cmaj7"
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

                # Create note item
                note_item = models.NoteItem(
                    time=0,  # We don't care about time
                    duration=duration,
                    pitch=pitch,
                    is_silence=is_silence,
                    is_continuation=is_continuation,
                    voice_name=voice_name,
                    techniques=techniques,
                    global_techniques=global_techniques,
                    measure_number=measure_number,
                    beat=beat,
                )
                notes.append(note_item)

    # Create and return the score
    score = models.Score(
        chords=chords,
        notes=notes,
        time_signatures=time_signatures,
        tempos=tempos,
        events=events,
        instruments=instruments,
        techniques=[],  # Not supporting technique lines for now
        title=title,
        composer=composer,
    )

    return score
