
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
