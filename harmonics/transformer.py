from typing import List, Optional, Union, Dict
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
    AbsoluteMelodyNote,
    Measure,
    MeasureRange,
    Repeat,
    Silence,
    Note,
    PedalEntry,
    Pedal,
    Form,
    Comment,
    RomanTextDocument,
    Melody,
    MelodyNote,
    Accompaniment,
    AccompanimentBeat,
    Tempo,
    Events,
    Event,
    Instrument,
    Instruments,
    AccompanimentVoice,
    VariableDeclaration,
    VariableCalling,
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
    elif child.data == "tempo_line":
        for token in child.children:
            if isinstance(token, Token) and token.type == "TEMPO_NUMBER":
                return Tempo(tempo=int(token.value))
        return Tempo(tempo=120)
    elif child.data == "instrument_line":
        return transform_instrument_line(child)
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
            for subchild in child.children:
                if isinstance(subchild, Token) and subchild.type == "INVERSION_STANDARD":
                    inversion = transform_token(subchild)
                elif isinstance(subchild, Tree) and subchild.data == "inversion_free":
                    for sschild in subchild.children:
                        inversion += sschild.value
    return chord_accidental + numeral + chord_quality + inversion

def transform_special_chord(node: Tree) -> str:
    # special_chord: SPECIAL_CHORD [inversion]
    special = ""
    inversion = ""
    for child in node.children:
        if isinstance(child, Token) and child.type == "SPECIAL_CHORD":
            special = transform_token(child)
        elif isinstance(child, Tree) and child.data == "inversion":
            for subchild in child.children:
                if isinstance(subchild, Token) and subchild.type == "INVERSION_STANDARD":
                    inversion = transform_token(subchild)
                elif isinstance(subchild, Tree) and subchild.data == "inversion_free":
                    for sschild in subchild.children:
                        inversion += sschild.value
    return special + inversion

def transform_chord_alteration(node: Tree) -> str:
    # chord_alteration: "[" alteration_content "]"
    alteration = ""
    for child in node.children:
        if isinstance(child, Tree) and child.data == "alteration_content":
            alteration += transform_alteration_content(child)
    return alteration

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
                alterations += transform_chord_alteration(child)
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
# Melody line transformer
# ------------------------------


def transform_melody_line(node: Tree) -> Melody:
    # melody_line: MELODY_MEASURE_INDICATOR (beat_note)* NEWLINE
    notes = []
    bar_octave = 0
    voice_name = "V1"
    for child in node.children:
        is_absolute_note = False
        is_silence = False
        if isinstance(child, Token) and child.type == "MELODY_MEASURE_INDICATOR":
            measure_number = int(child.value[len("mel"):])
        elif isinstance(child, Token) and child.type == "VOICE_NAME":
            voice_name = transform_token(child)
        elif isinstance(child, Tree) and child.data in ["beat_note", "first_beat_note"]:
            beat = 1
            octave = 0
            note = ""
            for token in child.children:
                if isinstance(token, Token):
                    if token.type == "MELODY_BEAT_INDICATOR":
                        beat = float(token.value[1:]) # Remove 't' prefix
                    elif token.type == "MELODY_NOTE":
                        note = token.value.replace('/', '')
                    elif token.type == "ABSOLUTE_NOTE":
                        note = token.value.replace('/', '')
                        is_absolute_note = True
                    elif token.type == "SILENCE":
                        is_silence = True
                    elif token.type == 'DELTA_OCTAVE':
                        octave = int(token.value[1:])
            if is_silence:
                notes.append(Silence(beat=beat))
            elif is_absolute_note:
                notes.append(AbsoluteMelodyNote(beat=beat, note=note))
            else:
                notes.append(MelodyNote(beat=beat, note=note, octave=octave, voice_name=voice_name))
            
    return Melody(measure_number=measure_number, notes=notes, voice_name=voice_name)
    
# ------------------------------
# Statement line transformer
# ------------------------------
def transform_accompaniment_line_content(node: Tree) -> List[AccompanimentBeat]:
    beats: List[AccompanimentBeat] = []
    for child in node.children:
        if isinstance(child, Token) and child.type == "BEAT_INDICATOR":
            beat = float(child.value[1:])
        elif isinstance(child, Tree) and child.data == "voice_list":
            voices: List[AccompanimentVoice] = []
            total_alteration = 0
            for subchild in child.children:
                if isinstance(subchild, Token) and subchild.type == "VOICE":
                    voices.append(AccompanimentVoice(voice=int(subchild.value), alteration=total_alteration))
                    total_alteration = 0
                elif isinstance(subchild, Token) and subchild.type == "OCTAVE":
                    octave = int(subchild.value[1:])
                    voices[-1].octave = octave
                elif isinstance(subchild, Token) and subchild.type == "ALTERATION":
                    total_alteration = subchild.value.count('+') - subchild.value.count('-')
            
            beats.append(AccompanimentBeat(beat=beat, voices=voices))
        elif isinstance(child, Token) and child.type == "SILENCE":
            beats.append(AccompanimentBeat(beat=beat, voices=[]))
    return beats

