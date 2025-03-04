import pytest
from harmonics.parser import HarmonicsParser


def test_score_with_accompaniment():
    input_text = """
Composer: Test Composer
Piece: Test Piece with Accompaniment
Time Signature: 4/4
Movement: 1
m1 b1 C: I
acc1 b1 1 2
mel1 t1 C5 t2 E5 t3 G5
m2 b1 IV
acc2 b1 3 4
mel2 t1 D5 t2 F5 t3 A5
"""
    parser = HarmonicsParser()
    score = parser.parse_to_events(input_text)

    # Check that chords, melody and accompaniment are parsed
    assert len(score.chords) > 0
    assert len(score.melody) > 0
    # We expect an explicit accompaniment event in measure 1 and measure 2.
    # (There may also be default events if other measures are present.)
    assert len(score.accompaniment) >= 2

    # Check that voices were correctly parsed:
    # Find the accompaniment event in measure 1 (the first event chronologically)
    first_acc = score.accompaniment[0]
    second_acc = score.accompaniment[1]
    # In measure 1, we explicitly set voices [1,2]
    assert [el.voice for el in first_acc.voices] == [1, 2]
    # In measure 2, we explicitly set voices [3,4]
    assert [el.voice for el in second_acc.voices] == [3, 4]


if __name__ == "__main__":
    pytest.main()
