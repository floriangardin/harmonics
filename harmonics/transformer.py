from typing import List, Optional, Union
from lark import Tree, Token
from .models import (
    Composer,
    Piece,
    Analyst,
    Proofreader,
    Movement,
    TimeSignature,
    KeySignature,
    MinorMode,
    MetadataLine,
    StatementLine,
    Line,
    Key,
    Chord,
    BeatItem,
    Measure,
    MeasureRange,
    Repeat,
    Note,
    PedalEntry,
    Pedal,
    Form,
    Comment,
    RomanTextDocument,
)

def transform_token(token: Token) -> str:
    return token.value

# ------------------------------
# Metadata lines transformer
# ------------------------------

def transform_metadata_line(node: Tree) -> MetadataLine:
    # node.data == "metadata_line"
    # It has a single child telling which type it is.
    child = node.children[0]
    if child.data == "composer_line":
        # composer_line: "Composer:" WS REST_LINE NEWLINE
        value = ""
        for token in child.children:
            if isinstance(token, Token) and token.type == "REST_LINE":
                value = transform_token(token).strip()
                break
        return Composer(composer=value)
    elif child.data == "piece_line":
        value = ""
        for token in child.children:
            if isinstance(token, Token) and token.type == "REST_LINE":
                value = transform_token(token).strip()
                break
        return Piece(piece=value)
    elif child.data == "analyst_line":
        value = ""
        for token in child.children:
            if isinstance(token, Token) and token.type == "REST_LINE":
                value = transform_token(token).strip()
                break
        return Analyst(analyst=value)
    elif child.data == "proofreader_line":
        value = ""
        for token in child.children:
            if isinstance(token, Token) and token.type == "REST_LINE":
                value = transform_token(token).strip()
                break
        return Proofreader(proofreader=value)
    elif child.data == "movement_line":
        for token in child.children:
            if isinstance(token, Token) and token.type == "MEASURE_NUMBER":
                return Movement(movement=transform_token(token))
        return Movement(movement="")
    elif child.data == "time_signature_line":
        numerator = 4
        denominator = 4
        
        for token in child.children:
            if isinstance(token, Tree) and token.data == "time_signature":
                for subchild in token.children:
                    if isinstance(subchild, Tree) and subchild.data == "numerator":
                        digits = ""
                        for subsubchild in subchild.children:
                            if isinstance(subsubchild, Token) and subsubchild.type == "DIGIT":
                                digits += subsubchild.value
                        numerator = int(digits)
                    elif isinstance(subchild, Tree) and subchild.data == "denominator":
                        digits = ""
                        for subsubchild in subchild.children:
                            if isinstance(subsubchild, Token) and subsubchild.type == "DIGIT":
                                digits += subsubchild.value
                        denominator = int(digits)
        return TimeSignature(numerator=numerator, denominator=denominator)
    elif child.data == "key_signature_line":
        for token in child.children:
            if isinstance(token, Token) and token.type == "SIGNED_INT":
                return KeySignature(key_signature=transform_token(token))
        return KeySignature(key_signature="")
    elif child.data == "minor_mode_line":
        for token in child.children:
            if isinstance(token, Token) and token.type == "MINOR_MODE_OPTION":
                return MinorMode(minor_mode=transform_token(token))
        return MinorMode(minor_mode="")
    else:
        raise ValueError(f"Unknown metadata_line type: {child.data}")

# ------------------------------
# Chord and related transformers
# ------------------------------

def transform_standard_chord(node: Tree) -> str:
    # standard_chord: [chord_accidental] numeral [chord_quality] [inversion]
    chord_accidental = ""
    numeral = ""
    chord_quality = ""
    inversion = ""
    for child in node.children:
        if isinstance(child, Tree) and child.data == "numeral":
            for token in child.children:
                if isinstance(token, Token) and token.type == "ROMAN_NUMERAL":
                    numeral = transform_token(token)
        elif isinstance(child, Tree) and child.data == "chord_accidental":
            chord_accidental = ""
            for token in child.children:
                if isinstance(token, Token) and token.type == "ACCIDENTAL":
                    chord_accidental += transform_token(token)
        elif isinstance(child, Token):
            if child.type == "CHORD_QUALITY":
                chord_quality = transform_token(child)
        elif isinstance(child, Tree) and child.data == "inversion":
            inversion = transform_token(child.children[0])
    return chord_accidental + numeral + chord_quality + inversion

def transform_special_chord(node: Tree) -> str:
    # special_chord: SPECIAL_CHORD [inversion]
    special = ""
    inversion = ""
    for child in node.children:
        if isinstance(child, Token) and child.type == "SPECIAL_CHORD":
            special = transform_token(child)
        elif isinstance(child, Tree) and child.data == "inversion":
            inversion = transform_token(child.children[0])
    return special + inversion

