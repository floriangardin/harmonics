from music21 import key, scale, pitch, chord, defaults, roman
import copy
from .constants import BASE_OCTAVE

# only some figures imply a root other than the bass (e.g. "54" does not)
FIGURES_IMPLYING_ROOT: tuple[tuple[int, ...], ...] = (
    # triads
    (6,),
    (6, 3),
    (6, 4),
    # seventh chords
    (6, 5, 3),
    (6, 5),
    (6, 4, 3),
    (4, 3),
    (6, 4, 2),
    (4, 2),
    (2,),
    # ninth chords
    (7, 6, 5, 3),
    (6, 5, 4, 3),
    (6, 4, 3, 2),
    (7, 5, 3, 2),
    # eleventh chords
    (9, 7, 6, 5, 3),
    (7, 6, 5, 4, 3),
    (9, 6, 5, 4, 3),
    (9, 7, 6, 4, 3),
    (7, 6, 5, 4, 2),
)


def matchInterval(interval):
    interval = interval.replace("b", "-")
    nb_flat = interval.count("-") * -1
    nb_sharp = interval.count("#")
    total_alteration = nb_flat + nb_sharp
    text_accidental = ""
    if total_alteration > 0:
        text_accidental = "#" * total_alteration
    elif total_alteration < 0:
        text_accidental = "-" * -total_alteration
    interval_without_accidental = interval.replace("-", "")
    interval_without_accidental = interval_without_accidental.replace("#", "")
    stepNumber = int(interval_without_accidental)
    return text_accidental, stepNumber


def getPitchFromInterval(figure, key, interval, octave):
    """
    Utility function to update the pitches to the new figure etc.
    """
    addAccidental, stepNumber = matchInterval(interval)
    rn = roman.RomanNumeral(figure, key)
    useScale: key.Key | scale.ConcreteScale
    if rn.secondaryRomanNumeralKey is not None:
        useScale = rn.secondaryRomanNumeralKey
    elif rn.useImpliedScale and rn.impliedScale is not None:
        useScale = rn.impliedScale
    else:
        useScale = rn.key

    # should be 7 but hey, octatonic scales, etc.
    # rn.scaleCardinality = len(useScale.pitches) - 1
    if "DiatonicScale" in useScale.classes:  # speed up simple case
        rn.scaleCardinality = 7
    else:
        rn.scaleCardinality = useScale.getDegreeMaxUnique()

    bassScaleDegree = rn.bassScaleDegreeFromNotation(rn.figuresNotationObj)
    bassPitch = useScale.pitchFromDegree(
        bassScaleDegree, direction=scale.Direction.ASCENDING
    )
    pitches: list[pitch.Pitch] = [bassPitch]
    lastPitch = bassPitch
    numberNotes = len(rn.figuresNotationObj.numbers)

    for j in range(numberNotes):
        i = numberNotes - j - 1
        thisScaleDegree = bassScaleDegree + rn.figuresNotationObj.numbers[i] - 1
        newPitch = useScale.pitchFromDegree(
            thisScaleDegree, direction=scale.Direction.ASCENDING
        )
        pitchName = rn.figuresNotationObj.modifiers[i].modifyPitchName(newPitch.name)
        newNewPitch = pitch.Pitch(pitchName)
        if newPitch.octave is not None:
            newNewPitch.octave = newPitch.octave
        else:
            newNewPitch.octave = defaults.pitchOctave
        if newNewPitch.ps < lastPitch.ps:
            newNewPitch.octave += 1  # type: ignore
        pitches.append(newNewPitch)
        lastPitch = newNewPitch

    if (
        rn.frontAlterationTransposeInterval
        and rn.frontAlterationTransposeInterval.semitones != 0
    ):
        chord_map = chord.tools.allChordSteps(chord.Chord(pitches))
        non_alter = (
            chord_map.get(7, None),
            chord_map.get(2, None),  # 9th
            chord_map.get(4, None),  # 11th
            chord_map.get(6, None),  # 13th
        )
        for thisPitch in pitches:
            if thisPitch not in non_alter:
                rn.frontAlterationTransposeInterval.transposePitch(
                    thisPitch, inPlace=True
                )
    rn.pitches = tuple(
        pitches
    )  # unnecessary tuple; mypy properties different typing bug

    if rn.figuresNotationObj.numbers not in FIGURES_IMPLYING_ROOT:
        # Avoid deriving a nonsense root later
        rn.root(rn.bass())

    rn._matchAccidentalsToQuality(rn.impliedQuality)

    # run this before omittedSteps and added steps so that
    # they don't change the sense of root.
    rn._correctBracketedPitches()
    if rn.omittedSteps or rn.addedSteps:
        # set the root manually so that these alterations don't change the root.
        rn.root(rn.root())

    if rn.omittedSteps:
        omittedPitches = []
        for thisCS in rn.omittedSteps:
            p = rn.getChordStep(thisCS)
            if p is not None:
                omittedPitches.append(p.name)

        newPitches = []
        for thisPitch in rn.pitches:
            if thisPitch.name not in omittedPitches:
                newPitches.append(thisPitch)
        rn.pitches = tuple(newPitches)

    if "-" in addAccidental:
        alteration = addAccidental.count("-") * -1
    else:
        alteration = addAccidental.count("#")
    thisScaleDegree = rn.scaleDegree + stepNumber - 1
    addedPitch = useScale.pitchFromDegree(
        thisScaleDegree, direction=scale.Direction.ASCENDING
    )
    if addedPitch.accidental is not None:
        addedPitch.accidental.alter += alteration
    else:
        addedPitch.accidental = pitch.Accidental(alteration)

    while addedPitch.ps < bassPitch.ps:
        addedPitch.octave += 1

    if (
        addedPitch.ps == bassPitch.ps
        and addedPitch.diatonicNoteNum < bassPitch.diatonicNoteNum
    ):
        # RN('IV[add#7]', 'C') would otherwise result
        # in E#4 as bass, not E#5 as highest note.
        addedPitch.octave += 1

    result = addedPitch
    result.octave += octave
    return result.nameWithOctave


