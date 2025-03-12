import os
import re
from lark import Lark
from music21.pitch import Pitch

from .transformer import transform_document
from .commons import to_mxl, to_midi, to_audio, to_ern, from_mxl
from harmonics.score_models import Score

CURRENT_FILEPATH = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_FILEPATH = os.path.join(CURRENT_FILEPATH, "grammar.ebnf")

from lark import Lark, Token, Transformer, Discard


class SpaceTransformer(Transformer):
    def WS(self, tok: Token):
        return Discard


class HarmonicsParser:
    def __init__(self):
        self.grammar_file = GRAMMAR_FILEPATH
        with open(self.grammar_file, "r") as f:
            self.grammar = f.read()
        self.parser = Lark(
            self.grammar,
            parser="earley",
            propagate_positions=True,
            maybe_placeholders=False,
        )

    def prepare_input(self, input_string):
        # Basic replacements
        input_string = input_string.replace("`", "").replace("%", "ø").replace("º", "o")
        input_string = input_string.replace("//", "Note:")
        input_string = input_string.replace("Fr+", "Fr")

        # Optimize whitespace for parsing performance
        # 1. Normalize all whitespace in measure lines to single spaces,
        #    except between beat indicators and their content
        lines = input_string.split("\n")
        optimized_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                optimized_lines.append(line)
                continue

            # If it's a measure line or melody line or accompaniment line, optimize whitespace
            if re.match(r"^(m|mel|acc)\d+", line.strip()):
                # First preserve the prefix (m1, mel1 V1, etc.)
                prefix_match = re.match(r"^([^b]*?)(?=b\d+|\Z)", line)
                if prefix_match:
                    prefix = prefix_match.group(1).strip()

                    # Check if the line contains variable calling
                    if "@" in line and not re.search(r"b\d+(?:\.\d+)?", line):
                        # Handle variable calling lines differently - keep as is
                        optimized_lines.append(line.strip())
                        continue

                    # Extract all beats and their content
                    beat_matches = re.finditer(
                        r"b(\d+(?:\.\d+)?)\s+(.*?)(?=\s+b\d+|\Z)", line
                    )
                    beats = []

                    for match in beat_matches:
                        beat_num = match.group(1)
                        content = match.group(2).strip()
                        beats.append(f"b{beat_num} {content}")

                    # Reconstruct the line with optimized whitespace
                    optimized_line = prefix + " " + " ".join(beats)
                    optimized_lines.append(optimized_line)
                else:
                    # Fallback - just normalize spaces
                    optimized_lines.append(" ".join(line.split()))
            else:
                # For other lines, just keep as is
                optimized_lines.append(line)

        input_string = "\n".join(optimized_lines)

        # Add a newline at the end for the parser
        return input_string + "\n"

    def parse(self, input_string):
        tree = self.parser.parse(self.prepare_input(input_string))
        tree = SpaceTransformer().transform(tree)
        document = transform_document(tree)
        return document

    def parse_to_score(self, input_string):
        if input_string.endswith(".mxl"):
            return from_mxl(input_string)
        elif (
            input_string.endswith(".ern")
            or input_string.endswith(".erntxt")
            or input_string.endswith(".har")
        ):
            return self._load_and_parse_to_score_string(input_string)
        else:
            return self._parse_to_score_string(input_string)

    def _load_and_parse_to_score_string(self, input_string):
        with open(input_string, "r") as f:
            input_string = f.read()
        return self._parse_to_score_string(input_string)

    def _parse_to_score_string(self, input_string):
        document = self.parse(input_string)
        data = document.data
        notes = document.notes
        events = document.events
        score = Score(
            chords=data.chords,
            notes=notes,
            time_signatures=data.time_signatures,
            tempos=data.tempos,
            events=events,
            instruments=data.instruments,
            composer=data.composer,
            title=data.title,
        )
        return score

    def _to_json(self, score, filepath):
        D = score.model_dump()
        import json

        with open(filepath, "w") as f:
            json.dump(D, f, indent=4)
        return score

    def parse_to_mxl(self, input_string, output_filename):
        score = self.parse_to_score(input_string)
        to_mxl(output_filename, score)
        return score

    def parse_to_ern(self, input_filename, output_filename):
        score = self.parse_to_score(input_filename)
        to_ern(output_filename, score)
        return score

    def parse_to_midi(self, input_string, output_filename):
        score = self.parse_to_score(input_string)
        to_midi(output_filename, score)
        return score

    def parse_to_audio(self, input_string, output_filename):
        score = self.parse_to_score(input_string)
        to_audio(output_filename, score)
        return score
