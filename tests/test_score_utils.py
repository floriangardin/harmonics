import pytest
from harmonics.score import get_measure_map, bar_duration_in_quarters
from harmonics.models import TimeSignature, Melody, Events, MelodyNote
from harmonics.exceptions import (
    TimeSignatureAlreadyDeclared,
    TimeSignatureNotDeclared,
    TimeSignatureMeasureMustBeDeclared,
)


def test_get_measure_map_single_time_signature():
    """Test get_measure_map with a single time signature (4/4) throughout."""
    # Create a simple score with a single time signature
    lines = [
        TimeSignature(numerator=4, denominator=4),
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=3, notes=[], voice_name="v1", track_name="T1"),
    ]

    measure_map = get_measure_map(lines)

    # Check that we have 3 measures
    assert len(measure_map) == 3

    # In 4/4, each measure is 4 quarter notes
    assert measure_map[1] == (0, 4, (4, 4))  # Measure 1: 0-4 quarters
    assert measure_map[2] == (4, 8, (4, 4))  # Measure 2: 4-8 quarters
    assert measure_map[3] == (8, 12, (4, 4))  # Measure 3: 8-12 quarters


def test_get_measure_map_changing_time_signatures():
    """Test get_measure_map with changing time signatures."""
    # Create a score with changing time signatures
    lines = [
        TimeSignature(numerator=4, denominator=4),  # Initial 4/4 time signature
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=3, denominator=4),  # Change to 3/4 at measure 3
        Melody(measure_number=3, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=4, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=6, denominator=8),  # Change to 6/8 at measure 5
        Melody(measure_number=5, notes=[], voice_name="v1", track_name="T1"),
    ]

    measure_map = get_measure_map(lines)

    # Check that we have 5 measures
    assert len(measure_map) == 5

    # Measure durations based on time signatures
    # 4/4 = 4 quarters, 3/4 = 3 quarters, 6/8 = 3 quarters
    assert measure_map[1] == (0, 4, (4, 4))  # Measure 1: 0-4 quarters (4/4)
    assert measure_map[2] == (4, 8, (4, 4))  # Measure 2: 4-8 quarters (4/4)
    assert measure_map[3] == (8, 11, (3, 4))  # Measure 3: 8-11 quarters (3/4)
    assert measure_map[4] == (11, 14, (3, 4))  # Measure 4: 11-14 quarters (3/4)
    assert measure_map[5] == (14, 17, (6, 8))  # Measure 5: 14-17 quarters (6/8)


def test_get_measure_map_complex_time_signatures():
    """Test get_measure_map with complex time signatures like 5/4, 7/8."""
    lines = [
        TimeSignature(numerator=4, denominator=4),  # Initial 4/4
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=5, denominator=4),  # Change to 5/4
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=7, denominator=8),  # Change to 7/8
        Melody(measure_number=3, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=3, denominator=2),  # Change to 3/2
        Melody(measure_number=4, notes=[], voice_name="v1", track_name="T1"),
    ]

    measure_map = get_measure_map(lines)

    # Check measure durations
    assert measure_map[1] == (0, 4, (4, 4))  # Measure 1: 0-4 quarters (4/4)
    assert measure_map[2] == (4, 9, (5, 4))  # Measure 2: 4-9 quarters (5/4)
    assert measure_map[3] == (9, 12.5, (7, 8))  # Measure 3: 9-12.5 quarters (7/8)
    assert measure_map[4] == (12.5, 18.5, (3, 2))  # Measure 4: 12.5-18.5 quarters (3/2)


def test_get_measure_map_with_different_line_types():
    """Test get_measure_map with different line types (Melody, Events)."""
    lines = [
        TimeSignature(numerator=4, denominator=4),
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
        Events(measure_number=3, events=[]),
        TimeSignature(numerator=3, denominator=4),
        Melody(measure_number=4, notes=[], voice_name="v1", track_name="T1"),
    ]

    measure_map = get_measure_map(lines)

    assert len(measure_map) == 4
    assert measure_map[1] == (0, 4, (4, 4))  # Measure 1: 0-4 quarters (4/4)
    assert measure_map[2] == (4, 8, (4, 4))  # Measure 2: 4-8 quarters (4/4)
    assert measure_map[3] == (8, 12, (4, 4))  # Measure 3: 8-12 quarters (4/4)
    assert measure_map[4] == (12, 15, (3, 4))  # Measure 4: 12-15 quarters (3/4)


