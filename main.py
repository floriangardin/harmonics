import dotenv

dotenv.load_dotenv()
import argparse

from harmonics import HarmonicsParser
from harmonics.commons import to_audio

file = "data/bach_1.erntxt"

text2 = """
Time Signature: 4/4
Form: Ternary
m1   b1 d: I
"""


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        default="data/composition.ern",
        help="Input file path",
    )
    parser.add_argument(
        "output", type=str, nargs="?", default="test.mid", help="Output file path"
    )
    args = parser.parse_args()
    file = args.file

    output_file = args.output
    parser = HarmonicsParser()

    # tree = parser.parse(text)
    # melody = tree.melody
    # print(tree)
    # print(melody)

    output_type = output_file.split(".")[-1]
    input_type = file.split(".")[-1]
    if input_type in ["mxl", "musicxml"]:
        if output_type == "ern":
            parser.parse_to_ern(file, output_file)

    elif input_type in ["ern", "erntxt", "har"]:
        with open(file, "r") as f:
            text = f.read()
        if output_type == "mid":
            parser.parse_to_midi(text, output_file)
        elif output_type in ["mxl", "musicxml"]:
            parser.parse_to_mxl(text, output_file)
        elif output_type == "mp3":
            parser.parse_to_audio(text, output_file)
        else:
            raise ValueError(f"Invalid output type: {output_type}")
    #   tree = parser.parse_to_mxl(text, "test.mxl")
    # print(tree)
