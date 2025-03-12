# Note event is a list of [time, pitch, duration, program, velocity, list of techniques]


def get_staccato(note_event):
    note_event[2] = min(note_event[2], 0.25)
    return note_event


def get_staccatissimo(note_event):
    note_event[2] = min(note_event[2], 0.125)
    return note_event


def get_marcato(note_event):
    note_event[2] = min(note_event[2], 0.33)
    return note_event


def get_pizzicato(note_event):
    note_event[4] = int(min(note_event[4] * 1.5, 127))
    return note_event


def get_accent(note_event):
    note_event[4] = int(min(note_event[4] * 1.5, 127))
    return note_event


def get_legato(note_event):
    return note_event


BEFORE_TECHNIQUE_MAP = {
    "staccato": get_staccato,
    "legato": get_legato,
    "marcato": get_marcato,
    "pizzicato": get_pizzicato,
    "staccatissimo": get_staccatissimo,
}

AFTER_TECHNIQUE_MAP = {
    "accent": get_accent,
}

GROUPS = {
    "articulation": [
        "staccato",
        "staccatissimo",
        "marcato",
        "pizzicato",
        "legato",
        "tenuto",
    ],
    "accents": ["accent", "ghost_note"],
    "dynamics": ["pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"],
    "note_effects": [
        "mordent",
        "upper_mordent" "appoggiatura",
        "trill",
        "acciaccatura",
        "turn",
        "grace_note",
        "arpeggio",
        "glissando",
        "slide",
        "vibrato",
        "tremolo",
    ],
}
# Create a reverse mapping from technique to group
TECHNIQUE_GROUPS = {}
for group_name, techniques in GROUPS.items():
    for technique in techniques:
        TECHNIQUE_GROUPS[technique] = group_name


def resolve_techniques(techniques):
    """
    If several techniques of the same group are provided, only use the last one.
    """
    resolved_techniques = []
    # Group techniques by their group
    grouped_techniques = {}

    # First, collect all techniques by their group
    for technique in techniques:
        if technique in TECHNIQUE_GROUPS:
            group = TECHNIQUE_GROUPS[technique]
            # For each group, keep only the last technique
            grouped_techniques[group] = technique
        else:
            # If technique doesn't belong to a group, always include it
            resolved_techniques.append(technique)

    # Add the last technique from each group to the resolved list
    for group, technique in grouped_techniques.items():
        resolved_techniques.append(technique)

    return resolved_techniques


def apply_techniques_before(techniques, note_event):
    tech = list(techniques)
    techniques = resolve_techniques(techniques)
    for technique in techniques:
        if technique in BEFORE_TECHNIQUE_MAP:
            note_event = BEFORE_TECHNIQUE_MAP[technique](note_event)
    return note_event


def apply_techniques_after(techniques, note_event):
    techniques = resolve_techniques(techniques)
    for technique in techniques:
        if technique in AFTER_TECHNIQUE_MAP:
            note_event = AFTER_TECHNIQUE_MAP[technique](note_event)
    return note_event