def test_get_measure_map_with_non_consecutive_measures():
    """Test get_measure_map with non-consecutive measure numbers."""
    lines = [
        TimeSignature(numerator=4, denominator=4),
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=3, notes=[], voice_name="v1", track_name="T1"),  # Skip measure 2
        Melody(measure_number=5, notes=[], voice_name="v1", track_name="T1"),  # Skip measure 4
    ]

    measure_map = get_measure_map(lines)

    # Even with skipped measures in the input, the function should create
    # a continuous map from 1 to the max measure number
    assert len(measure_map) == 5
    assert measure_map[1] == (0, 4, (4, 4))
    assert measure_map[2] == (4, 8, (4, 4))
    assert measure_map[3] == (8, 12, (4, 4))
    assert measure_map[4] == (12, 16, (4, 4))
    assert measure_map[5] == (16, 20, (4, 4))


def test_bar_duration_in_quarters():
    """Test the bar_duration_in_quarters helper function."""
    assert bar_duration_in_quarters((4, 4)) == 4.0
    assert bar_duration_in_quarters((3, 4)) == 3.0
    assert bar_duration_in_quarters((6, 8)) == 3.0
    assert bar_duration_in_quarters((5, 4)) == 5.0
    assert bar_duration_in_quarters((7, 8)) == 3.5
    assert bar_duration_in_quarters((3, 2)) == 6.0
    assert bar_duration_in_quarters((12, 8)) == 6.0


def test_get_measure_map_with_multiple_time_signatures_same_measure_raises_exception():
    """Test handling of multiple time signatures assigned to the same measure raises exception."""
    lines = [
        TimeSignature(numerator=4, denominator=4),
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(
            numerator=3, denominator=4
        ),  # This will be assigned to measure 2, will be ignored
        TimeSignature(
            numerator=2, denominator=4
        ),  # This will also be assigned to measure 2
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
    ]

    with pytest.raises(TimeSignatureAlreadyDeclared):
        get_measure_map(lines)


def test_get_measure_map_with_out_of_order_time_signatures_raises_exception():
    """Test handling of time signatures that appear out of order in the input raising exception when measures are not sorted and time signature measure number is not declared."""
    # In this test, we define time signatures for measures 5, 3, and 1 in that order
    lines = [
        # Define measure 1 time signature first
        TimeSignature(numerator=2, denominator=4),
        # But declare measure 5
        Melody(measure_number=5, notes=[], voice_name="v1", track_name="T1"),
        # Then define another time signature, will be applied to measure 6, because last line was 5
        TimeSignature(numerator=3, denominator=4),
        Melody(measure_number=3, notes=[], voice_name="v1", track_name="T1"),
        # Finally define measure 1's time signature
        TimeSignature(numerator=4, denominator=4),
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        # Add a few more measures without explicit time signatures
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=4, notes=[], voice_name="v1", track_name="T1"),
        Melody(measure_number=6, notes=[], voice_name="v1", track_name="T1"),
    ]

    with pytest.raises(TimeSignatureMeasureMustBeDeclared):
        measure_map = get_measure_map(lines)


def test_get_measure_map_with_out_of_order_time_signatures():
    """Test handling of time signatures that appear out of order in the input."""
    # In this test, we define time signatures for measures 5, 3, and 1 in that order
    lines = [
        # Define measure 1 time signature first
        # But declare measure 5
        Melody(measure_number=2, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=2, denominator=4, measure_number=1),
        Melody(measure_number=1, notes=[], voice_name="v1", track_name="T1"),
        TimeSignature(numerator=3, denominator=4, measure_number=3),
        Melody(measure_number=3, notes=[], voice_name="v1", track_name="T1"),
    ]

    measure_map = get_measure_map(lines)
    assert measure_map[1] == (0, 2, (2, 4))
    assert measure_map[2] == (2, 4, (2, 4))
    assert measure_map[3] == (4, 7, (3, 4))


if __name__ == "__main__":
    pytest.main()
