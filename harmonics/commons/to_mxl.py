import music21 as m21
from fractions import Fraction
import re
from typing import Dict, List, Optional, Set, Any
from copy import deepcopy
from harmonics.commons import utils_techniques
from harmonics.commons.utils_output import increment_voices, convert_musicxml_to_mxl

class PartState:
    """Class to track the state of a part during MusicXML conversion."""

    def __init__(self):
        self.ref_note = {}  # Reference notes for tied notes
        self.crescendo_notes = []  # Notes in a crescendo
        self.diminuendo_notes = []  # Notes in a diminuendo
        self.slur_notes = []  # Notes in a slur
        self.crescendo_start = False  # Whether a crescendo has started
        self.diminuendo_start = False  # Whether a diminuendo has started
        self.slur_start = False  # Whether a slur has started
        self.last_chord = None  # Last chord for comparison
        self.last_key = None  # Last key for comparison

        self.slur_notes = []  # Notes in a slur
        self.crescendo_start = False  # Whether a crescendo has started
        self.diminuendo_start = False  # Whether a diminuendo has started
        self.slur_start = False  # Whether a slur has started
        self.last_chord = None  # Last chord for comparison
        self.last_key = None  # Last key for comparison


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
            if technique.replace("!", "") == "crescendo":
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
            elif technique.replace("!", "") == "diminuendo":
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
            else:
                technique_obj, technique_type = _create_technique(technique)
                if technique_obj:
                    if technique_type == "articulations":
                        m21_note.articulations.append(technique_obj)
                    elif technique_type == "dynamics":
                        measure.insert(_get_offset(note.beat, ts), technique_obj)
                    elif technique_type == "expressions":
                        m21_note.expressions.append(technique_obj)

    # Only add to slur_notes if we're in a slur and haven't already added this note
    # (we already add the note when the slur starts or ends)
    if part_state.slur_start and m21_note not in part_state.slur_notes:
        part_state.slur_notes.append(m21_note)

    if part_state.crescendo_start and m21_note not in part_state.crescendo_notes:
        part_state.crescendo_notes.append(m21_note)
    if part_state.diminuendo_start and m21_note not in part_state.diminuendo_notes:
        part_state.diminuendo_notes.append(m21_note)

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
        #part.id = instrument.track_name

        # Add instrument to part
        m21_instrument = m21.instrument.Instrument()
        m21_instrument.midiProgram = (
            instrument.gm_number - 1
        )  # music21 uses 0-127, GM uses 1-128
        m21_instrument.instrumentName = instrument.name.capitalize().replace("_", " ")
        part.insert(0, m21_instrument)

        all_voices_for_instrument = list(sorted(set([note.voice_name for note in score.notes if note.track_name == instrument.track_name])))
        voices = []
        for idx, voice_name in enumerate(all_voices_for_instrument):
            voice = m21.stream.Voice()
            voices.append(voice)
            parts[(instrument.track_name, voice_name)] = voice

        for voice in voices:
            part.append(voice)
        # Add part to score
        m21_score.insert(0, part)
        #m21_score.append(part)

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
        current_ts = None
        measure_durations = {}
        for measure_num in range(1, max_measure + 1):
            for ts in score.time_signatures:
                if ts.measure_number == measure_num:
                    current_ts = ts.time_signature
                    break
            measure_durations[measure_num] = 4 * current_ts[0] / current_ts[1]
        time_sig_map = _get_time_sig_map(score.time_signatures, max_measure)
        for (track_name, voice_name), part in parts.items():
            idx += 1
            # Get time signatures for this part
            time_sigs = sorted(score.time_signatures, key=lambda ts: ts.time)
            current_ts = time_sigs[0].time_signature if time_sigs else (4, 4)

            # Get tempo markings
            tempos = sorted(score.tempos, key=lambda t: t.time)
            current_tempo_idx = 0

            # Get clef specifications for this voice
            voice_clefs = sorted(
                [clef for clef in score.clefs if clef.track_name == track_name],
                key=lambda c: (c.time, c.measure_number, c.beat),
            )
            current_clef_idx = 0

            # Get key signatures
            key_signatures = sorted(
                score.key_signatures, key=lambda ks: (ks.time, ks.measure_number)
            )
            current_key_sig_idx = 0

            # Initialize default clef (treble clef)
            current_clef = None
            if voice_clefs:
                current_clef = voice_clefs[0]

            # Initialize part state
            part_state = PartState()
            all_notes = []

            # Create measures
            for measure_num in range(1, max_measure + 1):
                current_ts = time_sig_map[measure_num]
                
                measure = m21.stream.Measure(number=measure_num, timeSignature=current_ts)
                all_measures[measure_num] = all_measures.get(measure_num, []) + [
                    measure
                ]
                if idx == 0:
                    first_instrument_measures[measure_num] = measure

                # Add initial clef to first measure or if there's a clef change
                if measure_num == 1 and current_clef is not None:
                    _add_clef_to_measure(measure, current_clef, 0)

                # Check for clef changes at the start of this measure
                while (
                    current_clef_idx < len(voice_clefs)
                    and voice_clefs[current_clef_idx].measure_number == measure_num
                    and voice_clefs[current_clef_idx].beat == 1.0
                ):
                    current_clef = voice_clefs[current_clef_idx]
                    _add_clef_to_measure(measure, current_clef, 0)
                    current_clef_idx += 1
                    if current_clef_idx >= len(voice_clefs):
                        break

                while (
                    current_key_sig_idx < len(key_signatures)
                    and key_signatures[current_key_sig_idx].measure_number
                    == measure_num
                ):
                    key_sig = key_signatures[current_key_sig_idx]
                    _add_key_signature_to_measure(measure, key_sig, current_ts)
                    current_key_sig_idx += 1
                    if current_key_sig_idx >= len(key_signatures):
                        break

                # Add tempo marking if it changes at this measure
                while (
                    current_tempo_idx < len(tempos)
                    and tempos[current_tempo_idx].measure_number == measure_num
                    and tempos[current_tempo_idx].beat == 1.0
                ):
                    tempo = tempos[current_tempo_idx]
                    m21_tempo = m21.tempo.MetronomeMark(number=tempo.tempo, referent=m21.note.Note(type='quarter'))
                    measure.insert(0, m21_tempo)
                    current_tempo_idx += 1
                    if current_tempo_idx >= len(tempos):
                        break

                # Add notes for this voice and measure
                measure_notes = [
                    note
                    for note in score.notes
                    if note.track_name == track_name
                    and note.voice_name == voice_name
                    and note.measure_number == measure_num
                ]

                if len(measure_notes) == 0:
                    m21_note = m21.note.Rest()
                    m21_note.quarterLength = measure_durations[measure_num]
                    measure.append(m21_note)

                for idx_note, note in enumerate(
                    sorted(measure_notes, key=lambda n: n.time)
                ):
                    # Convert duration to fraction
                    duration = _to_fraction(note.duration, current_ts)
                    # Create note or rest
                    if note.is_silence:
                        m21_note = m21.note.Rest()
                        m21_note.quarterLength = duration
                    elif note.is_continuation:
                        # Skip continuation notes as they're handled with ties
                        m21_note = deepcopy(
                            part_state.ref_note.get((note.track_name, note.voice_name), None)
                        )
                        m21_note.tie = m21.tie.Tie("stop")
                        m21_note.articulations = []
                        m21_note.duration = m21.duration.Duration(duration)
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
                            if n.track_name == track_name
                            and n.voice_name == voice_name
                            and n.time == note.time + note.duration
                            and n.is_continuation
                        ]

                        if next_notes:
                            m21_note.tie = m21.tie.Tie("start")
                            part_state.ref_note[(note.track_name, note.voice_name)] = m21_note
                            # Add continuation notes

                    # Apply techniques and update part state
                    m21_note = _apply_techniques(
                        note, m21_note, measure, part_state, current_ts
                    )

                    # Insert note at the correct offset within the measure
                    # Calculate offset based on beat position
                    offset = _get_offset(note.beat, current_ts)
                    measure.insert(offset, m21_note)

                    # Add text comment if present
                    if note.text_comment is not None:
                        text_expression = m21.expressions.TextExpression(note.text_comment)
                        text_expression.positionVertical = 20  # Position above the staff
                        text_expression.style.fontStyle = "italic"  # Make it italic
                        measure.insert(offset, text_expression)

                    all_notes.append(m21_note)

                # Check for mid-measure clef changes
                for clef_item in voice_clefs:
                    if clef_item.measure_number == measure_num and clef_item.beat > 1.0:
                        offset = _get_offset(clef_item.beat, current_ts)
                        _add_clef_to_measure(measure, clef_item, offset)

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
                current_ts=time_sig_map[chord.measure_number],
            )

    for event in score.events:
        if event.event_type == "tempo":
            # Find the measure where the tempo event should be placed
            if event.measure_number in first_instrument_measures:
                measure = first_instrument_measures[event.measure_number]
                current_ts = time_sig_map[event.measure_number]
                # Create a tempo mark
                tempo_mark = m21.tempo.MetronomeMark(number=event.event_value, referent=m21.note.Note(type='quarter'))
                # Calculate offset based on beat position
                offset = _get_offset(event.beat, current_ts)
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
    #m21_score.write("musicxml", filepath)
    _increment_and_compress(m21_score, filepath)


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

