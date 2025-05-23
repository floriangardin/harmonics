BASE_OCTAVE = 4

NB_BEATS_TIME_SIGNATURE = {
    (4, 4): 4,
    (3, 4): 3,
    (6, 8): 2,
    (2, 4): 2,
    (12, 8): 4,
    (5, 4): 5,
    (7, 8): 3.5,
    (9, 8): 3,
    (7, 4): 7,
    (3, 8): 1,
    (2, 2): 2,
    (6, 4): 6,
}

# 6/8 -> 2 beats notated and 3 quarter notes, in theory 6 units (6 eights) so one beat = 1.5 quarter notes

# Maps time signatures to how many quarter notes make up one beat
# For example: 6/8 has 2 beats but spans 6 eighth notes = 3 quarter notes, so one beat = 1.5 quarter notes
BEAT_TO_QUARTER_NOTES = {
    time_sig: (time_sig[0] / time_sig[1] * 4) / NB_BEATS_TIME_SIGNATURE[time_sig]
    for time_sig in NB_BEATS_TIME_SIGNATURE.keys()
}

DRUMS = "drums"
PIANO = "piano"
BRIGHT_PIANO = "bright_piano"
ELECTRIC_PIANO = "electric_piano"
HONKY_TONK = "honky_tonk"
ELECTRIC_PIANO_1 = "electric_piano_1"
ELECTRIC_PIANO_2 = "electric_piano_2"
HARPSICHORD = "harpsichord"
CLAVI = "clavi"
CELESTA = "celesta"
GLOCKENSPIEL = "glockenspiel"
MUSIC_BOX = "music_box"
VIBRAPHONE = "vibraphone"
MARIMBA = "marimba"
XYLOPHONE = "xylophone"
TUBULAR_BELLS = "tubular_bells"
DULCIMER = "dulcimer"
DRAWBAR_ORGAN = "drawbar_organ"
PERCUSSIVE_ORGAN = "percussive_organ"
ROCK_ORGAN = "rock_organ"
CHURCH_ORGAN = "church_organ"
REED_ORGAN = "reed_organ"
ACCORDION = "accordion"
HARMONICA = "harmonica"
TANGO_ACCORDION = "tango_accordion"
ACOUSTIC_GUITAR = "acoustic_guitar"
STEEL_GUITAR = "steel_guitar"
JAZZ_GUITAR = "jazz_guitar"
CLEAN_GUITAR = "clean_guitar"
MUTED_GUITAR = "muted_guitar"
OVERDRIVEN_GUITAR = "overdriven_guitar"
DISTORTION_GUITAR = "distortion_guitar"
HARMONIC_GUITAR = "harmonic_guitar"
ACOUSTIC_BASS = "acoustic_bass"
ELECTRIC_BASS_FINGER = "electric_bass_finger"
ELECTRIC_BASS_PICK = "electric_bass_pick"
FRETLESS_BASS = "fretless_bass"
SLAP_BASS_1 = "slap_bass_1"
SLAP_BASS_2 = "slap_bass_2"
SYNTH_BASS_1 = "synth_bass_1"
SYNTH_BASS_2 = "synth_bass_2"
VIOLIN = "violin"
VIOLA = "viola"
CELLO = "cello"
CONTRABASS = "contrabass"
TREMOLO_STRING = "tremolo_string"
PIZZICATO = "pizzicato"
HARP = "harp"
TIMPANI = "timpani"
STRING_ENSEMBLE_1 = "string_ensemble_1"
STRING_ENSEMBLE_2 = "string_ensemble_2"
SYNTH_STRING_1 = "synth_string_1"
SYNTH_STRING_2 = "synth_string_2"
CHOIR_AAHS = "choir_aahs"
CHOIR_OOHS = "choir_oohs"
SYNTH_CHOIR = "synth_choir"
ORCHESTRA_HIT = "orchestra_hit"
TRUMPET = "trumpet"
TROMBONE = "trombone"
TUBA = "tuba"
MUTED_TRUMPET = "muted_trumpet"
FRENCH_HORN = "french_horn"
BRASS_SECTION = "brass_section"
SYNTH_BRASS_1 = "synth_brass_1"
SYNTH_BRASS_2 = "synth_brass_2"
SOPRANO_SAX = "soprano_sax"
ALTO_SAX = "alto_sax"
TENOR_SAX = "tenor_sax"
BARITONE_SAX = "baritone_sax"
OBOE = "oboe"
ENGLISH_HORN = "english_horn"
BASSOON = "bassoon"
CLARINET = "clarinet"
PICCOLO = "piccolo"
FLUTE = "flute"
RECORDER = "recorder"
PAN_FLUTE = "pan_flute"
BLOWN_BOTTLE = "blown_bottle"
SHAKUHACHI = "shakuhachi"
WHISTLE = "whistle"
OCARINA = "ocarina"
SQUARE_LEAD = "square_lead"
SAWTOOTH_LEAD = "sawtooth_lead"
CALLIOPE_LEAD = "calliope_lead"
CHIFF_LEAD = "chiff_lead"
CHARANG_LEAD = "charang_lead"
VOICE_LEAD = "voice_lead"
FIFTHS_LEAD = "fifths_lead"
BASS_LEAD = "bass_lead"
PAD_NEW_AGE = "pad_new_age"
PAD_WARM = "pad_warm"
PAD_POLYSYNTH = "pad_polysynth"
PAD_CHOIR = "pad_choir"
PAD_BOWED = "pad_bowed"
PAD_METALLIC = "pad_metallic"
PAD_HALO = "pad_halo"
PAD_SWEEP = "pad_sweep"
FX_RAIN = "fx_rain"
FX_SOUNDTRACK = "fx_soundtrack"
FX_CRYSTAL = "fx_crystal"
FX_ATMOSPHERE = "fx_atmosphere"
FX_BRIGHTNESS = "fx_brightness"
FX_GLOBLINS = "fx_globlins"
FX_ECHOES = "fx_echoes"
FX_SCI_FI = "fx_sci_fi"
SITAR = "sitar"
BANJO = "banjo"
SHAMISEN = "shamisen"
KOTO = "koto"
KALIMBA = "kalimba"
BAGPIPE = "bagpipe"
FIDDLE = "fiddle"
SHANAI = "shanai"
TINKLE_BELL = "tinkle_bell"
AGOGO = "agogo"
STEEL_DRUMS = "steel_drums"
WOODBLOCK = "woodblock"
TAIKO_DRUM = "taiko_drum"
MELODIC_TOM = "melodic_tom"
SYNTH_DRUM = "synth_drum"
REVERSE_CYMBAL = "reverse_cymbal"
GUITAR_FRET_NOISE = "guitar_fret_noise"
BREATH_NOISE = "breath_noise"
SEASHORE = "seashore"
BIRD_TWEET = "bird_tweet"
TELEPHONE_RING = "telephone_ring"
HELICOPTER = "helicopter"
APPLAUSE = "applause"
GUNSHOT = "gunshot"

