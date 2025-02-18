
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
    (6, 4): 6
}   

# 6/8 -> 2 beats notated and 3 quarter notes, in theory 6 units (6 eights) so one beat = 1.5 quarter notes

# Maps time signatures to how many quarter notes make up one beat
# For example: 6/8 has 2 beats but spans 6 eighth notes = 3 quarter notes, so one beat = 1.5 quarter notes
BEAT_TO_QUARTER_NOTES = {
    time_sig: (time_sig[0] / time_sig[1] * 4) / NB_BEATS_TIME_SIGNATURE[time_sig]
    for time_sig in NB_BEATS_TIME_SIGNATURE.keys()
}
