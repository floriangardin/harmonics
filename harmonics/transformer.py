from typing import List, Optional, Union, Dict, Tuple, Any
from lark import Tree, Token
from harmonics.constants import INSTRUMENTS_DICT

from harmonics.models import (
    Composer,
    Title,
    Analyst,
    Proofreader,
    Movement,
    TimeSignature,
    KeySignature,
    MinorMode,
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
    Melody,
    MelodyNote,
    ChordMelodyNote,
    AccompanimentBeat,
    Tempo,
    Events,
    Event,
    Instrument,
    Instruments,
    AccompanimentVoice,
    Technique,
    TechniqueRange,
    Continuation,
    ClefType,
    Clef,
    ClefChange,
    KeySignature,
    TextComment,
    StaffGroup,
)
from .score import ScoreDocument


def transform_token(token: Token) -> str:
    return token.value


# ------------------------------
# Metadata lines transformers
# ------------------------------


def transform_key_signature_line(node: Tree) -> KeySignature:
    # key_signature_line: ( "(" WS*  "m" MEASURE_NUMBER WS* ")" WS*)? "Signature:" WS+ key_signature NEWLINE
    measure_number = None
    key_signature = ""

    for child in node.children:
        if isinstance(child, Tree) and child.data == "key_signature":
            key_signature = "".join(
                [transform_token(token) for token in child.children]
            )
        elif isinstance(child, Token) and child.type == "MEASURE_NUMBER":
            measure_number = int(transform_token(child))
    return KeySignature(key_signature=key_signature, measure_number=measure_number)


def transform_composer_line(node: Tree) -> Composer:
    # composer_line: "Composer:" WS REST_LINE NEWLINE
    value = ""
    for token in node.children:
        if isinstance(token, Token) and token.type == "REST_LINE":
            value = transform_token(token).strip()
            break
    return Composer(composer=value)


def transform_title_line(node: Tree) -> Title:
    # title_line: "Piece:" WS REST_LINE NEWLINE
    value = ""
    for token in node.children:
        if isinstance(token, Token) and token.type == "REST_LINE":
            value = transform_token(token).strip()
            break
    return Title(title=value)


def transform_analyst_line(node: Tree) -> Analyst:
    # analyst_line: "Analyst:" WS REST_LINE NEWLINE
    value = ""
    for token in node.children:
        if isinstance(token, Token) and token.type == "REST_LINE":
            value = transform_token(token).strip()
            break
    return Analyst(analyst=value)


def transform_proofreader_line(node: Tree) -> Proofreader:
    # proofreader_line: "Proofreader:" WS REST_LINE NEWLINE
    value = ""
    for token in node.children:
        if isinstance(token, Token) and token.type == "REST_LINE":
            value = transform_token(token).strip()
            break
    return Proofreader(proofreader=value)


def transform_movement_line(node: Tree) -> Movement:
    # movement_line: "Movement:" WS MEASURE_NUMBER NEWLINE
    for token in node.children:
        if isinstance(token, Token) and token.type == "MEASURE_NUMBER":
            return Movement(movement=transform_token(token))
    return Movement(movement="")


def transform_time_signature_line(node: Tree) -> TimeSignature:
    # time_signature_line: ( "(" WS*  "m" MEASURE_NUMBER WS* ")" WS*)? "Time Signature" WS* ":" WS* time_signature NEWLINE
    numerator = 4
    denominator = 4
    measure_number = None

    for token in node.children:
        if isinstance(token, Token) and token.type == "MEASURE_NUMBER":
            measure_number = int(token.value)
        elif isinstance(token, Tree) and token.data == "time_signature":
            for subchild in token.children:
                if isinstance(subchild, Tree) and subchild.data == "numerator":
                    digits = ""
                    for subsubchild in subchild.children:
                        if (
                            isinstance(subsubchild, Token)
                            and subsubchild.type == "DIGIT"
                        ):
                            digits += subsubchild.value
                    numerator = int(digits)
                elif isinstance(subchild, Tree) and subchild.data == "denominator":
                    digits = ""
                    for subsubchild in subchild.children:
                        if (
                            isinstance(subsubchild, Token)
                            and subsubchild.type == "DIGIT"
                        ):
                            digits += subsubchild.value
                    denominator = int(digits)
    return TimeSignature(
        numerator=numerator, denominator=denominator, measure_number=measure_number
    )