INSTRUMENTS_DICT_RAW = {
    "piano": 0,
    "bright_piano": 1,
    "electric_piano": 2,
    "honky_tonk": 3,
    "electric_piano_1": 4,
    "electric_piano_2": 5,
    "harpsichord": 6,
    "clavi": 7,
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "tubular_bells": 14,
    "dulcimer": 15,
    "drawbar_organ": 16,
    "percussive_organ": 17,
    "rock_organ": 18,
    "church_organ": 19,
    "reed_organ": 20,
    "accordion": 21,
    "harmonica": 22,
    "tango_accordion": 23,
    "acoustic_guitar": 24,
    "steel_guitar": 25,
    "jazz_guitar": 26,
    "clean_guitar": 27,
    "muted_guitar": 28,
    "overdriven_guitar": 29,
    "distortion_guitar": 30,
    "harmonic_guitar": 31,
    "acoustic_bass": 32,
    "electric_bass_finger": 33,
    "electric_bass_pick": 34,
    "fretless_bass": 35,
    "slap_bass_1": 36,
    "slap_bass_2": 37,
    "synth_bass_1": 38,
    "synth_bass_2": 39,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "tremolo_string": 44,
    "pizzicato": 45,
    "harp": 46,
    "timpani": 47,
    "string_ensemble_1": 48,
    "string_ensemble_2": 49,
    "synth_string_1": 50,
    "synth_string_2": 51,
    "choir_aahs": 52,
    "choir_oohs": 53,
    "synth_choir": 54,
    "orchestra_hit": 55,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "muted_trumpet": 59,
    "french_horn": 60,
    "brass_section": 61,
    "synth_brass_1": 62,
    "synth_brass_2": 63,
    "soprano_sax": 64,
    "alto_sax": 65,
    "tenor_sax": 66,
    "baritone_sax": 67,
    "oboe": 68,
    "english_horn": 69,
    "bassoon": 70,
    "clarinet": 71,
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "blown_bottle": 76,
    "shakuhachi": 77,
    "whistle": 78,
    "ocarina": 79,
    "square_lead": 80,
    "sawtooth_lead": 81,
    "calliope_lead": 82,
    "chiff_lead": 83,
    "charang_lead": 84,
    "voice_lead": 85,
    "fifths_lead": 86,
    "bass_lead": 87,
    "pad_new_age": 88,
    "pad_warm": 89,
    "pad_polysynth": 90,
    "pad_choir": 91,
    "pad_bowed": 92,
    "pad_metallic": 93,
    "pad_halo": 94,
    "pad_sweep": 95,
    "fx_rain": 96,
    "fx_soundtrack": 97,
    "fx_crystal": 98,
    "fx_atmosphere": 99,
    "fx_brightness": 100,
    "fx_globlins": 101,
    "fx_echoes": 102,
    "fx_sci_fi": 103,
    "sitar": 104,
    "banjo": 105,
    "shamisen": 106,
    "koto": 107,
    "kalimba": 108,
    "bagpipe": 109,
    "fiddle": 110,
    "shanai": 111,
    "tinkle_bell": 112,
    "agogo": 113,
    "steel_drums": 114,
    "woodblock": 115,
    "taiko_drum": 116,
    "melodic_tom": 117,
    "synth_drum": 118,
    "reverse_cymbal": 119,
    "guitar_fret_noise": 120,
    "breath_noise": 121,
    "seashore": 122,
    "bird_tweet": 123,
    "telephone_ring": 124,
    "helicopter": 125,
    "applause": 126,
    "gunshot": 127,
}

