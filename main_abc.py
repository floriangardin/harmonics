from music21 import abcFormat

abcStr = """
M:6/8
L:1/8
K:G
B3 A3 G6 B3 A3 G6
"""
ah = abcFormat.ABCHandler()
junk = ah.process(abcStr)
ah.definesMeasures()

from pdb import set_trace; set_trace()
