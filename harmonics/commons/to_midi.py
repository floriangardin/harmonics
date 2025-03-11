from symusic import Score, Track, Note, Tempo, TimeSignature
import music21 as m21
from .utils_techniques import apply_techniques_after, apply_techniques_before


def _create_velocity_mappings():
    """Returns a dictionary mapping dynamic markings to MIDI velocity values."""
    return {
        "pppp": 10,
        "ppp": 20,
        "pp": 30,
        "p": 40,
        "mp": 50,
        "mf": 60,
        "f": 70,
        "ff": 80,
        "fff": 90,
        "ffff": 100,
    }


def _process_velocity_events(events):
    """Process velocity and crescendo/diminuendo events."""
    velocities_array = []
    crescendo_stack = []
    crescendo_regions = []
    velocities_map = _create_velocity_mappings()

    if not events:
        return [], []

    current_velocity = 80  # Default velocity
    for event in events:
        if event.event_type == "velocity":
            current_velocity = velocities_map[event.event_value]
            velocities_array.append((event.time, current_velocity))
        elif event.event_type in ["start_crescendo", "start_diminuendo"]:
            start_vel = velocities_map[event.event_value]
            crescendo_stack.append((event.time, start_vel))
        elif event.event_type in ["end_crescendo", "end_diminuendo"]:
            if crescendo_stack:
                start_time, start_vel = crescendo_stack.pop()
                end_vel = velocities_map[event.event_value]
                crescendo_regions.append((start_time, event.time, start_vel, end_vel))

    velocities_array.sort(key=lambda x: x[0])
    crescendo_regions.sort(key=lambda x: x[0])
    return velocities_array, crescendo_regions


def _process_tempo_events(events):
    """Process tempo and accelerando/ritardando events."""
    tempo_array = []
    tempo_change_stack = []
    tempo_regions = []

    if not events:
        return [], []

    current_tempo = 120  # Default tempo
    for event in events:
        if event.event_type == "tempo":
            current_tempo = int(event.event_value)
            tempo_array.append((event.time, current_tempo))
        elif event.event_type in ["start_accelerando", "start_ritardando"]:
            start_tempo = int(event.event_value)
            tempo_change_stack.append((event.time, start_tempo))
        elif event.event_type in ["end_accelerando", "end_ritardando"]:
            if tempo_change_stack:
                start_time, start_tempo = tempo_change_stack.pop()
                end_tempo = int(event.event_value)
                tempo_regions.append((start_time, event.time, start_tempo, end_tempo))

    tempo_array.sort(key=lambda x: x[0])
    tempo_regions.sort(key=lambda x: x[0])
    return tempo_array, tempo_regions


def _initialize_score(time_signatures=None, tempos=None, target_tpq=480):
    """Initialize a Symusic Score with time signatures and tempos."""
    symusic_score = Score()
    symusic_score.tpq = target_tpq

    # Add time signatures
    if time_signatures:
        for ts in time_signatures:
            sym_ts = TimeSignature(
                time=int(ts.time * target_tpq),
                numerator=ts.time_signature[0],
                denominator=ts.time_signature[1],
            )
            symusic_score.time_signatures.append(sym_ts)
    else:
        symusic_score.time_signatures.append(
            TimeSignature(time=0, numerator=4, denominator=4)
        )

    # Add tempos
    if tempos:
        for t in tempos:
            sym_tempo = Tempo(time=int(t.time * target_tpq), qpm=int(t.tempo))
            symusic_score.tempos.append(sym_tempo)
    else:
        symusic_score.tempos.append(Tempo(time=0, qpm=120))


    return symusic_score


