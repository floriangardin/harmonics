from harmonics.notes_utils import (
    getPitchFromInterval,
    getMinimallyModifiedScale,
    getPitchFromIntervalFromMinimallyModifiedScale,
)

from music21 import roman, pitch


def test_chord_pitch_from_interval():
    assert getPitchFromInterval("IV", "C", "b3", 0) == pitch.Pitch("Ab4").nameWithOctave
    assert (
        getPitchFromInterval("IV[no5]", "C", "b5", 0)
        == pitch.Pitch("C-5").nameWithOctave
    )
    # When secondary roman numeral is not used, we use the base scale for intervals
    assert getPitchFromInterval("iv", "C", "3", 0) == pitch.Pitch("A4").nameWithOctave
    # When secondary roman numeral is used, we use the secondary scale for intervals
    assert (
        getPitchFromInterval("iv/i", "C", "3", 0) == pitch.Pitch("A-4").nameWithOctave
    )
    # Again when secondary roman numeral is not used, we use the base scale for intervals
    assert getPitchFromInterval("iv", "c", "3", 0) == pitch.Pitch("A-4").nameWithOctave
    # So when using a flat interval on an already flattened note, we get a double flat
    assert (
        getPitchFromInterval("iv", "c", "b3", 0) == pitch.Pitch("A--4").nameWithOctave
    )


def test_getPitchFromIntervalFromMinimallyModifiedScale():
    assert (
        getPitchFromIntervalFromMinimallyModifiedScale("iv", "C", "3", 0)
        == pitch.Pitch("A-4").nameWithOctave
    )
    assert (
        getPitchFromIntervalFromMinimallyModifiedScale("IV[no5]", "C", "b5", 0)
        == pitch.Pitch("C-4").nameWithOctave
    )
    assert (
        getPitchFromIntervalFromMinimallyModifiedScale("I", "C", "9", 0)
        == pitch.Pitch("D5").nameWithOctave
    )
    assert (
        getPitchFromIntervalFromMinimallyModifiedScale("I", "C", "b8", 0)
        == pitch.Pitch("C-5").nameWithOctave
    )
    assert (
        getPitchFromIntervalFromMinimallyModifiedScale("I54", "C", "3", 0)
        == pitch.Pitch("E4").nameWithOctave
    )
    assert (
        getPitchFromIntervalFromMinimallyModifiedScale("Ib954", "C", "9", 0)
        == pitch.Pitch("D-5").nameWithOctave
    )


def test_getMinimallyModifiedScale():
    assert getMinimallyModifiedScale("iv", "C") == ["F", "G", "A-", "B", "C", "D", "E"]
    assert getMinimallyModifiedScale("I[add#11]", "D") == [
        "D",
        "E",
        "F#",
        "G#",
        "A",
        "B",
        "C#",
    ]
    assert getMinimallyModifiedScale("bii", "C") == [
        "D-",
        "E",
        "F-",
        "G",
        "A-",
        "B",
        "C",
    ]
    assert getMinimallyModifiedScale("N", "C") == ["D-", "E", "F", "G", "A-", "B", "C"]
    assert getMinimallyModifiedScale("N", "c") == [
        "D-",
        "E-",
        "F",
        "G",
        "A-",
        "B-",
        "C",
    ]
    assert getMinimallyModifiedScale("V", "c") == ["G", "A-", "B", "C", "D", "E-", "F"]
    assert getMinimallyModifiedScale("viio", "c") == [
        "B",
        "C",
        "D",
        "E-",
        "F",
        "G",
        "A-",
    ]
    assert getMinimallyModifiedScale("vii", "c") == [
        "B",
        "C",
        "D",
        "E-",
        "F#",
        "G",
        "A-",
    ]
    assert getMinimallyModifiedScale("iv/i", "C") == [
        "F",
        "G",
        "A-",
        "B-",
        "C",
        "D",
        "E-",
    ]