INSTRUMENTS_DICT = {
    key: (val, 0) for key, val in INSTRUMENTS_DICT_RAW.items()  # instrument, is_drum
}
INSTRUMENTS_DICT["drums_0"] = (0, 1)
INSTRUMENTS_DICT["drums"] = (0, 1)
INSTRUMENTS_DICT["pizzicato_strings"] = (45, 0)
INSTRUMENTS_DICT["acoustic_piano"] = (0, 0)
INSTRUMENTS_DICT["grand_piano"] = (0, 0)
INSTRUMENTS_DICT["string_ensemble"] = (48, 0)
INSTRUMENTS_DICT["synth_strings"] = (51, 0)
INSTRUMENTS_DICT["synth_brass"] = (62, 0)
INSTRUMENTS_DICT["choir"] = (52, 0)
INSTRUMENTS_DICT["singer"] = (52, 0)
INSTRUMENTS_DICT["voice"] = (52, 0)
INSTRUMENTS_DICT["tenor"] = (52, 0)
INSTRUMENTS_DICT["soprano"] = (52, 0)
INSTRUMENTS_DICT["baritone"] = (52, 0)
INSTRUMENTS_DICT["violins"] = (40, 0)
INSTRUMENTS_DICT["violas"] = (41, 0)
INSTRUMENTS_DICT["cellos"] = (42, 0)
INSTRUMENTS_DICT["contrabasses"] = (43, 0)
INSTRUMENTS_DICT["violoncello"] = (42, 0)
INSTRUMENTS_DICT["alto"] = (41, 0)
INSTRUMENTS_DICT["altos"] = (41, 0)
INSTRUMENTS_DICT["double_bass"] = (43, 0)
INSTRUMENTS_DICT["violin_1"] = (40, 0)
INSTRUMENTS_DICT["violin_2"] = (40, 0)
INSTRUMENTS_DICT["choir_tenor"] = (52, 0)
INSTRUMENTS_DICT["choir_bass"] = (53, 0)
INSTRUMENTS_DICT["choir_soprano"] = (52, 0)
INSTRUMENTS_DICT["choir_alto"] = (53, 0)
INSTRUMENTS_DICT["pipe_organ"] = (19, 0)
INSTRUMENTS_DICT["organ"] = (19, 0)
INSTRUMENTS_DICT["church_organ"] = (19, 0)

REVERSE_INSTRUMENT_DICT = {val: key for key, val in INSTRUMENTS_DICT.items()}

# Add plurals to instrument_dict
for key, val in list(INSTRUMENTS_DICT.items()):
    INSTRUMENTS_DICT[key + "s"] = val

API_URL_VARIABLE = "API_URL"
MUSICLANG_API_KEY_VARIABLE = "MUSICLANG_API_KEY"