def transform_minor_mode_line(node: Tree) -> MinorMode:
    # minor_mode_line: "Minor Sixth / Minor Seventh:" WS MINOR_MODE_OPTION NEWLINE
    for token in node.children:
        if isinstance(token, Token) and token.type == "MINOR_MODE_OPTION":
            return MinorMode(minor_mode=transform_token(token))
    return MinorMode(minor_mode="")


def transform_groups_line(node: Tree) -> StaffGroup:
    group_name = ""
    track_names = []
    for child in node.children:
        if isinstance(child, Token) and child.type == "GROUP_NAME":
            group_name = transform_token(child)
        elif isinstance(child, Token) and child.type == "TRACK_NAME":
            track_names.append(transform_token(child))
    return StaffGroup(group_name=group_name, track_names=track_names)


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
                if (
                    isinstance(subchild, Token)
                    and subchild.type == "INVERSION_STANDARD"
                ):
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
            if special in ["r", "R"]:
                special = "NC"
        elif isinstance(child, Tree) and child.data == "inversion":
            for subchild in child.children:
                if (
                    isinstance(subchild, Token)
                    and subchild.type == "INVERSION_STANDARD"
                ):
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


def transform_measure_line_content(
    node: Tree, context: Dict[str, List[AccompanimentBeat]]
) -> List[BeatItem]:
    beat_items = []
    for subchild in node.children:
        if isinstance(subchild, Token) and subchild.type == "VARIABLE_CALLING":
            variable_name = subchild.value[1:]
            beat_items = context[variable_name]
        elif subchild.data == "chord_beat_1":
            beat_items.append(transform_beat_chord(subchild))
        elif subchild.data == "beat_chord":
            beat_items.append(transform_beat_chord(subchild))
        elif subchild.data == "key_change":
            beat_items.append(transform_key_change(subchild))
        elif subchild.data == "PHRASE_BOUNDARY":
            # For simplicity we join the token children
            phrase_boundary = "".join(
                transform_token(c) for c in subchild.children if isinstance(c, Token)
            )
    return beat_items