def events_to_midi(
    note_events,
    output_file,
    tempos=None,
    time_signatures=None,
    quarter_value=1.0,
    events=None,
):
    """Converts a list of events to a MIDI file using Symusic."""
    target_tpq = 480

    # Process velocity and tempo events
    velocities_array, crescendo_regions = _process_velocity_events(events)
    tempo_array, tempo_regions = _process_tempo_events(events)

    def get_current_velocity(time: float) -> int:
        current_velocity = None
        for velocity in velocities_array:
            if velocity[0] <= time:
                current_velocity = velocity[1]
            else:
                break

        for cresc in crescendo_regions:
            start_time, end_time, start_vel, end_vel = cresc
            if start_time <= time <= end_time:
                progress = (time - start_time) / (end_time - start_time)
                current_velocity = int(start_vel + (end_vel - start_vel) * progress)

        return current_velocity if current_velocity is not None else 80

    def get_current_tempo(time: float) -> int:
        current_tempo = None
        for tempo in tempo_array:
            if tempo[0] <= time:
                current_tempo = tempo[1]
            else:
                break

        for tempo_region in tempo_regions:
            start_time, end_time, start_tempo, end_tempo = tempo_region
            if start_time <= time <= end_time:
                progress = (time - start_time) / (end_time - start_time)
                current_tempo = int(start_tempo + (end_tempo - start_tempo) * progress)

        return current_tempo if current_tempo is not None else 120

    # Initialize score
    symusic_score = _initialize_score(time_signatures, tempos, target_tpq)

    # Add tempo events
    previous_time = 0
    previous_tempo = 120
    step_size = 0.25  # Quarter note divisions for smooth tempo changes

    # Process all tempo changes including gradual ones
    all_times = sorted(
        set(
            [0]
            + [t[0] for t in tempo_array]
            + [t for region in tempo_regions for t in [region[0], region[1]]]
        )
    )

    for time in all_times:
        if time > previous_time:
            # Add intermediate tempo points for smooth transitions
            for t in range(int(previous_time / step_size), int(time / step_size)):
                current_time = t * step_size
                current_tempo = get_current_tempo(current_time)
                if current_tempo != previous_tempo:
                    tempo = Tempo(
                        time=int(current_time * target_tpq), qpm=current_tempo
                    )
                    symusic_score.tempos.append(tempo)
                    previous_tempo = current_tempo

        current_tempo = get_current_tempo(time)
        if current_tempo != previous_tempo:
            tempo = Tempo(time=int(time * target_tpq), qpm=current_tempo)
            symusic_score.tempos.append(tempo)
            previous_tempo = current_tempo
        previous_time = time

    # Add events
    for event in events:
        if event.event_type == "tempo":
            tempo = Tempo(time=int(event.time * target_tpq), qpm=int(event.event_value))
            symusic_score.tempos.append(tempo)

    # Group events by MIDI program
    program_events = {}
    for event in note_events:
        time, pitch, duration, midi_program, velocity, techniques = event
        if midi_program not in program_events:
            program_events[midi_program] = []
        program_events[midi_program].append(event)

    # Create a track for each MIDI program
    for midi_program, prog_events in program_events.items():
        sym_track = Track(program=midi_program - 1, is_drum=False)

        # Sort events by start time
        prog_events.sort(key=lambda x: x[0])
        for event in prog_events:

            if event[4] is None:
                event[4] = get_current_velocity(time)

            event = apply_techniques_after(event[5], event)
            time, pitch, duration, _, velocity, techniques = event

            # Convert time and duration from event units to ticks
            note_start_time = int((time / quarter_value) * target_tpq)
            note_duration = int((duration / quarter_value) * target_tpq)

            # Create a Symusic Note object
            sym_note = Note(
                pitch=pitch,
                velocity=int(velocity),
                time=note_start_time,
                duration=note_duration,
            )
            sym_track.notes.append(sym_note)
        symusic_score.tracks.append(sym_track)
    # Dump the MIDI to the specified output file
    symusic_score.dump_midi(output_file)

def solve_continuation(notes):
    """
    Refactor note items to handle continuations.
    
    This function processes a list of NoteItem objects, extending the duration of notes
    when they are followed by continuation marks. Continuation notes themselves are not
    included in the result.
    
    Args:
        notes: A list of NoteItem objects from the score
        
    Returns:
        A list of NoteItem objects with continuations resolved
    """
    last_note_of_voice = {}  # Tracks the last note for each voice
    result = []
    
    for note in notes:
        if note.is_continuation:
            # If this is a continuation, extend the duration of the last note in this voice
            if note.voice_name in last_note_of_voice:
                last_note = last_note_of_voice[note.voice_name]
                last_note.duration += note.duration
            # Don't add the continuation note to the result
        else:
            # Add regular notes to the result
            result.append(note)
            # Update the last note for this voice
            last_note_of_voice[note.voice_name] = note

    return result
def to_midi(filepath, score):
    # Default MIDI programs if not specified
    DEFAULT_MELODY_CHANNEL = 1
    # Create a time-based mapping of voice assignments from instrument items
    voice_program_map = {}
    for instrument in score.instruments:
        if instrument.voice_name == "T":
            voice_key = f"T{instrument.voice_index}"
        else:
            voice_key = instrument.voice_name
        voice_program_map[voice_key] = int(instrument.gm_number)

    note_events = []
    notes = solve_continuation(score.notes)
    for s in notes:
        if not s.is_silence:
            program = voice_program_map.get(s.voice_name, DEFAULT_MELODY_CHANNEL)
            if isinstance(s.pitch, str):
                note_event = [
                    s.time,
                    m21.pitch.Pitch(s.pitch).midi,
                    s.duration,
                    program,
                    None,
                    s.techniques,
                ]
                note_event = apply_techniques_before(s.techniques, note_event)
                note_events.append(note_event)
            else:
                for pitch in s.pitch:
                    note_event = [
                        s.time,
                        m21.pitch.Pitch(pitch).midi,
                        s.duration,
                        program,
                        None,
                        s.techniques,
                    ]
                    note_event = apply_techniques_before(s.techniques, note_event)
                    note_events.append(note_event)


    events_to_midi(
        note_events,
        filepath,
        tempos=score.tempos,
        time_signatures=score.time_signatures,
        events=score.events,
    )
