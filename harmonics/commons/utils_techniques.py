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


def apply_techniques_before(techniques, note_event):
    for technique in techniques:
        if technique in BEFORE_TECHNIQUE_MAP:
            note_event = BEFORE_TECHNIQUE_MAP[technique](note_event)
    return note_event


def apply_techniques_after(techniques, note_event):
    for technique in techniques:
        if technique in AFTER_TECHNIQUE_MAP:
            note_event = AFTER_TECHNIQUE_MAP[technique](note_event)
    return note_event