def getPitchFromIntervalFromMinimallyModifiedScale(figure, key, interval, octave):
    """
    Given a roman numeral chord symbol (rnStr) in the key keyStr,
    return a music21.pitch.Pitch object that represents the pitch
    that is the result of the interval from the minimal scale.
    """
    text_accidental, step_number = matchInterval(interval)
    real_minimal_scale = getMinimallyModifiedScale(figure, key)

    scale_note = real_minimal_scale[(step_number - 1) % len(real_minimal_scale)]
    scale_note_octave = (step_number - 1) // len(real_minimal_scale)

    alteration = text_accidental.count("#") + text_accidental.count("-") * -1
    scale_note_alteration = scale_note.count("#") + scale_note.count("-") * -1
    total_alteration = alteration + scale_note_alteration
    total_alteration_str = ""
    if total_alteration > 0:
        total_alteration_str = "#" * total_alteration
    elif total_alteration < 0:
        total_alteration_str = "-" * -total_alteration

    scale_note = scale_note.replace("#", "").replace("-", "")
    scale_note = scale_note + total_alteration_str
    result = pitch.Pitch(scale_note, octave=scale_note_octave + BASE_OCTAVE)
    result.octave += octave
    return result.nameWithOctave


def getMinimallyModifiedScale(rnStr, keyStr):
    """
    Given a roman numeral chord symbol (rnStr) in the key keyStr,
    return a list of 7 music21.pitch.Pitch objects that represent the
    diatonic scale (the mode of the key starting on the chord’s root)
    with any accidentals modified to “fit” the chord.

    For example:
      getModifiedScale('iv','C') returns pitches corresponding to
      F, G, A♭, B, C, D, E

      getModifiedScale('I[add#11]', 'D') returns
      D, E, F#, G#, A, B, C#
    """
    # Create the RomanNumeral chord object.
    rn = roman.RomanNumeral(rnStr, keyStr)
    # Get the key (music21.key.Key object)
    k: key.Key | scale.ConcreteScale
    if rn.secondaryRomanNumeralKey is not None:
        k = rn.secondaryRomanNumeralKey
    elif rn.useImpliedScale and rn.impliedScale is not None:
        k = rn.impliedScale
    else:
        k = rn.key

    # Get the diatonic scale for the key.
    # (For a major key, pitchFromDegree(1..7) gives the seven scale degrees.)
    diatonic = [k.pitchFromDegree(i) for i in range(1, 8)]

    # “Rotate” the scale so that the chord’s root becomes the first note.
    chordRoot = rn.root()  # a music21.pitch.Pitch object
    # Find the note in the diatonic scale with the same letter (step) as the chord’s root.
    for i, p in enumerate(diatonic):
        if p.step == chordRoot.step:
            modeScale = diatonic[i:] + diatonic[:i]
            break
    else:
        raise ValueError("Chord root not found in the diatonic scale of key " + keyStr)

    # Now “patch” any scale degree that is altered in the chord.
    # (For example, in C–major the rotated scale is F, G, A, B, C, D, E.
    # But the chord “iv” (F minor) has tones F, A♭, C so we want the 3rd
    # degree (letter A) to be A♭.)
    modScale = list(modeScale)  # copy the list
    for chordPitch in rn.pitches:
        # Find the note in modScale that has the same letter name (step).
        for i, scalePitch in enumerate(modScale):
            if scalePitch.step == chordPitch.step:
                # If the accidentals differ then replace that note.
                if chordPitch.name != scalePitch.name:
                    modScale[i] = chordPitch
                break
    return [n.name for n in modScale]


# Try the examples:
if __name__ == "__main__":
    ms1 = getMinimallyModifiedScale("iv", "C")
    print("Modified scale for RomanNumeral('iv','C'):")
    print([p.name for p in ms1])
    # Expected output: ['F', 'G', 'Ab', 'B', 'C', 'D', 'E']

    ms2 = getMinimallyModifiedScale("I[add#11]", "D")
    print("\nModified scale for RomanNumeral('I[add#11]','D'):")
    print([p.name for p in ms2])
    # Expected output: ['D', 'E', 'F#', 'G#', 'A', 'B', 'C#']
