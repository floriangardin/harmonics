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
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=False,
        )

    def prepare_input(self, input_string):
        # Basic replacements
        input_string = input_string.replace("`", "").replace("%", "ø").replace("º", "o")
        input_string = input_string.replace("//", "Note: ")
        input_string = input_string.replace("Fr+", "Fr")
        input_string = "\n".join(input_string.split("\n"))

        return input_string + "\n"

    def parse(self, input_string):
        import time

        start_time = time.time()
        clean_input = self.prepare_input(input_string)
        tree = self.parser.parse(clean_input)
        document = transform_document(tree)
        end_time = time.time()
        print(f"Document parsed and transformed in {end_time - start_time} seconds")
        return document

    def parse_to_score(self, input_string):
        if input_string.endswith(".mxl") or input_string.endswith(".musicxml"):
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
        import time

        start_time = time.time()
        data = document.data
        end_time = time.time()
        print(f"Data extracted in {end_time - start_time} seconds")
        start_time = time.time()
        notes = document.notes
        end_time = time.time()
        print(f"Notes extracted in {end_time - start_time} seconds")
        start_time = time.time()
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
            clefs=data.clefs,
            key_signatures=data.key_signatures,
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
