from harmonics import HarmonicsParser

text = r"""
Time Signature: 4/4
Note: test
m1 b1 c: #vi6[add9][add##11]/V/##ii b3 Ger65/i
m2 b2 C: I/II b3 It
"""


def test_complicated_chords():
    parser = HarmonicsParser()
    tree = parser.parse(text)


def test_no_beat_one():
    parser = HarmonicsParser()
    text = r"""
    Time Signature: 4/4
    Note: test
    m1 c: I
    """
    tree = parser.parse(text)


text_with_variable = r"""
Time Signature: 4/4
Note: test
my_var = c: I b3 V
my_var_mel = b1 C5
my_var_acc = b1 1 2 3 4
m1 @my_var
mel1 @my_var_mel
acc1 @my_var_acc
"""


def test_variable():
    parser = HarmonicsParser()
    tree = parser.parse(text_with_variable)
    assert tree is not None


text_with_events = r"""
Time Signature: 4/4
Note: test
e1 b1 tempo(110)
m1 c: I
m2 c: V
"""


def test_events():
    parser = HarmonicsParser()
    tree = parser.parse(text_with_events)
    assert tree is not None


text_with_instruments = r"""
Time Signature: 4/4
Note: test
Instrument: V1=piano, V2=pizzicato_strings
acc1 b1 1234
"""


def test_instruments():
    parser = HarmonicsParser()
    tree = parser.parse(text_with_instruments)
    assert tree is not None
