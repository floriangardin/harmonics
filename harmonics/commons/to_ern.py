from .utils_beat import beat_to_ern


def to_ern(filepath, score):
    """
    Convert a score to an ern TXT file.

    Parameters:
        filepath (str): The path to the ern TXT file.
        score (Score): The score to convert.

    Returns:
        str: The path to the ern TXT file.
    """

    lines = []

    # Add metadata
    lines.extend(_generate_metadata(score))

    # Add notes and comments
    lines.append("")

    # Add technique lines
    lines.extend(_generate_technique_lines(score))

    lines.append("")

    # Add variable definitions if any
    # (Not implemented as Score model doesn't seem to store variables)

    # Add event lines
    lines.extend(_generate_event_lines(score))

    lines.append("")

    # Process measures
    measure_data = _organize_by_measure(score)

    # Generate harmony, melody and accompaniment lines
    for measure_number in sorted(measure_data.keys()):
        measure = measure_data[measure_number]
        # Add time signature changes if there are any for this measure
        if "time_signature" in measure:
            time_sig = measure["time_signature"]
            if time_sig and measure_number > 1:
                lines.append(
                    f"(m{measure_number}) Time Signature: {time_sig[0]}/{time_sig[1]}"
                )

        # Add key signature changes if there are any for this measure
        if "key_signatures" in measure and measure["key_signatures"]:
            for key_sig in measure["key_signatures"]:
                if measure_number > 1 or key_sig.beat > 1.0:
                    # Format the key signature change
                    if key_sig.beat > 1.0:
                        # Mid-measure key signature change
                        lines.append(
                            f"(m{measure_number} b{beat_to_ern(key_sig.beat)}) Signature: {key_sig.key_signature}"
                        )
                    else:
                        # Start of measure key signature change
                        lines.append(
                            f"(m{measure_number}) Signature: {key_sig.key_signature}"
                        )

        # Add mid-measure clef changes for this measure
        if "clefs" in measure and measure["clefs"]:
            clef_changes = [c for c in measure["clefs"] if c.beat > 1.0]
            if clef_changes:
                lines.extend(_generate_clef_changes(measure_number, clef_changes))

        # Add harmony line if exists
        if "chords" in measure and measure["chords"]:
            lines.extend(_generate_harmony_line(measure_number, measure["chords"]))

        # Add melody lines grouped by track and voice
        if "notes" in measure:
            # Group notes by track and voice
            track_voice_notes = {}
            for note in measure["notes"]:
                track_name = note.track_name
                voice_name = note.voice_name if note.voice_name else "default"

                # Create a composite key for track and voice
                track_voice_key = (track_name, voice_name)

                if track_voice_key not in track_voice_notes:
                    track_voice_notes[track_voice_key] = []
                track_voice_notes[track_voice_key].append(note)

            # Process each track's clef changes first
            track_clef_changes = {}
            if "clefs" in measure and measure["clefs"]:
                for track_name in set(tv[0] for tv in track_voice_notes.keys()):
                    clef_changes = [
                        c
                        for c in measure["clefs"]
                        if c.track_name == track_name and c.beat == 1.0
                    ]
                    if clef_changes:
                        track_clef_changes[track_name] = clef_changes

            # Generate melody lines for each track-voice combination
            for (track_name, voice_name), notes in track_voice_notes.items():
                # Add beginning-of-measure clef changes if they exist
                if track_name in track_clef_changes:
                    lines.extend(
                        _generate_clef_changes(
                            measure_number, track_clef_changes[track_name]
                        )
                    )

                # Generate melody line for this track-voice combination
                sorted_notes = sorted(notes, key=lambda n: n.beat)
                lines.extend(
                    _generate_melody_line(
                        measure_number, track_name, voice_name, sorted_notes
                    )
                )
        lines.append("")
    # Write the ern text to file
    with open(filepath, "w") as f:
        f.write("\n".join(lines))

    return filepath


