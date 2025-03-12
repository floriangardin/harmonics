import music21 as m21
from fractions import Fraction
import re
from typing import Dict, List, Optional, Set
from copy import deepcopy


def to_mxl(filepath, score):
    """
    Convert a score to a MusicXML file.

    Args:
        filepath: Path to save the MusicXML file
        score: Score object containing notes, chords, time signatures, etc.
    """
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

    # Create instruments and parts
    for instrument in score.instruments:
        # Create a part for each voice
        part = m21.stream.Part()
        part.id = instrument.voice_name

        # Add instrument to part
        m21_instrument = m21.instrument.Instrument()
        m21_instrument.midiProgram = (
            instrument.gm_number - 1
        )  # music21 uses 0-127, GM uses 1-128
        part.insert(0, m21_instrument)

        # Store part in dictionary
        parts[instrument.voice_name] = part

        # Add part to score
        m21_score.append(part)

    first_instrument_measures = {}
    all_measures = {}
    # Add measures to parts
    if score.notes:
        max_measure = max(
            note.measure_number
            for note in score.notes
            if note.measure_number is not None
        )

        # Create measures for each part
        idx = -1
        for voice_name, part in parts.items():
            idx += 1
            # Get time signatures for this part
            time_sigs = sorted(score.time_signatures, key=lambda ts: ts.time)
            current_ts_idx = 0
            current_ts = time_sigs[0].time_signature if time_sigs else (4, 4)

            # Get tempo markings
            tempos = sorted(score.tempos, key=lambda t: t.time)
            current_tempo_idx = 0

            # Track the last chord and key to only add when they change
            last_chord = None
            last_key = None

            # Create measures
            for measure_num in range(1, max_measure + 1):
                measure = m21.stream.Measure(number=measure_num)
                all_measures[measure_num] = all_measures.get(measure_num, []) + [
                    measure
                ]
                if idx == 0:
                    first_instrument_measures[measure_num] = measure
                # Add time signature if it changes at this measure
                while current_ts_idx < len(time_sigs) and any(
                    note.measure_number == measure_num
                    and note.beat == 1.0
                    and note.time == time_sigs[current_ts_idx].time
                    for note in score.notes
                    if note.measure_number is not None
                ):
                    ts = time_sigs[current_ts_idx]
                    current_ts = ts.time_signature
                    m21_ts = m21.meter.TimeSignature(f"{current_ts[0]}/{current_ts[1]}")
                    measure.insert(0, m21_ts)
                    current_ts_idx += 1
                    if current_ts_idx >= len(time_sigs):
                        break

                # Add tempo marking if it changes at this measure
                while (
                    current_tempo_idx < len(tempos)
                    and tempos[current_tempo_idx].measure_number == measure_num
                    and tempos[current_tempo_idx].beat == 1.0
                ):
                    tempo = tempos[current_tempo_idx]
                    m21_tempo = m21.tempo.MetronomeMark(number=tempo.tempo)
                    measure.insert(0, m21_tempo)
                    current_tempo_idx += 1
                    if current_tempo_idx >= len(tempos):
                        break

                # Add notes for this voice and measure
                measure_notes = [
                    note
                    for note in score.notes
                    if note.voice_name == voice_name
                    and note.measure_number == measure_num
                ]

                ref_note = {}
                for note in sorted(measure_notes, key=lambda n: n.time):
                    # Convert duration to fraction
                    duration = _to_fraction(note.duration)

                    # Create note or rest
                    if note.is_silence:
                        m21_note = m21.note.Rest()
                        m21_note.quarterLength = duration
                    elif note.is_continuation:
                        # Skip continuation notes as they're handled with ties

                        m21_note = deepcopy(ref_note.get(note.voice_name, None))
                        m21_note.tie = m21.tie.Tie("stop")
                        m21_note.articulations = []
                        if m21_note is None:
                            continue
                    else:
                        # Handle single pitch or chord
                        if isinstance(note.pitch, list):
                            # Create chord
                            m21_note = m21.chord.Chord(note.pitch)
                            m21_note.quarterLength = duration
                        else:
                            # Create single note
                            m21_note = m21.note.Note(note.pitch)
                            m21_note.quarterLength = duration

                        # Check if this note is tied to the next note
                        next_notes = [
                            n
                            for n in score.notes
                            if n.voice_name == voice_name
                            and n.time == note.time + note.duration
                            and n.is_continuation
                        ]

                        if next_notes:
                            m21_note.tie = m21.tie.Tie("start")
                            ref_note[note.voice_name] = m21_note
                            # Add continuation notes

                    # Add techniques/articulations
                    if note.techniques:
                        for technique in note.techniques:
                            technique, technique_type = _create_technique(technique)
                            if technique:
                                if technique_type == "articulations":
                                    m21_note.articulations.append(technique)
                                elif technique_type == "dynamics":
                                    measure.insert(note.beat - 1.0, technique)
                                elif technique_type == "expressions":
                                    m21_note.expressions.append(technique)

                    # Insert note at the correct offset within the measure
                    # Calculate offset based on beat position
                    offset = note.beat - 1.0  # beats are 1-indexed
                    measure.insert(offset, m21_note)

                # Add measure to part
                part.append(measure)

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
            )

    for event in score.events:
        if event.event_type == "tempo":
            # Find the measure where the tempo event should be placed
            if event.measure_number in first_instrument_measures:
                measure = first_instrument_measures[event.measure_number]
                # Create a tempo mark
                tempo_mark = m21.tempo.MetronomeMark(number=event.event_value)
                # Calculate offset based on beat position
                offset = event.beat - 1.0  # beats are 1-indexed
                # Insert tempo mark at the correct offset within the measure
                measure.insert(offset, tempo_mark)

    for time_signature in score.time_signatures:
        if time_signature.measure_number in first_instrument_measures:
            measures = all_measures[time_signature.measure_number]
            for measure in measures:
                num = time_signature.time_signature[0]
                den = time_signature.time_signature[1]
                time_signature_mark = m21.meter.TimeSignature(f"{num}/{den}")
                measure.insert(0, time_signature_mark)
    m21_score.makeMeasures(inPlace=True)
    m21_score.write("musicxml", filepath)