def _increment_and_compress(m21_score, filepath):
    import shutil
    import tempfile
    import os
    final_filepath = filepath
    with tempfile.NamedTemporaryFile(delete=False,suffix=".musicxml") as temp_file:
        m21_score.write("musicxml", temp_file.name)
        increment_voices(temp_file.name)  # TEMP : To fix 0-indexed voice issue in musescore, is there a better solution ?
        if final_filepath.endswith(".mxl"):
            new_filepath = convert_musicxml_to_mxl(temp_file.name)
        else:
            new_filepath = temp_file.name

    # Copy the new file to the final filepath
    shutil.copy(new_filepath, final_filepath)
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
    return _to_beat_fraction(beat - 1.0, current_ts)


def _to_beat_fraction(beat, current_ts):
    ratio_beat = Fraction(4, current_ts[1])
    if beat == int(beat):
        return int(beat) * ratio_beat
    else:
        fractional_part = beat - int(beat)
        fraction = _to_fraction(fractional_part, (4, 4))
        return (int(beat) + fraction) * ratio_beat


def _to_fraction(duration, current_ts):
    """Convert a float duration to a Fraction for better MusicXML representation."""
    # Handle common durations
    threshold = 0.015
    ratio_beat = Fraction(4, current_ts[1])
    if abs(duration - 0.25) < threshold:
        return 0.25 * ratio_beat  # Sixteenth note
    elif abs(duration - 0.5) < threshold:
        return 0.5 * ratio_beat  # Eighth note
    elif abs(duration - 0.75) < threshold:
        return 0.75 * ratio_beat  # Dotted eighth note
    elif abs(duration - 1.0) < threshold:
        return 1.0 * ratio_beat      # Quarter note
    elif abs(duration - 1.5) < threshold:
        return 1.5 * ratio_beat  # Dotted quarter note
    elif abs(duration - 2.0) < threshold:
        return 2.0 * ratio_beat  # Half note
    elif abs(duration - 3.0) < threshold:
        return 3.0 * ratio_beat  # Dotted half note
    elif abs(duration - 4.0) < threshold:
        return 4.0 * ratio_beat # Whole note

    # For triplets and other complex rhythms
    if abs(duration - 1 / 3) < threshold:
        return Fraction(1, 3) * ratio_beat
    elif abs(duration - 2 / 3) < threshold:
        return Fraction(2, 3) * ratio_beat
    
    # For other durations, convert to fraction
    return Fraction(duration).limit_denominator(64) * ratio_beat


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
    }

    # Create the clef
    clef_name = clef_map.get(clef_item.clef_name, "treble")
    m21_clef = m21.clef.clefFromString(clef_name)

    # Apply octave change if specified
    if clef_item.octave_change is not None:
        m21_clef.octaveChange = clef_item.octave_change

    # Insert clef at the specified offset
    measure.insert(offset, m21_clef)
