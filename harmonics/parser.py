import os
from lark import Lark
from music21.pitch import Pitch

from .transformer import transform_document
from .romanyh import generateBestHarmonization
from .commons import to_mxl, to_midi, to_audio
from .score import Score

CURRENT_FILEPATH = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_FILEPATH = os.path.join(CURRENT_FILEPATH, "ebnf.txt")


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
        input_string = input_string.replace("`", "").replace("%", "ø").replace("º", "o")
        input_string = input_string.replace("//", "Note:")
        return input_string + "\n"

    def parse(self, input_string):
        tree = self.parser.parse(self.prepare_input(input_string))
        document = transform_document(tree)
        return document

    def parse_to_events(self, input_string):
        document = self.parse(input_string)
        chords, time_signatures, tempos, instruments = document.data
        if len(chords) > 0:
            progression = generateBestHarmonization(
                chords,
                closePosition=False,
                firstVoicing=None,
                lastVoicing=None,
                allowedUnisons=0,
            )
        else:
            progression = []

        for chord, pitches in zip(chords, progression):
            pitches = [Pitch(p).nameWithOctave for p in pitches]
            chord.pitches = pitches

        melody = document.melody
        events = document.events
        score = Score(
            chords=chords,
            melody=melody,
            accompaniment=document.accompaniment,
            time_signatures=time_signatures,
            tempos=tempos,
            events=events,
            instruments=instruments,
        )
        return score

    def parse_to_mxl(self, input_string, output_filename):
        score = self.parse_to_events(input_string)
        to_mxl(output_filename, score)
        return score

    def parse_to_midi(self, input_string, output_filename):
        score = self.parse_to_events(input_string)
        to_midi(output_filename, score)
        return score

    def parse_to_audio(self, input_string, output_filename):
        score = self.parse_to_events(input_string)
        to_audio(output_filename, score)
        return score
