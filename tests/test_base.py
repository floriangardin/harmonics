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
my_var_acc = b1 1234
m1 @my_var
m1 T1 @my_var_mel
m1 T2 @my_var_acc
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
Instrument: T1=piano, T2=pizzicato
m1 T1 b1 1234
"""


def test_instruments():
    parser = HarmonicsParser()
    tree = parser.parse(text_with_instruments)
    assert tree is not None


text_with_continuation = r"""
Time Signature: 4/4
Note: test
m1 c: I
m1 b1 C5
m2 c: V
m2 b1 L
"""


def test_continuation():
    parser = HarmonicsParser()
    tree = parser.parse(text_with_continuation)
    assert tree is not None


text_with_techniques = r"""
Time Signature: 4/4
Note: test
tech [T1] (m1 b1 - m4 b3) : legato
tech [T1] (m1 b1 - m40 b3) : accent
m1 T1 b1 C5
m2 T1 b1 C#5
"""


def test_techniques():
    parser = HarmonicsParser()
    tree = parser.parse(text_with_techniques)
    assert tree is not None
