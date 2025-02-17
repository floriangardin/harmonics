import dotenv
dotenv.load_dotenv()
import argparse

from harmonics import HarmonicsParser   

file = 'data/bach_1.erntxt'

text2 = """
Time Signature: 4/4
Form: Ternary
m1   b1 d: I
"""


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default='data/bach_1.erntxt')
    args = parser.parse_args()
    file = args.file

    with open(file, 'r') as f:
        text = f.read()

    parser = HarmonicsParser()

    # tree = parser.parse(text)
    # melody = tree.melody
    # print(tree)
    # print(melody)
    parser.parse_to_midi(text, "test.mid")
    #   tree = parser.parse_to_mxl(text, "test.mxl")
    # print(tree)