import os
import re
from lark import Lark, Token, Transformer, Discard

CURRENT_FILEPATH = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_FILEPATH = os.path.join(CURRENT_FILEPATH, "chord_grammar.ebnf")

class SpaceTransformer(Transformer):
    def WS(self, tok: Token):
        return Discard

class ChordParser:
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
        return input_string

    def is_chord(self, input_string):
        try:    
            tree = self.parser.parse(self.prepare_input(input_string))
            tree = SpaceTransformer().transform(tree)
            return True
        except Exception as e:
            return False

    

