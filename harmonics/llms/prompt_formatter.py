import os

import jinja2

pardir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pardir_pardir = os.path.dirname(pardir)

system_dir = os.path.join(pardir_pardir, "system")
harmonic_file_dir = os.path.join(system_dir, "library", "harmonies")
melodic_file_dir = os.path.join(system_dir, "library", "melodies")
accompaniment_file_dir = os.path.join(system_dir, "library", "accompaniments")


base_harmonic_file = os.path.join(harmonic_file_dir, "base.txt")
base_melodic_file = os.path.join(melodic_file_dir, "base.txt")
base_accompaniment_file = os.path.join(accompaniment_file_dir, "base.txt")

language_specification_file = os.path.join(system_dir, "erntxt.md")

with open(language_specification_file, "r") as f:
    language_specification_content = f.read()

with open(base_harmonic_file, "r") as f:
    base_harmonic_file_content = f.read()
with open(base_melodic_file, "r") as f:
    base_melodic_file_content = f.read()
with open(base_accompaniment_file, "r") as f:
    base_accompaniment_file_content = f.read()


from harmonics.llms.instructions import INSTRUCTION
class PromptFormatter:
    def __init__(self):
        self.data = {
            "LANGUAGE_SPECIFICATION": language_specification_content,
            "HARMONIC_LIBRARY": base_harmonic_file_content,
            "MELODY_LIBRARY": base_melodic_file_content,
            "ACCOMPANIMENT_LIBRARY": base_accompaniment_file_content,
        }

    def format_prompt(self, prompt):
        template = jinja2.Template(prompt)
        return template.render(**self.data)









prompt_formatter = PromptFormatter()
prompt = prompt_formatter.format_prompt(INSTRUCTION)


from pdb import set_trace; set_trace()