def transform_measure_line(
    node: Tree, context: Dict[str, List[AccompanimentBeat]]
) -> Measure:
    # measure_line: MEASURE_INDICATOR (chord_beat_1)? (beat_chord | key_change)+ PHRASE_BOUNDARY? NEWLINE
    measure_number = 0
    beat_items: List[BeatItem] = []
    phrase_boundary = None
    for child in node.children:
        if isinstance(child, Token) and child.type == "MEASURE_INDICATOR":
            measure_number = int(child.value[1:])
        elif isinstance(child, Token) and child.type == "VARIABLE_CALLING":
            variable_name = child.value[1:]
            beat_items = context[variable_name]
        elif isinstance(child, Tree) and child.data == "measure_line_content":
            beat_items = transform_measure_line_content(child, context)
    return Measure(
        measure_number=measure_number,
        beat_items=beat_items,
        phrase_boundary=phrase_boundary,
        line_number=context["line_number"],
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
    return PedalEntry(
        measure_indicator=measure_indicator, beat_indicator=beat_indicator
    )


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


def transform_absolute_note(
    node: Tree, beat: float, is_exact: bool
) -> AbsoluteMelodyNote:
    from harmonics.constants import TECHNIQUE_DICT, END_PLAYING_STYLE_DICT

    noteletter = ""
    accidental = ""
    absolute_octave = None
    techniques = []
    for child in node.children:
        if isinstance(child, Token) and child.type == "NOTELETTER_CAPITALIZED":
            noteletter = transform_token(child)
        elif isinstance(child, Token) and child.type == "ACCIDENTAL":
            accidental = transform_token(child)
        elif isinstance(child, Token) and child.type == "ABSOLUTE_OCTAVE":
            absolute_octave = transform_token(child)
        elif isinstance(child, Token) and child.type == "PLAYING_STYLE":
            techniques.append(TECHNIQUE_DICT[transform_token(child)][0])
        elif isinstance(child, Token) and child.type == "END_PLAYING_STYLE":
            techniques.append(END_PLAYING_STYLE_DICT[transform_token(child)])

    return AbsoluteMelodyNote(
        note=noteletter + accidental + absolute_octave,
        beat=beat,
        techniques=techniques,
        is_exact=is_exact,
    )


def transform_beat_note(node: Tree, notes: List[MelodyNote]) -> BeatItem:
    beat = 1
    all_notes = []
    techniques = []
    text_comment = None
    is_exact = False
    from fractions import Fraction

    for token in node.children:
        if isinstance(token, Token):
            if token.type == "BEAT_INDICATOR":
                if "+" in token.value:
                    integer_part, fractional_part = token.value[1:].split("+")
                    integer_part = int(integer_part)
                    num, den = fractional_part.split("/")
                    beat = integer_part + Fraction(int(num), int(den))
                    is_exact = True
                elif "." not in token.value:
                    beat = int(token.value[1:])
                    is_exact = True
                elif Fraction(token.value[1:]).denominator in [2, 3, 4, 5, 6, 8, 10]:
                    beat = Fraction(token.value[1:]).limit_denominator(10)
                    is_exact = True
                elif token.value[1:].split(".")[-1] in ["33", "66", "67"]:
                    beat = Fraction(token.value[1:]).limit_denominator(3)
                    is_exact = True
                else:
                    from harmonics.commons.utils_beat import to_beat_fraction

                    beat = to_beat_fraction(float(token.value[1:]), is_exact)
            elif token.type == "TEXT_COMMENT":
                text_comment = token.value[1:-1]
            elif token.type == "SILENCE":
                return [
                    Silence(beat=beat, text_comment=text_comment, is_exact=is_exact)
                ]
            elif token.type == "CONTINUATION":
                return [
                    Continuation(
                        beat=beat, text_comment=text_comment, is_exact=is_exact
                    )
                ]
        elif isinstance(token, Tree) and token.data == "absolute_note":
            note = transform_absolute_note(token, beat, is_exact)
            all_notes.append(note)
        elif isinstance(token, Tree) and token.data == "note_techniques":
            techniques += transform_note_techniques(token)

    if text_comment is not None:
        for note in all_notes:
            note.text_comment = text_comment

    if len(all_notes) == 1:
        all_notes[0].techniques += techniques
        return all_notes
    else:
        for note in all_notes:
            techniques += note.techniques
        return [
            ChordMelodyNote(
                beat=beat,
                notes=all_notes,
                techniques=techniques,
                text_comment=text_comment,
                is_exact=is_exact,
            )
        ]


def transform_note_techniques(node: Tree) -> List[Technique]:
    techniques = []
    for child in node.children:
        if isinstance(child, Token) and child.type == "TECHNIQUE_NAME":
            techniques.append(child.value)
    return techniques


def transform_melody_line_content(
    node: Tree, context: Dict[str, List[AccompanimentBeat]]
) -> List[BeatItem]:
    notes = []
    for child in node.children:
        if isinstance(child, Tree) and child.data in ["beat_note", "first_beat_note"]:
            result = transform_beat_note(child, notes)
            notes.extend(result)
    return notes


def transform_melody_line(
    node: Tree, context: Dict[str, List[AccompanimentBeat]]
) -> Union[Melody, ClefChange]:
    # melody_line: MEASURE_INDICATOR (WS+ TRACK_NAME)? (beat_note)* NEWLINE
    measure_number = 0
    track_name = "T1"  # Default voice
    voice_name = "v1"  # Default voice

    notes = []
    variable_calling = None

    for child in node.children:
        if isinstance(child, Token):
            if child.type == "MEASURE_INDICATOR":
                measure_number = int(child.value[1:])
            elif child.type == "TRACK_NAME":
                track_name = transform_token(child)
            elif child.type == "VOICE_NAME":
                voice_name = transform_token(child)
            elif child.type == "VARIABLE_CALLING":
                variable_calling = transform_token(child)[1:]  # Remove @ prefix
                if variable_calling in context:
                    return Melody(
                        measure_number=measure_number,
                        voice_name=voice_name,
                        notes=context[variable_calling],
                    )
                else:
                    raise Exception(
                        f"Variable {variable_calling} not found in context when called in measure {measure_number}"
                    )
        elif isinstance(child, Tree):
            for beat_note_result in transform_melody_line_content(child, context):
                notes.append(beat_note_result)

    return Melody(
        measure_number=measure_number,
        track_name=track_name,
        voice_name=voice_name,
        notes=notes,
    )


# ------------------------------
# Statement line transformer
# ------------------------------


def transform_tempo_line(node: Tree) -> Tempo:
    # tempo_line: "Tempo:" WS TEMPO_NUMBER NEWLINE
    tempo = 120  # Default tempo
    for token in node.children:
        if isinstance(token, Token) and token.type == "TEMPO_NUMBER":
            tempo = int(token.value)
    return Tempo(tempo=tempo)


def transform_instrument_line(node: Tree) -> Instruments:
    # instrument_line: "Instrument:" WS TRACK_NAME WS* "=" WS* GM_INSTRUMENT_NAME NEWLINE
    instruments = []
    track_name = ""
    gm_instrument_name = ""
    for child in node.children:
        if isinstance(child, Token) and child.type == "TRACK_NAME":
            track_name = transform_token(child)
        elif isinstance(child, Token) and child.type == "GM_INSTRUMENT_NAME":
            gm_instrument_name = transform_token(child)
            instruments.append(
                Instrument(
                    track_name=track_name,
                    gm_number=INSTRUMENTS_DICT[gm_instrument_name][0] + 1,
                    name=gm_instrument_name,
                )
            )
    return Instruments(instruments=instruments)


def transform_variable_declaration_line(
    node: Tree, context: Dict[str, List[AccompanimentBeat]]
) -> Dict[str, List[AccompanimentBeat]]:
    # variable_declaration_line: VARIABLE_NAME WS* "=" WS* VARIABLE_VALUE NEWLINE
    variable_name = ""
    variable_value = ""
    beats = []

    for child in node.children:
        if isinstance(child, Token):
            if child.type == "VARIABLE_NAME":
                variable_name = transform_token(child)
            elif child.type == "TRACK_NAME":
                voice_name = transform_token(child)
                context["voice_name"] = voice_name
        elif isinstance(child, Tree) and child.data == "variable_content":
            for subchild in child.children:
                if (
                    isinstance(subchild, Tree)
                    and subchild.data == "accompaniment_line_content"
                ):
                    beats += transform_accompaniment_line_content(subchild, context)
                elif (
                    isinstance(subchild, Tree)
                    and subchild.data == "melody_line_content"
                ):
                    beats += transform_melody_line_content(subchild, context)
                elif (
                    isinstance(subchild, Tree)
                    and subchild.data == "measure_line_content"
                ):
                    beats += transform_measure_line_content(subchild, context)
    context[variable_name] = beats
    return None


def transform_voice_list_for_technique(node: Tree) -> List[str]:
    # voice_list_for_technique: "[" TRACK_NAME ("," TRACK_NAME)* "]"
    voice_names = []
    for child in node.children:
        if child.type == "TRACK_NAME":
            voice_names.append(transform_token(child))
    return voice_names


def transform_single_voice_for_technique(node: Tree) -> List[str]:
    # single_voice_for_technique: TRACK_NAME
    return [transform_token(node.children[0])]


def transform_measure_range_with_beats(node: Tree) -> TechniqueRange:
    # measure_range_with_beats: "(" MEASURE_INDICATOR WS BEAT_INDICATOR WS "-" WS MEASURE_INDICATOR WS BEAT_INDICATOR ")"

    filtered_tokens = [token for token in node.children if token.type != "WS"]
    start_measure_indicator = filtered_tokens[0]
    start_beat_indicator = filtered_tokens[1]
    end_measure_indicator = filtered_tokens[2]
    end_beat_indicator = filtered_tokens[3]

    # Extract measure numbers
    start_measure_str = transform_token(start_measure_indicator).lstrip("m")
    end_measure_str = transform_token(end_measure_indicator).lstrip("m")

    # Extract beat numbers
    start_beat_str = transform_token(start_beat_indicator).lstrip("b")
    end_beat_str = transform_token(end_beat_indicator).lstrip("b")

    return TechniqueRange(
        start_measure=int(start_measure_str),
        start_beat=float(start_beat_str),
        end_measure=int(end_measure_str),
        end_beat=float(end_beat_str),
    )


def transform_technique_list(node: Tree) -> List[str]:
    # technique_list: TECHNIQUE_NAME ("," TECHNIQUE_NAME)*
    techniques = []
    for child in node.children:
        if child.type == "TECHNIQUE_NAME":
            techniques.append(transform_token(child))
    return techniques


def transform_technique_line(node: Tree) -> Technique:
    # technique_line: "tech" WS (voice_list_for_technique | single_voice_for_technique) WS measure_range_with_beats WS ":" WS technique_list NEWLINE
    voice_list_node = None
    single_voice_node = None
    measure_range_node = None
    technique_list_node = None

    for child in node.children:
        if isinstance(child, Tree):
            if child.data == "voice_list_for_technique":
                voice_list_node = child
            elif child.data == "single_voice_for_technique":
                single_voice_node = child
            elif child.data == "measure_range_with_beats":
                measure_range_node = child
            elif child.data == "technique_list":
                technique_list_node = child

    if voice_list_node:
        track_names = transform_voice_list_for_technique(voice_list_node)
    else:
        track_names = transform_single_voice_for_technique(single_voice_node)

    technique_range = transform_measure_range_with_beats(measure_range_node)
    techniques = transform_technique_list(technique_list_node)

    return Technique(
        track_names=track_names, technique_range=technique_range, techniques=techniques
    )


def transform_statement_line(
    node: Tree, context: Dict[str, List[AccompanimentBeat]]
) -> Line:
    # statement_line: measure_line | pedal_line | form_line | note_line | repeat_line | melody_line | accompaniment_line
    child = node
    line = child.meta.line
    context["line_number"] = line
    if child.data == "measure_line":
        return transform_measure_line(child, context)
    elif child.data == "pedal_line":
        return transform_pedal_line(child)
    elif child.data == "form_line":
        return transform_form_line(child)
    elif child.data == "note_line":
        return transform_note_line(child)
    elif child.data == "repeat_line":
        return transform_repeat_line(child)
    elif child.data == "melody_line":
        return transform_melody_line(child, context)
    elif child.data == "event_line":
        return transform_event_line(child)
    elif child.data == "variable_declaration_line":
        return transform_variable_declaration_line(child, context)
    elif child.data == "technique_line":
        return transform_technique_line(child)
    elif child.data == "clef_change_line":
        return transform_clef_change_line(child)
    elif child.data == "key_signature_line":
        return transform_key_signature_line(child)
    elif child.data == "composer_line":
        return transform_composer_line(child)
    elif child.data == "title_line":
        return transform_title_line(child)
    elif child.data == "analyst_line":
        return transform_analyst_line(child)
    elif child.data == "proofreader_line":
        return transform_proofreader_line(child)
    elif child.data == "movement_line":
        return transform_movement_line(child)
    elif child.data == "time_signature_line":
        return transform_time_signature_line(child)
    elif child.data == "minor_mode_line":
        return transform_minor_mode_line(child)
    elif child.data == "tempo_line":
        return transform_tempo_line(child)
    elif child.data == "instrument_line":
        return transform_instrument_line(child)
    elif child.data == "clef_line":
        return transform_clef_line(child)
    elif child.data == "groups_line":
        return transform_groups_line(child)
    else:
        raise ValueError(f"Unknown line type: {child.data}")


# ------------------------------
# New Function to Populate Properties
# ------------------------------


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
                event_value=event_value,
            )
            events.append(event)

    result = Events(events=events, measure_number=measure_number)
    return result


