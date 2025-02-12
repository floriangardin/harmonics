from symusic import Score, Track, Note, Tempo, TimeSignature
import music21 as m21
def events_to_midi(events, output_file, tempo=120, quarter_value=1.0):
    """
    Converts a list of events to a MIDI file using Symusic.

    Args:
        events (list): A list of events where each event is [time, pitch, duration, midi_program, velocity].
                       - time: int, in units where 'quarter_value' units = 1 quarter note.
                       - pitch: int, MIDI pitch number.
                       - duration: int, in units where 'quarter_value' units = 1 quarter note.
                       - midi_program: int, MIDI program number (1-128).
                       - velocity: int, velocity (0-127).
        output_file (str): Path to the output MIDI file.
    """

    # Initialize a Symusic Score object
    symusic_score = Score()
    target_tpq = 480
    symusic_score.tpq = target_tpq

    # Set default tempo and time signature
    default_tempo = tempo  # BPM
    default_time_signature = (4, 4)

    # Add default Time Signature
    sym_ts = TimeSignature(
        time=0,
        numerator=default_time_signature[0],
        denominator=default_time_signature[1]
    )
    symusic_score.time_signatures.append(sym_ts)

    # Add default Tempo
    sym_tempo = Tempo(
        time=0,
        qpm=default_tempo
    )
    symusic_score.tempos.append(sym_tempo)

    # Group events by MIDI program
    program_events = {}
    for event in events:
        time, pitch, duration, midi_program, velocity = event
        if midi_program not in program_events:
            program_events[midi_program] = []
        program_events[midi_program].append(event)

    # Create a track for each MIDI program
    for midi_program, prog_events in program_events.items():
        sym_track = Track(program=midi_program, is_drum=False)

        # Sort events by start time
        prog_events.sort(key=lambda x: x[0])
        for event in prog_events:
            time, pitch, duration, _, velocity = event

            # Convert time and duration from event units to ticks
            note_start_time = int((time / quarter_value) * target_tpq)
            note_duration = int((duration / quarter_value) * target_tpq)

            # Create a Symusic Note object
            sym_note = Note(
                pitch=pitch,
                velocity=velocity,
                time=note_start_time,
                duration=note_duration
            )
            sym_track.notes.append(sym_note)
        symusic_score.tracks.append(sym_track)

    # Dump the MIDI to the specified output file
    symusic_score.dump_midi(output_file)


def to_midi(filepath, score, tempo=120):
            # Transform to list of events
            CHORD_CHANNEL = 1
            MELODY_CHANNEL = 41
            events = []
            for s in score.chords:
                for idx, pitch in enumerate(s.pitches):
                    events.append([s.time, m21.pitch.Pitch(pitch).midi,s.duration, CHORD_CHANNEL, 60])
            for s in score.melody:
                if not s.is_silence:
                    events.append([s.time, m21.pitch.Pitch(s.pitch).midi, s.duration, MELODY_CHANNEL, 80])
            events_to_midi(events, filepath, tempo)


def _to_midi(S, output_file, delta=1.0, channel=0, velocity=100, midi_offset=48, scale=None, programs=None, no_repeat=False, quarter_value=1.0):
    events = to_events(S, delta, channel, velocity, midi_offset, scale, programs, no_repeat)
    events_to_midi(events, output_file, quarter_value=quarter_value)

def to_events(S, delta=1.0, channel=0, velocity=100, midi_offset=48, scale=None, programs=None, no_repeat=False):
    events = []
    if programs is None:
        programs = [0] * S.shape[0]
    
    # Initialize tracking for each voice if no_repeat is enabled
    if no_repeat:
        last_pitches = [None] * S.shape[0]          # Tracks last pitch per voice
        last_event_indices = [None] * S.shape[0]    # Tracks last event index per voice
    
    for t in range(S.shape[1]):
        for i in range(S.shape[0]):
            pitch = int(S[i, t])
            if scale is not None:
                pitch = scale[pitch % len(scale)] + 12 * (pitch // len(scale))
            current_time = t * delta
            current_pitch = midi_offset + pitch
            current_duration = delta
            current_program = programs[i]
            current_velocity = velocity
            
            if no_repeat:
                if last_pitches[i] == current_pitch and last_event_indices[i] is not None:
                    # Merge with the previous event by extending its duration
                    last_event = events[last_event_indices[i]]
                    last_event[2] += current_duration  # Increment duration
                else:
                    # Add a new event and update tracking
                    event = [current_time, current_pitch, current_duration, current_program, current_velocity]
                    events.append(event)
                    last_pitches[i] = current_pitch
                    last_event_indices[i] = len(events) - 1
            else:
                # Standard event addition without repeat handling
                event = [current_time, current_pitch, current_duration, current_program, current_velocity]
                events.append(event)
    
    return events


