def _create_articulation(technique):
    """Create a music21 articulation object based on the technique name."""
    # Articulations
    if technique == "staccato":
        return m21.articulations.Staccato()
    elif technique == "staccatissimo":
        return m21.articulations.Staccatissimo()
    elif technique == "marcato":
        return m21.articulations.StrongAccent()
    elif technique == "pizzicato":
        return m21.articulations.Pizzicato()
    elif technique == "legato":
        return m21.articulations.Tenuto()

    # Accents
    elif technique == "accent":
        return m21.articulations.Accent()
    elif technique == "ghost_note":
        return m21.articulations.Unstress()

    # Dynamics
    elif technique in ["pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]:
        return m21.dynamics.Dynamic(technique)

    # Note: These expressions should be handled differently in the main code
    # as they're not articulations but expressions
    # Return None for unsupported techniques or expressions that need special handling
    return None


def _to_mxl(filepath, score):
    """
    Convert a score to a MusicXML file.

    Args:
        filepath: Path to save the MusicXML file
        score: Score object containing notes, chords, time signatures, etc.
    """
    # Create a music21 score
    m21_score = m21.stream.Score()

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

    # Add measures to parts
    if score.notes:
        max_measure = max(
            note.measure_number
            for note in score.notes
            if note.measure_number is not None
        )

        # Create measures for each part
        for voice_name, part in parts.items():
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

                for note in sorted(measure_notes, key=lambda n: n.time):
                    # Convert duration to fraction
                    duration = _to_fraction(note.duration)

                    # Create note or rest
                    if note.is_silence:
                        m21_note = m21.note.Rest()
                        m21_note.quarterLength = duration
                    elif note.is_continuation:
                        # Skip continuation notes as they're handled with ties
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
                                and n.pitch == note.pitch
                            ]

                            if next_notes:
                                m21_note.tie = m21.tie.Tie("start")

                    # Add techniques/articulations
                    if note.techniques:
                        for technique in note.techniques:
                            # Handle expressions separately from articulations
                            if technique == "trill":
                                m21_note.expressions.append(m21.expressions.Trill())
                            elif technique == "mordent":
                                m21_note.expressions.append(m21.expressions.Mordent())
                            elif technique == "upper_mordent":
                                m21_note.expressions.append(
                                    m21.expressions.InvertedMordent()
                                )
                            elif technique == "turn":
                                m21_note.expressions.append(m21.expressions.Turn())
                            elif technique == "tremolo":
                                m21_note.expressions.append(m21.expressions.Tremolo())
                            else:
                                # Handle regular articulations
                                articulation = _create_articulation(technique)
                                if articulation:
                                    m21_note.articulations.append(articulation)

                    # Add chord symbol as text expression if it changes
                    if note.chord and note.chord != last_chord:
                        chord_text = f"{note.chord}"
                        if note.key and note.key != last_key:
                            chord_text += f" ({note.key})"

                        harmony = m21.harmony.ChordSymbol(figure="C/E")
                        harmony.writeAsChord = False
                        measure.insert(note.time, harmony)

                        last_chord = note.chord
                        last_key = note.key

                    # Insert note at the correct offset within the measure
                    # Calculate offset based on beat position
                    offset = note.beat - 1.0  # beats are 1-indexed
                    measure.insert(offset, m21_note)

                # Add measure to part
                part.append(measure)

    # Write to file
    m21_score.write("musicxml", filepath)