def _write_comment(measure, beat, key=None, chord=None):
    chord_text = ""
    if key is not None:
        chord_text += f"{key}: "
    if chord is not None:
        chord_text += f"{chord}"

    if key is None and chord is None:
        return

    comment_text = chord_text
    # Create a text expression for the chord symbol
    chord_expression = m21.expressions.TextExpression(chord_text)
    chord_expression.style.fontWeight = "bold"
    chord_expression.placement = "above"

    # Create a comment object
    comment = m21.expressions.TextExpression(comment_text)
    comment.style.fontStyle = "italic"
    comment.style.fontSize = 8
    comment.placement = "above"
    measure.insert(beat - 1.0, comment)


def _to_fraction(duration):
    """Convert a float duration to a Fraction for better MusicXML representation."""
    # Handle common durations
    if abs(duration - 0.25) < 0.01:
        return 0.25  # Sixteenth note
    elif abs(duration - 0.5) < 0.01:
        return 0.5  # Eighth note
    elif abs(duration - 0.75) < 0.01:
        return 0.75  # Dotted eighth note
    elif abs(duration - 1.0) < 0.01:
        return 1.0  # Quarter note
    elif abs(duration - 1.5) < 0.01:
        return 1.5  # Dotted quarter note
    elif abs(duration - 2.0) < 0.01:
        return 2.0  # Half note
    elif abs(duration - 3.0) < 0.01:
        return 3.0  # Dotted half note
    elif abs(duration - 4.0) < 0.01:
        return 4.0  # Whole note

    # For triplets and other complex rhythms
    if abs(duration - 1 / 3) < 0.01:
        return Fraction(1, 3)
    elif abs(duration - 2 / 3) < 0.01:
        return Fraction(2, 3)

    # For other durations, convert to fraction
    return Fraction(duration).limit_denominator(64)


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
