from harmonics.chord_parser import ChordParser

def test_positive_chord_parser_with_key():
    assert ChordParser().is_chord("a: V")

def test_positive_chord_parser_with_text_comment():
    assert ChordParser().is_chord("V7/V")

def test_negative_chord_parser():
    assert not ChordParser().is_chord("not a chord")
