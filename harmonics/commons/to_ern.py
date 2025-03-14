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
        
        # Add mid-measure clef changes for this measure
        if "clefs" in measure and measure["clefs"]:
            clef_changes = [c for c in measure["clefs"] if c.beat > 1.0]
            if clef_changes:
                lines.extend(_generate_clef_changes(measure_number, clef_changes))
        
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
                # Add beginning-of-measure clef changes if they exist and if they are not in the metadata
                if "clefs" in measure and measure["clefs"]:
                    clef_changes = [c for c in measure["clefs"] if c.voice_name == voice_name and c.beat == 1.0]
                    if clef_changes:
                        lines.extend(_generate_clef_changes(measure_number, clef_changes))
                
                lines.extend(_generate_melody_line(measure_number, voice_name, sorted(notes, key=lambda n: n.beat)))
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

    # Add tempo (defaults to 120 if none found)
    tempo = 120
    if score.tempos and len(score.tempos) > 0:
        tempo = score.tempos[0].tempo
    lines.append(f"Tempo: {tempo}")

    # Add clef declarations
    initial_clefs = {}
    for clef in score.clefs:
        if clef.measure_number == 1 and clef.beat == 1.0:
            voice_name = clef.voice_name
            # Only keep the first clef per voice (measure 1, beat 1)
            if voice_name not in initial_clefs:
                initial_clefs[voice_name] = clef
    
    # Add instrument definitions
    if score.instruments:
        instrument_defs = []
        for instrument in score.instruments:
            instrument_defs.append(f"{instrument.voice_name}={instrument.name}")
        lines.append(f"Instrument: {', '.join(instrument_defs)}")
    
    # Add clef definitions after instrument definitions
    for voice_name, clef in initial_clefs.items():
        # Format clef with octave change if necessary
        formatted_clef = clef.clef_name
        if clef.octave_change:
            if clef.octave_change > 0:
                formatted_clef += f"+{clef.octave_change}"
            else:
                formatted_clef += f"{clef.octave_change}"
        
        lines.append(f"Clef: {voice_name}={formatted_clef}")

    return lines


def _generate_technique_lines(score):
    """Generate technique lines for the ern file."""
    lines = []
    
    # Sort techniques by start measure and beat for consistent output
    sorted_techniques = sorted(
        score.techniques, 
        key=lambda t: (t.measure_number_start, t.beat_start)
    )
    
    for technique in sorted_techniques:
        voice_list = technique.voice_name
        
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
            event_line += f" {beat_to_ern(event.beat)} {event.event_type}({event.event_value})"
        
        lines.append(event_line)
    
    return lines


def _generate_clef_changes(measure_number, clef_items):
    """Generate clef change lines for the ern file."""
    lines = []
    
    for clef_item in clef_items:
        voice_name = clef_item.voice_name
        beat = clef_item.beat
        
        # Format clef with octave change if necessary
        formatted_clef = clef_item.clef_name
        if clef_item.octave_change:
            if clef_item.octave_change > 0:
                formatted_clef += f"+{clef_item.octave_change}"
            else:
                formatted_clef += f"{clef_item.octave_change}"
                
        if beat == 1.0:
            # Beginning of measure clef change
            lines.append(f"(m{measure_number}) Clef: {voice_name}={formatted_clef}")
        else:
            # Mid-measure clef change
            lines.append(f"(m{measure_number} {beat_to_ern(beat)}) Clef: {voice_name}={formatted_clef}")
    
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
