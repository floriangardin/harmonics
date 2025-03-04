# Harmonics

A domain-specific language (DSL) for musical composition using Extended Roman Text Numeral Notation (ERNTXT).

## About

Harmonics is a powerful text-based music composition language designed for both humans and AI. It enables the creation of harmonic grids in Roman numeral notation and melodies with precise rhythmic notation. The language is carefully designed to be:

- 🎵 Easy for quickly sketching musical pieces
- 🎹 Rich in expressive capabilities for detailed compositions
- 🤖 Compatible with Large Language Models (LLMs) for "compositional assistance"
- 🎼 Capable of outputting MIDI, MusicXML, and audio files

## Installation

```bash
# Clone the repository
git clone https://github.com/floriangardin/harmonics.git
cd harmonics

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install for development
pip install -e .
```

## Quick Start

Create a simple musical piece by writing a `.ern` file:

```erntxt
Composer: Your Name
Piece: My First Composition
Time Signature: 4/4
Tempo: 120

m1 b1 C: I b3 V ||
mel1 V1 b1 C5 b2 E5 b3 G5 b4 F5
acc1 b1 1 b2 234 b3 1 b4 234
```

Then compile it to MIDI, MusicXML, or audio:

```bash
# To MIDI
python main.py your_composition.ern --output output.mid

# To MusicXML
python main.py your_composition.ern --output output.mxl

# To audio (MP3)
python main.py your_composition.ern --output output.mp3
```

## Documentation

For more detailed documentation, please refer to:

- [Installation Guide](documentation/INSTALLATION.md)
- [Language Syntax](documentation/LANGUAGE_SYNTAX.md)
- [Examples](documentation/EXAMPLES.md)
- [API Reference](documentation/API_REFERENCE.md)
- [LLM Integration](documentation/LLM_INTEGRATION.md)
- [Contributing](documentation/CONTRIBUTING.md)

## License

Harmonics is released under the MIT License. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2023 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.