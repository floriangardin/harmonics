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

    # Add variable definitions if any
    # (Not implemented as Score model doesn't seem to store variables)

    # Add event lines
    lines.extend(_generate_event_lines(score))

    # Process measures
    measure_data = _organize_by_measure(score)

    # Generate harmony, melody and accompaniment lines
    for measure_number in sorted(measure_data.keys()):
        measure = measure_data[measure_number]

        # Add harmony line if exists
        if "chords" in measure and measure["chords"]:
            lines.extend(_generate_harmony_line(measure_number, measure["chords"]))

        # Add melody lines grouped by voice
        if "notes" in measure:
            melody_by_voice = {}
            for note in measure["notes"]:
                voice_name = note.voice_name
                if voice_name not in melody_by_voice:
                    melody_by_voice[voice_name] = []
                melody_by_voice[voice_name].append(note)

            for voice_name, notes in melody_by_voice.items():
                lines.extend(_generate_melody_line(measure_number, voice_name, notes))

        # Add time signature changes if there are any for this measure
        if "time_signature" in measure:
            time_sig = measure["time_signature"]
            if time_sig:
                lines.append(
                    f"(m{measure_number}) Time Signature: {time_sig[0]}/{time_sig[1]}"
                )

        # Add a blank line between measures for readability
        lines.append("")

    text = "\n".join(lines)

    with open(filepath, "w") as f:
        f.write(text)

    return filepath


def _generate_metadata(score):
    """Generate metadata lines for the ERN file."""
    lines = []

    # Add composer and title
    if score.composer:
        lines.append(f"Composer: {score.composer}")
    if score.title:
        lines.append(f"Piece: {score.title}")

    # Add time signature (use the first one if available)
    if score.time_signatures and len(score.time_signatures) > 0:
        ts = score.time_signatures[0]
        lines.append(f"Time Signature: {ts.time_signature[0]}/{ts.time_signature[1]}")

    # Add tempo (use the first one if available)
    if score.tempos and len(score.tempos) > 0:
        tempo = score.tempos[0]
        lines.append(f"Tempo: {tempo.tempo}")

    # Add instruments
    if score.instruments:
        instruments_line = "Instrument: "
        instruments = []
        for instrument in score.instruments:
            instruments.append(f"{instrument.voice_name}={instrument.gm_number}")
        instruments_line += ", ".join(instruments)
        lines.append(instruments_line)

    return lines


def _generate_technique_lines(score):
    """Generate technique lines for the ERN file."""
    lines = []

    # Group techniques by voice and time range
    tech_by_voice = {}
    for tech in score.techniques:
        voice_name = tech.voice_name
        key = (tech.time_start, tech.time_end, voice_name)
        if key not in tech_by_voice:
            tech_by_voice[key] = []
        tech_by_voice[key].append(tech.technique)

    # Convert to tech lines
    for (time_start, time_end, voice_name), techniques in tech_by_voice.items():
        # Find the measure and beat for start and end
        start_measure, start_beat = _find_measure_beat(score, time_start)
        end_measure, end_beat = _find_measure_beat(score, time_end)

        if start_measure and end_measure and start_beat and end_beat:
            tech_line = f"tech {voice_name} (m{start_measure} b{start_beat} - m{end_measure} b{end_beat}) : {','.join(techniques)}"
            lines.append(tech_line)

    return lines


def _generate_event_lines(score):
    """Generate event lines for the ERN file."""
    lines = []

    # Group events by measure number
    events_by_measure = {}
    for event in score.events:
        if event.measure_number not in events_by_measure:
            events_by_measure[event.measure_number] = []
        events_by_measure[event.measure_number].append(event)

    # Generate event lines
    for measure, events in sorted(events_by_measure.items()):
        event_line = f"e{measure}"
        for event in sorted(events, key=lambda e: e.beat):
            event_line += f" b{event.beat} {event.event_type}({event.event_value})"
        lines.append(event_line)

    return lines


def _organize_by_measure(score):
    """Organize score items by measure."""
    measure_data = {}

    # Process chords
    for chord in score.chords:
        if chord.measure_number not in measure_data:
            measure_data[chord.measure_number] = {}

        if "chords" not in measure_data[chord.measure_number]:
            measure_data[chord.measure_number]["chords"] = []

        measure_data[chord.measure_number]["chords"].append(chord)

    # Process notes
    for note in score.notes:
        if note.measure_number not in measure_data:
            measure_data[note.measure_number] = {}

        if "notes" not in measure_data[note.measure_number]:
            measure_data[note.measure_number]["notes"] = []

        measure_data[note.measure_number]["notes"].append(note)

    # Process time signatures
    for ts in score.time_signatures:
        measure, _ = _find_measure_beat(score, ts.time)
        if measure and measure not in measure_data:
            measure_data[measure] = {}

        if measure:
            measure_data[measure]["time_signature"] = ts.time_signature

    return measure_data


def _generate_harmony_line(measure_number, chords):
    """Generate harmony line for a measure."""
    lines = []

    harmony_line = f"m{measure_number}"

    # Sort chords by beat
    sorted_chords = sorted(chords, key=lambda c: c.beat)

    for chord in sorted_chords:
        if chord.key and chord.chord:
            harmony_line += f" b{chord.beat} {chord.key} {chord.chord}"
        elif chord.chord:
            harmony_line += f" b{chord.beat} {chord.chord}"

    # Add phrase boundary if needed
    # (Would require additional flag in the chord model to specify this)
    # harmony_line += " ||"

    lines.append(harmony_line)

    return lines


def _generate_melody_line(measure_number, voice_name, notes):
    """Generate melody line for a measure and voice."""
    lines = []

    melody_line = f"m{measure_number} {voice_name}"

    # Sort notes by beat
    sorted_notes = sorted(notes, key=lambda n: n.beat if n.beat is not None else 0)

    for note in sorted_notes:
        # Skip continuation notes as they're part of the previous note's duration
        if note.is_continuation:
            continue

        if note.is_silence:
            melody_line += f" b{note.beat} R"
        elif isinstance(note.pitch, list):
            # Handle chord
            pitches = " ".join(note.pitch)
            melody_line += f" b{note.beat} {pitches}"
        elif note.pitch:
            melody_line += f" b{note.beat} {note.pitch}"

    lines.append(melody_line)

    return lines


def _find_measure_beat(score, time):
    """Find the measure number and beat for a given time."""
    # This is a placeholder implementation. In a real implementation,
    # you would need to calculate the measure and beat based on time,
    # using the time signatures in the score.

    # For notes and chords, we already have measure_number and beat
    for item in score.notes:
        if (
            abs(item.time - time) < 0.001
            and item.measure_number is not None
            and item.beat is not None
        ):
            return item.measure_number, item.beat

    for item in score.chords:
        if abs(item.time - time) < 0.001:
            return item.measure_number, item.beat

    # If no exact match found, we'd need to calculate it
    # This would require knowledge of time signatures and beats per measure
    # For now, just return None
    return None, None
