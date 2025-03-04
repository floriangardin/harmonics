"""
Code copied from : https://github.com/napulen/romanyh
with BSD 3-Clause "New" or "Revised" License
Copyright (c) 2020 Néstor Nápoles López (from commit 1cfe02c)
Copyright (c) 2020 Eric Zhang (until commit d4bd33b)
"""

from enum import IntEnum


class PartEnum(IntEnum):
    SOPRANO = 3
    ALTO = 2
    TENOR = 1
    BASS = 0


class IntervalV(IntEnum):
    ALTO_SOPRANO = 5
    TENOR_SOPRANO = 4
    TENOR_ALTO = 3
    BASS_SOPRANO = 2
    BASS_ALTO = 1
    BASS_TENOR = 0


class Cost(IntEnum):
    FORBIDDEN = 64
    VERYBAD = 8
    BAD = 4
    MAYBEBAD = 2
    NOTIDEAL = 1


class Rule(IntEnum):
    # Progression-Related Rules
    IDENTICAL_VOICING = 1
    ALLVOICES_SAME_DIRECTION = 2
    MELODIC_INTERVAL_FORBIDDEN = 3
    MELODIC_INTERVAL_BEYONDOCTAVE = 4
    MELODIC_INTERVAL_BEYONDFIFTH = 5
    MELODIC_INTERVAL_BEYONDTHIRD = 6
    MELODIC_INTERVAL_BEYONDSECOND = 7
    UNISON_BY_LEAP = 8
    PARALLEL_FIFTH = 9
    PARALLEL_OCTAVE = 10
    HIDDEN_FIFTH = 11
    HIDDEN_OCTAVE = 12
    VOICE_CROSSING = 13
    SEVENTH_UNPREPARED = 14
    SEVENTH_UNRESOLVED = 15
    LEADINGTONE_UNRESOLVED = 16
    # Voicing-Related Rules
    VERTICAL_NOT_DOUBLINGROOT = 17
    VERTICAL_SEVENTH_MISSINGNOTE = 18