def parse_key_signature(key_signature: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parses the key signature string to extract mode and tonality.
    This is a placeholder and should be adjusted based on actual key encoding.
    """
    # Example implementation:
    # Assuming key_signature is in the format "C:maj" or "Am"
    if ":" in key_signature:
        tonality, mode = key_signature.split(":", 1)
    elif key_signature.endswith("m"):
        tonality = key_signature[:-1]
        mode = "minor"
    else:
        tonality = key_signature
        mode = "major"
    return mode, tonality


def transform_clef_line(node: Tree) -> Clef:
    # clef_line: ( "(" WS*  "m" MEASURE_NUMBER WS* ")" WS*)? "Clef:" WS+ TRACK_NAME WS* "=" WS* clef_type NEWLINE
    measure_number = None
    voice_name = ""
    clef_name = ""
    octave_change = None

    for child in node.children:
        if isinstance(child, Token):
            if child.type == "MEASURE_NUMBER":
                measure_number = int(child.value)
            elif child.type == "TRACK_NAME":
                track_name = transform_token(child)
        elif isinstance(child, Tree) and child.data == "clef_type":
            clef_type = transform_clef_type(child)
            clef_name = clef_type.name
            octave_change = clef_type.octave_change

    return Clef(
        track_name=track_name,
        clef_type=ClefType(name=clef_name, octave_change=octave_change),
        measure_number=measure_number,
    )


def transform_clef_type(node: Tree) -> ClefType:
    # clef_type: CLEF_NAME (WS+ CLEF_OCTAVE_CHANGE)?
    clef_name = ""
    octave_change = None

    for child in node.children:
        if isinstance(child, Token):
            if child.type == "CLEF_NAME":
                clef_name = transform_token(child)
            elif child.type == "CLEF_OCTAVE_CHANGE":
                value = transform_token(child)
                # Parse +1, -1, etc.
                if value.startswith("+"):
                    octave_change = int(value[1:])
                elif value.startswith("-"):
                    octave_change = -int(value[1:])
                else:
                    octave_change = int(value)

    return ClefType(name=clef_name, octave_change=octave_change)


def transform_clef_change_line(node: Tree) -> ClefChange:
    # clef_change_line: MEASURE_INDICATOR (WS+ TRACK_NAME)? WS+ BEAT_INDICATOR WS+ "clef" WS+ clef_type NEWLINE
    measure_number = 0
    voice_name = "T1"  # Default voice
    beat = 1.0
    clef_name = ""
    octave_change = None

    for child in node.children:
        if isinstance(child, Token):
            if child.type == "MEASURE_INDICATOR":
                measure_number = int(child.value[1:])
            elif child.type == "BEAT_INDICATOR":
                beat = float(child.value[1:])
            elif child.type == "TRACK_NAME":
                voice_name = transform_token(child)
        elif isinstance(child, Tree) and child.data == "clef_type":
            clef_type = transform_clef_type(child)
            clef_name = clef_type.name
            octave_change = clef_type.octave_change

    return ClefChange(
        measure_number=measure_number,
        beat=beat,
        voice_name=voice_name,
        clef_type=ClefType(name=clef_name, octave_change=octave_change),
    )


# ------------------------------
# Top-level document transformer
# ------------------------------


def transform_document(tree: Tree) -> ScoreDocument:
    lines = []
    context = {}
    for child in tree.children:
        if isinstance(child, Token):
            pass
        elif child.data == "line":
            subchild = child.children[0]
            result = transform_statement_line(subchild, context)
            if result is not None:
                lines.append(result)

    document = ScoreDocument(lines=lines)
    return document