ALL_INSTRUMENTS = [
    DRUMS,
    PIANO,
    BRIGHT_PIANO,
    ELECTRIC_PIANO,
    HONKY_TONK,
    ELECTRIC_PIANO_1,
    ELECTRIC_PIANO_2,
    HARPSICHORD,
    CLAVI,
    CELESTA,
    GLOCKENSPIEL,
    MUSIC_BOX,
    VIBRAPHONE,
    MARIMBA,
    XYLOPHONE,
    TUBULAR_BELLS,
    DULCIMER,
    DRAWBAR_ORGAN,
    PERCUSSIVE_ORGAN,
    ROCK_ORGAN,
    CHURCH_ORGAN,
    REED_ORGAN,
    ACCORDION,
    HARMONICA,
    TANGO_ACCORDION,
    ACOUSTIC_GUITAR,
    STEEL_GUITAR,
    JAZZ_GUITAR,
    CLEAN_GUITAR,
    MUTED_GUITAR,
    OVERDRIVEN_GUITAR,
    DISTORTION_GUITAR,
    HARMONIC_GUITAR,
    ACOUSTIC_BASS,
    ELECTRIC_BASS_FINGER,
    ELECTRIC_BASS_PICK,
    FRETLESS_BASS,
    SLAP_BASS_1,
    SLAP_BASS_2,
    SYNTH_BASS_1,
    SYNTH_BASS_2,
    VIOLIN,
    VIOLA,
    CELLO,
    CONTRABASS,
    TREMOLO_STRING,
    PIZZICATO,
    HARP,
    TIMPANI,
    STRING_ENSEMBLE_1,
    STRING_ENSEMBLE_2,
    SYNTH_STRING_1,
    SYNTH_STRING_2,
    CHOIR_AAHS,
    CHOIR_OOHS,
    SYNTH_CHOIR,
    ORCHESTRA_HIT,
    TRUMPET,
    TROMBONE,
    TUBA,
    MUTED_TRUMPET,
    FRENCH_HORN,
    BRASS_SECTION,
    SYNTH_BRASS_1,
    SYNTH_BRASS_2,
    SOPRANO_SAX,
    ALTO_SAX,
    TENOR_SAX,
    BARITONE_SAX,
    OBOE,
    ENGLISH_HORN,
    BASSOON,
    CLARINET,
    PICCOLO,
    FLUTE,
    RECORDER,
    PAN_FLUTE,
    BLOWN_BOTTLE,
    SHAKUHACHI,
    WHISTLE,
    OCARINA,
    SQUARE_LEAD,
    SAWTOOTH_LEAD,
    CALLIOPE_LEAD,
    CHIFF_LEAD,
    CHARANG_LEAD,
    VOICE_LEAD,
    FIFTHS_LEAD,
    BASS_LEAD,
    PAD_NEW_AGE,
    PAD_WARM,
    PAD_POLYSYNTH,
    PAD_CHOIR,
    PAD_BOWED,
    PAD_METALLIC,
    PAD_HALO,
    PAD_SWEEP,
    FX_RAIN,
    FX_SOUNDTRACK,
    FX_CRYSTAL,
    FX_ATMOSPHERE,
    FX_BRIGHTNESS,
    FX_GLOBLINS,
    FX_ECHOES,
    FX_SCI_FI,
    SITAR,
    BANJO,
    SHAMISEN,
    KOTO,
    KALIMBA,
    BAGPIPE,
    FIDDLE,
    SHANAI,
    TINKLE_BELL,
    AGOGO,
    STEEL_DRUMS,
    WOODBLOCK,
    TAIKO_DRUM,
    MELODIC_TOM,
    SYNTH_DRUM,
    REVERSE_CYMBAL,
    GUITAR_FRET_NOISE,
    BREATH_NOISE,
    SEASHORE,
    BIRD_TWEET,
    TELEPHONE_RING,
    HELICOPTER,
    APPLAUSE,
    GUNSHOT,
]


TECHNIQUE_DICT = {
    ".": ["staccato"],
    "!": ["staccatissimo"],
    "-": ["tenuto"],
    "^": ["marcato"],
    ">": ["accent"],
    "tr": ["trill"],
    "~": ["turn"],
    "i~": ["inverted_turn"],
    "/~": ["mordent"],
    "i/~": ["inverted_mordent"],
}

POST_TECHNIQUE_DICT = {}
for k, v in TECHNIQUE_DICT.items():
    for tech in v:
        POST_TECHNIQUE_DICT[tech] = k

END_PLAYING_STYLE_DICT = {
}
# Pre technique dict
PRE_TECHNIQUE_DICT = {
    "!legato": "_",
    "!slur": "_",
    "!pedal.": "*",
    "!ped": "*",
    "!pedal.": "*",
    "!pedal": "*",
    "!ped": "*",
}
