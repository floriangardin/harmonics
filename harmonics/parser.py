from lark import Lark
import os
from music21.pitch import Pitch
from music21.stream import Stream

from .transformer import transform_document
from .romanyh.voicing import solveProgressionChords, generateHarmonization
from .commons.to_midi import events_to_midi

CURRENT_FILEPATH = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_FILEPATH = os.path.join(CURRENT_FILEPATH, 'ebnf.txt')
SIMPLIFIED_GRAMMAR_FILEPATH = os.path.join(CURRENT_FILEPATH, 'simplified_ebnf.txt')

class HarmonicsParser:
    def __init__(self):
        self.grammar_file = GRAMMAR_FILEPATH
        with open(self.grammar_file, 'r') as f:
            self.grammar = f.read()
        self.parser = Lark(self.grammar, parser='earley', 
                           propagate_positions=True, 
                           maybe_placeholders=False)

    def parse(self, input_string):
        tree = self.parser.parse(input_string)
        document = transform_document(tree)
        return document
    

    def parse_to_events(self, input_string):

        document = self.parse(input_string)
        chords = document.chords
        costTable = solveProgressionChords(chords, closePosition=False,  firstVoicing=None, lastVoicing=None, allowedUnisons=0)
        scores = []
        for progression, cost in generateHarmonization(costTable):
            scores.append(progression)

        for chord, progression in zip(chords, scores[0]):
            pitches = [Pitch(p).midi for p in progression]
            chord.pitches = pitches

        return chords

    def parse_to_midi(self, input_string, output_filename):
        def to_midi(filepath, score, tempo=120):
            # Transform to list of events
            events = []
            for s in score:
                for idx, pitch in enumerate(s.pitches):
                    events.append([s.time, pitch,s.duration, 1, 100])
            events_to_midi(events, filepath, tempo)

        chords = self.parse_to_events(input_string)

        to_midi(output_filename, chords)
        return chords