def _generate_metadata(score):
    """Generate metadata lines for the ern file."""
    lines = []

    # Add composer and title
    if score.composer:
        lines.append(f"Composer: {score.composer}")
    if score.title:
        lines.append(f"Piece: {score.title}")

    # Add time signature (defaults to 4/4 if none found)
    time_signature = (4, 4)
    if score.time_signatures and len(score.time_signatures) > 0:
        time_signature = score.time_signatures[0].time_signature
    lines.append(f"Time Signature: {time_signature[0]}/{time_signature[1]}")

    # Add initial key signature for measure 1 if exists
    key_signature = None
    for ks in score.key_signatures:
        if ks.measure_number == 1 and ks.beat == 1.0:
            key_signature = ks.key_signature
            break

    if key_signature:
        lines.append(f"Signature: {key_signature}")

    # Add tempo (defaults to 120 if none found)
    tempo = 120
    if score.tempos and len(score.tempos) > 0:
        tempo = score.tempos[0].tempo
    lines.append(f"Tempo: {tempo}")

    # Add clef declarations
    initial_clefs = {}
    for clef in score.clefs:
        if clef.measure_number == 1 and clef.beat == 1.0:
            track_name = clef.track_name
            # Only keep the first clef per voice (measure 1, beat 1)
            if track_name not in initial_clefs:
                initial_clefs[track_name] = clef

    # Add instrument definitions
    if score.instruments:
        instrument_defs = []
        for instrument in score.instruments:
            instrument_defs.append(f"{instrument.track_name}={instrument.name}")
        lines.append(f"Instrument: {', '.join(instrument_defs)}")

    # Add clef definitions after instrument definitions
    for track_name, clef in initial_clefs.items():
        # Format clef with octave change if necessary
        formatted_clef = clef.clef_name
        if clef.octave_change:
            if clef.octave_change > 0:
                formatted_clef += f"+{clef.octave_change}"
            else:
                formatted_clef += f"{clef.octave_change}"

        lines.append(f"Clef: {track_name}={formatted_clef}")

    return lines


def _generate_technique_lines(score):
    """Generate technique lines for the ern file."""
    lines = []

    # Sort techniques by start measure and beat for consistent output
    sorted_techniques = sorted(
        score.techniques, key=lambda t: (t.measure_number_start, t.beat_start)
    )

    for technique in sorted_techniques:
        voice_list = technique.track_name

        # Format the technique range
        technique_range = f"(m{technique.measure_number_start} {beat_to_ern(technique.beat_start)} - m{technique.measure_number_end} {beat_to_ern(technique.beat_end)})"

        # Format the technique list
        techniques_str = ", ".join(technique.technique.split(","))

        lines.append(f"tech {voice_list} {technique_range} : {techniques_str}")

    return lines


def _generate_event_lines(score):
    """Generate event lines for the ern file."""
    lines = []

    # Group events by measure number
    events_by_measure = {}
    for event in score.events:
        measure_number = event.measure_number
        if measure_number not in events_by_measure:
            events_by_measure[measure_number] = []
        events_by_measure[measure_number].append(event)

    # Generate event lines for each measure
    for measure_number in sorted(events_by_measure.keys()):
        events = events_by_measure[measure_number]
        event_line = f"e{measure_number}"

        # Sort events by beat for consistent output
        sorted_events = sorted(events, key=lambda e: e.beat)

        for event in sorted_events:
            event_line += (
                f" {beat_to_ern(event.beat)} {event.event_type}({event.event_value})"
            )

        lines.append(event_line)

    return lines


def _generate_clef_changes(measure_number, clef_items):
    """Generate clef change lines for the ern file."""
    lines = []

    for clef_item in clef_items:
        track_name = clef_item.track_name
        beat = clef_item.beat

        if measure_number == 1 and beat == 1.0:
            continue

        # Format clef with octave change if necessary
        formatted_clef = clef_item.clef_name
        if clef_item.octave_change:
            if clef_item.octave_change > 0:
                formatted_clef += f"+{clef_item.octave_change}"
            else:
                formatted_clef += f"{clef_item.octave_change}"

        if beat == 1.0:
            # Beginning of measure clef change
            lines.append(f"(m{measure_number}) Clef: {track_name}={formatted_clef}")
        else:
            # Mid-measure clef change
            lines.append(
                f"m{measure_number} {track_name} {beat_to_ern(beat)} clef {formatted_clef}"
            )

    return lines