def transform_accompaniment_line(node: Tree, context: Dict[str, List[AccompanimentBeat]]) -> Accompaniment:
    # accompaniment_line: ACCOMPANIMENT_INDICATOR (voice_list)* NEWLINE
    measure_number = 0
    beats: List[AccompanimentBeat] = []
    for first_child in node.children:
        octave = 0
        if isinstance(first_child, Token) and first_child.type == "ACCOMPANIMENT_INDICATOR":
            # Remove the 'acc' prefix to get the measure number
            measure_number = int(first_child.value[3:])
        elif isinstance(first_child, Token) and first_child.type == "VARIABLE_CALLING":
            variable_name = first_child.value[1:]
            beats = context[variable_name]
        elif isinstance(first_child, Tree) and first_child.data == "accompaniment_line_content":
            beats += transform_accompaniment_line_content(first_child)

    return Accompaniment(measure_number=measure_number, beats=beats)


def transform_tempo_line(node: Tree) -> Tempo:
    # tempo_line: "Tempo:" WS TEMPO_NUMBER NEWLINE
    tempo = 0
    for child in node.children:
        if isinstance(child, Token) and child.type == "TEMPO_NUMBER":
            tempo = int(child.value)
    return Tempo(tempo=tempo)

def transform_instrument_line(node: Tree) -> Instruments:
    # instrument_line: "Instrument:" WS VOICE_NAME WS* "=" WS* GM_NUMBER NEWLINE
    instruments = []
    voice_name = ""
    gm_number = ""
    for child in node.children:
        if isinstance(child, Token) and child.type == "VOICE_NAME":
            voice_name = transform_token(child)
        elif isinstance(child, Token) and child.type == "GM_NUMBER":
            gm_number = int(transform_token(child))
            instruments.append(Instrument(voice_name=voice_name, gm_number=gm_number))
    return Instruments(instruments=instruments)

def transform_variable_declaration_line(node: Tree, context: Dict[str, List[AccompanimentBeat]]) -> Dict[str, List[AccompanimentBeat]]:
    # variable_declaration_line: VARIABLE_NAME WS* "=" WS* VARIABLE_VALUE NEWLINE
    variable_name = ""
    variable_value = ""
    beats = []
    for child in node.children:
        if isinstance(child, Token) and child.type == "VARIABLE_NAME":
            variable_name = transform_token(child)
        elif isinstance(child, Tree) and child.data == "variable_content":
            for subchild in child.children:
                if isinstance(subchild, Tree) and subchild.data == "accompaniment_line_content":
                    beats += transform_accompaniment_line_content(subchild)
    context[variable_name] = beats
    return None


def transform_statement_line(node: Tree, context: Dict[str, List[AccompanimentBeat]]) -> StatementLine:
    # statement_line: measure_line | pedal_line | form_line | note_line | repeat_line | melody_line | accompaniment_line
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
    elif child.data == "melody_line":
        return transform_melody_line(child)
    elif child.data == "accompaniment_line":
        return transform_accompaniment_line(child, context)
    elif child.data == "event_line":
        return transform_event_line(child)
    elif child.data == "variable_declaration_line":
        return transform_variable_declaration_line(child, context)
    else:
        raise ValueError(f"Unknown statement_line type: {child.data}")

# ------------------------------
# New Function to Populate Properties
# ------------------------------

"""
class Event(BaseModel):
    measure_number: int
    beat: float
    event_type: str
    event_value: str

class Events(BaseModel):
    events: List[Event]
    measure_number: int 
"""
def transform_event_line(node: Tree) -> Events:
    
    def eval_argument(argument: str) -> str:
        try:
            return eval(argument)
        except Exception as e:
            return eval('"' + argument + '"')
    measure_number = 0
    events: List[Event] = []
    # Parse measure number
    for child in node.children:
        if isinstance(child, Token) and child.type == "MEASURE_NUMBER":
            measure_number = int(child.value)
        elif isinstance(child, Tree) and child.data == "event_content":
            # event_content: BEAT_INDICATOR WS* event_type WS* event_value
            beat = 0.0
            event_type = ""
            event_value = ""
            
            for content_child in child.children:
                if isinstance(content_child, Token):
                    if content_child.type == "BEAT_INDICATOR":
                        # Remove 'b' or 't' prefix and convert to float
                        beat_str = content_child.value[1:]
                        beat = float(beat_str)
                    elif content_child.type == "EVENT_FUNCTION_NAME":
                        event_type = content_child.value
                    elif content_child.type == "EVENT_ARGUMENT":
                        event_value = eval_argument(content_child.value)
            event = Event(
                measure_number=measure_number,
                beat=beat,
                event_type=event_type,
                event_value=event_value
            )
            events.append(event)
    
    result =  Events(events=events, measure_number=measure_number)
    return result



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
    context = {}
    for child in tree.children:
        if isinstance(child, Token):
            pass
        elif child.data == 'line':
            for subchild in child.children:
                if subchild.data == "metadata_line":
                    lines.append(transform_metadata_line(subchild))
                elif subchild.data == "statement_line":
                    result = transform_statement_line(subchild, context)
                    if result is not None:
                        lines.append(result)

    document = RomanTextDocument(lines=lines)
    return document 