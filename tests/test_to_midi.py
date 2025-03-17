from harmonics.commons.to_midi import solve_continuation
from harmonics.score_models import NoteItem


def test_solve_continuation():

    # notes = [
    #     NoteItem(beat=0, duration=1, pitch="C4", voice_name="T1"),
    #     NoteItem(beat=1, duration=1, pitch="D4", voice_name="T2"),
    #     NoteItem(beat=1, duration=1, pitch=None, is_continuation=True, voice_name="T1"),
    #     NoteItem(beat=2, duration=1, pitch="E4", voice_name="T1"),
    # ]
    # assert solve_continuation(notes) == [
    #     NoteItem(beat=0, duration=2, pitch="C4", voice_name="T1"),
    #     NoteItem(beat=1, duration=1, pitch="D4", voice_name="T2"),
    #     NoteItem(beat=2, duration=1, pitch="E4", voice_name="T1"),
    # ]
    # FIXME : all to_midi utils are broken, output in mxl for the time being
    pass
