import sys
import os
import tempfile

BASE_FLUIDSYNTH_COMMAND = "fluidsynth {midi_file} --fast-render={output_wav}"


def to_audio(output_mp3, score):
    from .to_midi import to_midi

    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as temp_midi:
        to_midi(temp_midi.name, score)
        midi_to_mp3(temp_midi.name, output_mp3)
    os.remove(temp_midi.name)


def midi_to_mp3(midi_file, output_mp3):
    output_wav = output_mp3.replace(".mp3", ".wav")
    os.system(
        BASE_FLUIDSYNTH_COMMAND.format(midi_file=midi_file, output_wav=output_wav)
    )
    os.system(f"ffmpeg -y -i {output_wav} -codec:a libmp3lame -qscale:a 2 {output_mp3}")
    os.remove(output_wav)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python to_audio.py <input.mid> <output.mp3>")
        sys.exit(1)

    midi_file = sys.argv[1]
    output_mp3 = sys.argv[2]

    midi_to_mp3(midi_file, output_mp3)
    print(f"Converted {midi_file} to {output_mp3}")
