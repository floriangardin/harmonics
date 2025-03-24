import dotenv

dotenv.load_dotenv()
import argparse
from harmonics.score_models import Score
from harmonics import HarmonicsParser
from typing import List


def format_chord(chord: str):
    result = ""
    key = ""
    if chord.new_key:
        key = f"{chord.key}: "
    pitches = [p.replace('-', 'b') for p in chord.pitches]
    result += f"b{chord.beat} {key}{chord.chord}->{",".join(pitches)} "
    return result

def format_chord_line(chords: List[str], measure_number: int):
    result = " ".join(chords)
    return f"// m{measure_number} {result}"


def write_harmony(score: Score, text: str):
    lines = text.split("\n")
    lines_result_dict = {}
    line_number_measure_number_dict = {}
    for chord in score.chords:
        if chord.line_number not in lines_result_dict:
            lines_result_dict[chord.line_number] = []
        lines_result_dict[chord.line_number].append(format_chord(chord))
        line_number_measure_number_dict[chord.line_number] = chord.measure_number
    
    for line_number, chords in lines_result_dict.items():
        lines_result_dict[line_number] = format_chord_line(chords, line_number_measure_number_dict[line_number])

    # Create a new list of lines with the chord information inserted
    result_lines = []
    for i, line in enumerate(lines):
        result_lines.append(line)
        # If this line number has chord information, add it after the original line
        if i+1 in lines_result_dict:
            result_lines.append(lines_result_dict[i+1])
    
    return "\n".join(result_lines)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        default="data/composition.ern",
        help="Input file path",
    )
    args = parser.parse_args()
    file = args.file
    parser = HarmonicsParser()
    input_type = file.split(".")[-1]
    if input_type in ["ern", "erntxt", "har"]:
        with open(file, "r") as f:
            text = f.read()
    else:
        raise ValueError(
            f"Invalid input type: {input_type}. Need to be ERN format"
        )

    score = parser.parse_to_score(text)

    new_text = write_harmony(score, text)
    # write to file
    with open(file, "w") as f:
        f.write(new_text)