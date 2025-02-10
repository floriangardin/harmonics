from harmonics import HarmonicsParser   

text = r"""
Time Signature: 4/4
m1 b1 c: i b2 i[add9] b3 i[add13]
m2 b1 I+ b3 vi6
m3 I7 b3 V7/#iii
m4 e: i
m5 i[add9][add13]
m6 i[add9][add13]
m7 i[add9][add13]
"""

parser = HarmonicsParser()
tree = parser.parse_to_midi(text, "test.mid")
print(tree)