import harmonics.models as models
from harmonics.score import ScoreDocument
from typing import List, Tuple
from harmonics.commons.utils_techniques import resolve_techniques


def test_techniques():
    # Create a simple document with time signatures and techniques
    lines = [
        models.TimeSignature(numerator=4, denominator=4, measure_number=1),
        models.Technique(
            voice_names=["V1"],
            technique_range=models.TechniqueRange(
                start_measure=1, start_beat=1.0, end_measure=2, end_beat=1.0
            ),
            techniques=["staccato"],
        ),
        models.Technique(
            voice_names=["V1", "V2"],
            technique_range=models.TechniqueRange(
                start_measure=2, start_beat=1.0, end_measure=3, end_beat=1.0
            ),
            techniques=["legato", "forte"],
        ),
        models.Melody(measure_number=1, notes=[], voice_name="V1"),
    ]

    doc = ScoreDocument(lines=lines)
    techniques = doc.techniques

    # Test that the correct number of technique items are created
    # First technique: 1 voice * 1 technique = 1 item
    # Second technique: 2 voices * 2 techniques = 4 items
    assert len(techniques) == 5

    # Test the first technique (staccato for V1)
    staccato_items = [t for t in techniques if t.technique == "staccato"]
    assert len(staccato_items) == 1
    assert staccato_items[0].voice_name == "V1"
    assert staccato_items[0].time_start == 0.0  # Measure 1, beat 1
    assert (
        staccato_items[0].time_end == 4.0
    )  # Measure 2, beat 1 (after one 4/4 measure)

    # Test the second technique (legato and forte for V1 and V2)
    legato_items = [t for t in techniques if t.technique == "legato"]
    assert len(legato_items) == 2  # One for each voice
    forte_items = [t for t in techniques if t.technique == "forte"]
    assert len(forte_items) == 2  # One for each voice

    # Check that both voices have the techniques
    v1_items = [t for t in techniques if t.voice_name == "V1"]
    v2_items = [t for t in techniques if t.voice_name == "V2"]
    assert len(v1_items) == 3  # staccato, legato, forte
    assert len(v2_items) == 2  # legato, forte


def test_techniques_with_different_time_signatures():
    # Test with different time signatures
    lines = [
        models.TimeSignature(numerator=4, denominator=4, measure_number=1),
        models.Technique(
            voice_names=["V1"],
            technique_range=models.TechniqueRange(
                start_measure=1, start_beat=2.0, end_measure=3, end_beat=1.0
            ),
            techniques=["pizzicato"],
        ),
        models.Melody(measure_number=1, notes=[], voice_name="V1"),
        models.TimeSignature(numerator=3, denominator=4, measure_number=2),
        models.Melody(measure_number=2, notes=[], voice_name="V1"),
    ]

    doc = ScoreDocument(lines=lines)
    techniques = doc.techniques

    # Check that the technique spans correctly across different time signatures
    assert len(techniques) == 1
    technique = techniques[0]
    assert technique.voice_name == "V1"
    assert technique.technique == "pizzicato"

    # Measure 1 (4/4) starts at 0.0, beat 2 is at 1.0
    assert technique.time_start == 1.0

    # Measure 2 (3/4) starts at 4.0, Measure 3 would start at 7.0, beat 1 is at 7.0
    assert technique.time_end == 7.0


def test_techniques_with_multiple_techniques_same_range():
    # Test multiple techniques applied to the same range
    lines = [
        models.TimeSignature(numerator=4, denominator=4, measure_number=1),
        models.Technique(
            voice_names=["V1"],
            technique_range=models.TechniqueRange(
                start_measure=1, start_beat=1.0, end_measure=1, end_beat=4.0
            ),
            techniques=["staccato", "forte", "accent"],
        ),
        models.Melody(measure_number=1, notes=[], voice_name="V1"),
    ]

    doc = ScoreDocument(lines=lines)
    techniques = doc.techniques

    # Check that all three techniques are created for the same voice and range
    assert len(techniques) == 3

    # All techniques should have the same time range
    for technique in techniques:
        assert technique.voice_name == "V1"
        assert technique.time_start == 0.0  # Measure 1, beat 1
        assert technique.time_end == 3.0  # Measure 1, beat 4

    # Check that all three technique types are present
    technique_names = [t.technique for t in techniques]
    assert "staccato" in technique_names
    assert "forte" in technique_names
    assert "accent" in technique_names


def test_techniques_with_measure_beyond_declared_measures():
    # Test technique that extends beyond the last declared measure
    lines = [
        models.TimeSignature(numerator=4, denominator=4, measure_number=1),
        models.Technique(
            voice_names=["V1"],
            technique_range=models.TechniqueRange(
                start_measure=1,
                start_beat=1.0,
                end_measure=5,  # Beyond any declared measure
                end_beat=1.0,
            ),
            techniques=["tremolo"],
        ),
        models.Melody(measure_number=1, notes=[], voice_name="V1"),
    ]

    doc = ScoreDocument(lines=lines)
    techniques = doc.techniques

    # Check that the technique extends correctly
    assert len(techniques) == 1
    technique = techniques[0]
    assert technique.voice_name == "V1"
    assert technique.technique == "tremolo"
    assert technique.time_start == 0.0  # Measure 1, beat 1

    # End time should be calculated by adding the duration of the extra measures
    # Measure 1 ends at 4.0, then 4 more measures of 4/4 = 16.0 more beats
    assert technique.time_end == 16.0  # Measure 5, beat 1


def test_get_techniques_for_note():
    # Test the get_techniques_for_note method
    lines = [
        models.TimeSignature(numerator=4, denominator=4, measure_number=1),
        models.Technique(
            voice_names=["V1"],
            technique_range=models.TechniqueRange(
                start_measure=1, start_beat=1.0, end_measure=2, end_beat=1.0
            ),
            techniques=["staccato"],
        ),
        models.Technique(
            voice_names=["V1"],
            technique_range=models.TechniqueRange(
                start_measure=1, start_beat=2.0, end_measure=1, end_beat=4.0
            ),
            techniques=["forte"],
        ),
        models.Melody(measure_number=1, notes=[], voice_name="V1"),
    ]

    doc = ScoreDocument(lines=lines)
    techniques = doc.techniques

    # Test a note at measure 1, beat 1 (only staccato applies)
    active_techniques = doc.get_techniques_for_note(0.0, "V1", techniques)
    assert len(active_techniques) == 1
    assert "staccato" in active_techniques

    # Test a note at measure 1, beat 2 (both staccato and forte apply)
    active_techniques = doc.get_techniques_for_note(1.0, "V1", techniques)
    assert len(active_techniques) == 2
    assert "staccato" in active_techniques
    assert "forte" in active_techniques

    # Test a note at measure 1, beat 4 (only staccato applies, as forte ends exactly at beat 4)
    active_techniques = doc.get_techniques_for_note(3.0, "V1", techniques)
    assert len(active_techniques) == 1
    assert "staccato" in active_techniques

    # Test a note for a different voice (no techniques should apply)
    active_techniques = doc.get_techniques_for_note(1.0, "V2", techniques)
    assert len(active_techniques) == 0

    # Test a note outside any technique range
    active_techniques = doc.get_techniques_for_note(5.0, "V1", techniques)
    assert len(active_techniques) == 0


def test_resolve_techniques():
    techniques = ["staccato", "legato", "p", "f", "accent"]
    resolved_techniques = resolve_techniques(techniques)
    assert resolved_techniques == ["legato", "f", "accent"]
