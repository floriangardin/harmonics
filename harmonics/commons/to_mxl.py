import music21 as m21


def to_mxl(filepath, score):
    # Create a new Music21 score
    score_template = m21.stream.Score()
    # Create a melody part from the note events.
    melody_part = m21.stream.Part()
    melody_part.id = "Melody"
    melody_part.name = "Melody"
    for note_item in score.melody:
        if note_item.pitch and not note_item.is_silence:
            n = m21.note.Note(note_item.pitch)
            n.duration.quarterLength = note_item.duration
            melody_part.insert(note_item.time, n)

    score_template.insert(0, melody_part)

    # Create staff in part
    trebleStaff = m21.stream.Part()
    trebleStaff.id = "Treble"
    trebleStaff.insert(0, m21.clef.TrebleClef())
    score_template.insert(0, trebleStaff)
    bassStaff = m21.stream.Part()
    bassStaff.id = "Bass"
    bassStaff.insert(0, m21.clef.BassClef())
    score_template.insert(0, bassStaff)

    for note_items in score.chords:
        rn = m21.roman.RomanNumeral(note_items.chord, note_items.key)
        b, t, a, s = [
            m21.note.Note(p, quarterLength=note_items.duration)
            for p in note_items.pitches
        ]
        b.lyric = rn.lyric
        trebleStaff.insert(note_items.time, s)
        trebleStaff.insert(note_items.time, a)
        bassStaff.insert(note_items.time, t)
        bassStaff.insert(note_items.time, b)

    staffGroup = m21.layout.StaffGroup(
        [trebleStaff, bassStaff], name="Harmonic reduction", symbol="brace"
    )
    score_template.insert(0, staffGroup)

    # Write the result as a MusicXML file to the given filepath.
    score_template.write("musicxml", fp=filepath)
