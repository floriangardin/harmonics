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
            instruments.append(f"{instrument.voice_name}={instrument.name}")
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
        key = (
            tech.measure_number_start,
            tech.beat_start,
            tech.measure_number_end,
            tech.beat_end,
            voice_name,
        )
        if key not in tech_by_voice:
            tech_by_voice[key] = []
        tech_by_voice[key].append(tech.technique)

    # Convert to tech lines
    for (
        start_measure,
        start_beat,
        end_measure,
        end_beat,
        voice_name,
    ), techniques in tech_by_voice.items():
        if start_measure and end_measure and start_beat and end_beat:
            tech_line = f"tech {voice_name} (m{start_measure} {beat_to_ern(start_beat)} - m{end_measure} {beat_to_ern(end_beat)}) : {','.join(techniques)}"
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
            event_line += (
                f" {beat_to_ern(event.beat)} {event.event_type}({event.event_value})"
            )
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
        if ts.measure_number not in measure_data:
            measure_data[ts.measure_number] = {}

        if ts.measure_number:
            measure_data[ts.measure_number]["time_signature"] = ts.time_signature

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


def _generate_melody_line(measure_number, voice_name, notes):
    """Generate melody line for a measure and voice."""
    lines = []

    melody_line = f"m{measure_number} {voice_name}"

    # Sort notes by beat
    sorted_notes = sorted(notes, key=lambda n: n.beat if n.beat is not None else 0)

    # If only silence don't add the melody line
    if all(note.is_silence for note in notes):
        return lines

    for note in sorted_notes:
        # Skip continuation notes as they're part of the previous note's duration
        if note.is_continuation:
            melody_line += f" {beat_to_ern(note.beat)} L"

        elif note.is_silence:
            melody_line += f" {beat_to_ern(note.beat)} R"
        elif isinstance(note.pitch, list):
            # Handle chord
            pitches = " ".join(note.pitch)
            melody_line += f" {beat_to_ern(note.beat)} {pitches}"
        elif note.pitch:
            melody_line += f" {beat_to_ern(note.beat)} {note.pitch}"

        # Add techniques
        if note.techniques:
            melody_line += f" [{','.join(note.techniques)}]"

    lines.append(melody_line)

    return lines