def transform_chord_alteration(node: Tree) -> str:
    # chord_alteration: "[" alteration_content "]"
    for child in node.children:
        if isinstance(child, Tree) and child.data == "alteration_content":
            return transform_alteration_content(child)
    raise ValueError("ChordAlteration missing alteration_content")

def transform_alteration_content(node: Tree) -> str:
    # alteration_content: ((omit_alteration | add_alteration)? [ACCIDENTAL]? DIGITS)
    alt_type = ""
    accidental = ""
    digits = ""
    for child in node.children:
        if isinstance(child, Tree):
            if child.data == "omit_alteration":
                alt_type = "no"
            elif child.data == "add_alteration":
                alt_type = "add"
        elif isinstance(child, Token):
            if child.type == "ACCIDENTAL":
                accidental += transform_token(child)
            elif child.type == "DIGITS":
                digits += transform_token(child)
    return "[" + alt_type + accidental + digits + "]"

def transform_chord_component(node: Tree) -> str:
    # chord_component: (special_chord | standard_chord) chord_alteration*
    base = ""
    text = ""
    alterations = ""
    for child in node.children:
        if isinstance(child, Tree):
            if child.data == "special_chord":
                base = transform_special_chord(child)
            elif child.data == "standard_chord":
                base = transform_standard_chord(child)
            elif child.data == "chord_alteration":
                alterations = transform_chord_alteration(child)
    if base is None:
        raise ValueError("ChordComponent missing base chord")
    text = base + alterations
    return text

def transform_tonality_component(node: Tree) -> str:
    # tonality_component: [chord_accidental] numeral
    chord_accidental = ""
    numeral = ""
    for child in node.children:
        if isinstance(child, Tree) and child.data == "numeral":
            for token in child.children:
                if isinstance(token, Token) and token.type == "ROMAN_NUMERAL":
                    numeral = transform_token(token)
        elif isinstance(child, Tree) and child.data == "chord_accidental":
            chord_accidental = ""
            for token in child.children:
                if isinstance(token, Token) and token.type == "ACCIDENTAL":
                    chord_accidental += transform_token(token)
    return chord_accidental + numeral


def transform_chord(node: Tree) -> str:

    final_str = ""
    for child in node.children:
        if isinstance(child, Tree):
            if child.data == "chord_component":
                final_str += transform_chord_component(child)
            elif child.data == "tonality_component":
                final_str += "/" + transform_tonality_component(child)
    return final_str


# ------------------------------
# Beat and key-change transformers
# ------------------------------

def transform_key(node: Tree) -> Key:
    # key: KEY
    for child in node.children:
        if isinstance(child, Token) and child.type == "KEY":
            return transform_token(child)[:-1]
    raise ValueError("key missing KEY token")

def transform_beat_chord(node: Tree) -> Chord:
    # beat_chord: WS BEAT_INDICATOR (WS key)? WS chord
    beat_number = 1
    key = None
    chord = None
    for child in node.children:
        if isinstance(child, Token) and child.type == "BEAT_INDICATOR":
            beat_number = float(child.value[1:])
        elif isinstance(child, Tree):
            if child.data == "key":
                key = transform_key(child)
            elif child.data == "chord":
                chord = transform_chord(child)
    if chord is None:
        raise ValueError("Chord missing chord")
    return Chord(beat=beat_number, key=key, chord=chord)

def transform_key_change(node: Tree) -> Key:
    # key_change: WS key
    key_obj = None
    for child in node.children:
        if isinstance(child, Tree) and child.data == "key":
            key_obj = transform_key(child)
    if key_obj is None:
        raise ValueError("KeyChange missing key")
    return Key(key=key_obj)

# ------------------------------
# Measure line transformer
# ------------------------------

def transform_measure_line(node: Tree) -> Measure:
    # measure_line: MEASURE_INDICATOR (chord_beat_1)? (beat_chord | key_change)+ PHRASE_BOUNDARY? NEWLINE
    measure_number = 0
    beat_items: List[BeatItem] = []
    phrase_boundary = None
    for child in node.children:
        if isinstance(child, Token) and child.type == "MEASURE_INDICATOR":
            measure_number = int(child.value[1:])
        elif isinstance(child, Tree):
            if child.data == "chord_beat_1":
                beat_items.append(transform_beat_chord(child))
            elif child.data == "beat_chord":
                beat_items.append(transform_beat_chord(child))
            elif child.data == "key_change":
                beat_items.append(transform_key_change(child))
            elif child.data == "PHRASE_BOUNDARY":
                # For simplicity we join the token children
                phrase_boundary = "".join(transform_token(c) for c in child.children if isinstance(c, Token))
    return Measure(
        measure_number=measure_number,
        beat_items=beat_items,
        phrase_boundary=phrase_boundary
    )

# ------------------------------
# Pedal line transformer
# ------------------------------

