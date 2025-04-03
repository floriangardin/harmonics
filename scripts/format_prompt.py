import argparse
import sys
import os

HARMONY_PROMPT = """
- Harmony : 

{data}
"""

MELODY_PROMPT = """
- Melody : 

```
{data}
```
"""

ACCOMPANIMENT_PROMPT = """
- Accompaniment :

```
{data}
```
"""

STRUCTURE_PROMPT = """
- Structure : 

```
{data}
```
"""

SEPARATOR  = "--------"

FILE_DICT = {
    "system_prompt": "system_prompt.md",
    "harmony": "harmony_system_prompt.md",
    "melody": "melody_system_prompt.md",
    "accompaniment": "accompaniment_system_prompt.md",
    "structure": "structure.ern.spec",
}
BASE_DIR = 'system'

def get_system_prompt(type):
    filepath = os.path.join(BASE_DIR, FILE_DICT[type])
    with open(filepath, 'r') as f:
        return f.read()

def format_prompt(output, type, structure=None, harmony=None, melody=None, accompaniment=None):
    user_prompt = ""
    system_prompt = get_system_prompt(type)
    user_prompt += "Instructions:\n"
    user_prompt += system_prompt + "\n"
    user_prompt += "User:\n"
    if harmony:
        user_prompt += HARMONY_PROMPT.format(data=harmony)
    if melody:
        user_prompt += MELODY_PROMPT.format(data=melody)
    if accompaniment:
        user_prompt += ACCOMPANIMENT_PROMPT.format(data=accompaniment)
    if structure:
        user_prompt += STRUCTURE_PROMPT.format(data=structure)
    with open(output, 'w') as f:
        f.write(user_prompt)
    return user_prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure", "-s", type=str, default=None, required=False)
    parser.add_argument("--harmony", "-ha", type=str, default=None, required=False)
    parser.add_argument("--melody", "-m", type=str, default=None, required=False)
    parser.add_argument("--accompaniment", "-a", type=str, default=None, required=False)
    parser.add_argument("--type", "-t", type=str, required=True)
    parser.add_argument("--directory", "-d", type=str, default=None, required=False)
    parser.add_argument("--output", "-o", type=str, default=None, required=False)

    args = parser.parse_args()
    output = args.output
    type = args.type
    structure = args.structure
    harmony = args.harmony
    melody = args.melody
    accompaniment = args.accompaniment
    directory = args.directory
    if not output and not directory:
        raise ValueError("You must provide either an output file or a directory")
    
    if directory and (structure or harmony or melody or accompaniment):
        raise ValueError("Cannot provide both directory and individual arguments")

    if directory:
        if os.path.exists(os.path.join(directory, "structure.ern.spec")):
            with open(os.path.join(directory, "structure.ern.spec"), 'r') as f:
                structure = f.read()
        if os.path.exists(os.path.join(directory, "harmony.ern")):
            with open(os.path.join(directory, "harmony.ern"), 'r') as f:
                harmony = f.read()
        if os.path.exists(os.path.join(directory, "melody.ern")):
            with open(os.path.join(directory, "melody.ern"), 'r') as f:
                melody = f.read()
        if os.path.exists(os.path.join(directory, "accompaniment.ern")):
            with open(os.path.join(directory, "accompaniment.ern"), 'r') as f:
                accompaniment = f.read()
        if not output:
            output = os.path.join(directory, f"prompt_{type}.txt")
    
    print(output, type, structure, harmony, melody, accompaniment)
    print(format_prompt(output, type, structure, harmony, melody, accompaniment))