def _organize_by_measure(score):
    """Organize score data by measure number."""
    measure_data = {}

    # Process harmony (chords)
    for chord in score.chords:
        measure_number = chord.measure_number
        if measure_number not in measure_data:
            measure_data[measure_number] = {}
        if "chords" not in measure_data[measure_number]:
            measure_data[measure_number]["chords"] = []
        measure_data[measure_number]["chords"].append(chord)

    # Process melody (notes)
    for note in score.notes:
        measure_number = note.measure_number
        if measure_number not in measure_data:
            measure_data[measure_number] = {}
        if "notes" not in measure_data[measure_number]:
            measure_data[measure_number]["notes"] = []
        measure_data[measure_number]["notes"].append(note)

    # Process time signatures
    for ts in score.time_signatures:
        measure_number = ts.measure_number
        if measure_number not in measure_data:
            measure_data[measure_number] = {}
        measure_data[measure_number]["time_signature"] = ts.time_signature

    # Process clefs
    for clef in score.clefs:
        measure_number = clef.measure_number
        if measure_number not in measure_data:
            measure_data[measure_number] = {}
        if "clefs" not in measure_data[measure_number]:
            measure_data[measure_number]["clefs"] = []
        measure_data[measure_number]["clefs"].append(clef)

    # Process key signatures
    for ks in score.key_signatures:
        measure_number = ks.measure_number
        if measure_number not in measure_data:
            measure_data[measure_number] = {}
        if "key_signatures" not in measure_data[measure_number]:
            measure_data[measure_number]["key_signatures"] = []
        measure_data[measure_number]["key_signatures"].append(ks)

    return measure_data


def _generate_harmony_line(measure_number, chords):
    """Generate harmony line for a measure."""
    lines = []

    harmony_line = f"m{measure_number}"

    # Sort chords by beat
    sorted_chords = sorted(chords, key=lambda c: c.beat)

    for chord in sorted_chords:
        if chord.key and chord.new_key:
            harmony_line += f" {beat_to_ern(chord.beat)} {chord.key}: {chord.chord}"
        elif chord.chord:
            harmony_line += f" {beat_to_ern(chord.beat)} {chord.chord}"

    # Add phrase boundary if needed
    # (Would require additional flag in the chord model to specify this)
    # harmony_line += " ||"

    lines.append(harmony_line)

    return lines


def _generate_melody_line(measure_number, track_name, voice_name, notes):
    """Generate melody line for a measure and voice."""
    lines = []

    # Skip empty voices
    if not notes:
        return lines

    # If only silence don't add the melody line
    if all(note.is_silence for note in notes) and all(
        note.text_comment is None for note in notes
    ):
        return lines

    # Start the melody line with measure number and track name
    if voice_name == "default":
        melody_line = f"m{measure_number} {track_name}"
    else:
        melody_line = f"m{measure_number} {track_name}.{voice_name}"

    for note in notes:
        text_comment = (
            '"' + note.text_comment + '" ' if note.text_comment is not None else ""
        )
        # Skip continuation notes as they're part of the previous note's duration
        if note.is_continuation:
            melody_line += f" {beat_to_ern(note.beat)} {text_comment}L"
        # Handle text comments
        elif note.is_silence:
            melody_line += f" {beat_to_ern(note.beat)} {text_comment}R"
        elif isinstance(note.pitch, list):
            # Handle chord
            pitches = " ".join(note.pitch)
            melody_line += f" {beat_to_ern(note.beat)} {text_comment}{pitches}"
        elif note.pitch:
            melody_line += f" {beat_to_ern(note.beat)} {text_comment}{note.pitch}"

        # Add techniques
        if note.techniques:
            melody_line += f" [{','.join(note.techniques)}]"

    lines.append(melody_line)

    return lines