def transform_pedal_entry(node: Tree) -> PedalEntry:
    # pedal_entry: MEASURE_INDICATOR WS BEAT_INDICATOR
    measure_indicator = ""
    beat_indicator = ""
    for child in node.children:
        if isinstance(child, Token):
            if child.type == "MEASURE_INDICATOR":
                measure_indicator = transform_token(child)
            elif child.type == "BEAT_INDICATOR":
                beat_indicator = transform_token(child)
    return PedalEntry(measure_indicator=measure_indicator, beat_indicator=beat_indicator)

def transform_note_in_pedal(node: Tree) -> Note:
    # note: NOTELETTER ACCIDENTAL?
    noteletter = ""
    accidental = None
    for child in node.children:
        if isinstance(child, Token) and child.type == "NOTELETTER":
            noteletter = transform_token(child)
        elif isinstance(child, Token) and child.type == "ACCIDENTAL":
            accidental = transform_token(child)
    return Note(noteletter=noteletter, accidental=accidental)

def transform_pedal_line(node: Tree) -> Pedal:
    # pedal_line: "Pedal:" WS note WS pedal_entries NEWLINE
    note_obj = None
    pedal_entries = []
    for child in node.children:
        if isinstance(child, Tree) and child.data == "note":
            note_obj = transform_note_in_pedal(child)
        elif isinstance(child, Tree) and child.data == "pedal_entries":
            for subchild in child.children:
                if isinstance(subchild, Tree) and subchild.data == "pedal_entry":
                    pedal_entries.append(transform_pedal_entry(subchild))
    if note_obj is None:
        raise ValueError("PedalLine missing note")
    return Pedal(note=note_obj, pedal_entries=pedal_entries)

# ------------------------------
# Form and Note line transformers
# ------------------------------

def transform_form_line(node: Tree) -> Form:
    # form_line: "Form:" WS REST_LINE NEWLINE
    form_value = ""
    for child in node.children:
        if isinstance(child, Token) and child.type == "REST_LINE":
            form_value = transform_token(child).strip()
            break
    return Form(form=form_value)

def transform_note_line(node: Tree) -> Comment:
    # note_line: "Note:" WS REST_LINE NEWLINE
    note_value = ""
    for child in node.children:
        if isinstance(child, Token) and child.type == "REST_LINE":
            note_value = transform_token(child).strip()
            break
    return Comment(comment=note_value)

# ------------------------------
# Repeat line transformer
# ------------------------------

def transform_measure_range(node: Tree) -> MeasureRange:
    # measure_range: MEASURE_INDICATOR ("-" MEASURE_INDICATOR)+
    measures = []
    for child in node.children:
        if isinstance(child, Token) and child.type == "MEASURE_INDICATOR":
            measures.append(transform_token(child))
    return MeasureRange(measures=measures)

def transform_repeat_line(node: Tree) -> Repeat:
    # repeat_line: measure_range WS "=" WS measure_range NEWLINE
    ranges = []
    equals = ""
    for child in node.children:
        if isinstance(child, Tree) and child.data == "measure_range":
            ranges.append(transform_measure_range(child))
        elif isinstance(child, Token) and child.value == "=":
            equals = transform_token(child)
    if len(ranges) != 2:
        raise ValueError("RepeatLine must have two measure ranges")
    return Repeat(start_range=ranges[0], equals=equals, end_range=ranges[1])

# ------------------------------
# Statement line transformer
# ------------------------------

def transform_statement_line(node: Tree) -> StatementLine:
    # statement_line: measure_line | pedal_line | form_line | note_line | repeat_line
    child = node.children[0]
    if child.data == "measure_line":
        return transform_measure_line(child)
    elif child.data == "pedal_line":
        return transform_pedal_line(child)
    elif child.data == "form_line":
        return transform_form_line(child)
    elif child.data == "note_line":
        return transform_note_line(child)
    elif child.data == "repeat_line":
        return transform_repeat_line(child)
    else:
        raise ValueError(f"Unknown statement_line type: {child.data}")

# ------------------------------
# New Function to Populate Properties
# ------------------------------


def parse_key_signature(key_signature: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parses the key signature string to extract mode and tonality.
    This is a placeholder and should be adjusted based on actual key encoding.
    """
    # Example implementation:
    # Assuming key_signature is in the format "C:maj" or "Am"
    if ':' in key_signature:
        tonality, mode = key_signature.split(':', 1)
    elif key_signature.endswith('m'):
        tonality = key_signature[:-1]
        mode = 'minor'
    else:
        tonality = key_signature
        mode = 'major'
    return mode, tonality

# ------------------------------
# Top-level document transformer
# ------------------------------

def transform_document(tree: Tree) -> RomanTextDocument:
    lines = []
    for child in tree.children:
        if isinstance(child, Token):
            pass
        elif child.data == 'line':
            for subchild in child.children:
                if subchild.data == "metadata_line":
                    lines.append(transform_metadata_line(subchild))
                elif subchild.data == "statement_line":
                    lines.append(transform_statement_line(subchild))
    document = RomanTextDocument(lines=lines)
    return document 