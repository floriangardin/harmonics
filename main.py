import dotenv
dotenv.load_dotenv()

from harmonics import HarmonicsParser   

text = r"""
Composer: Ludwig van Beethoven
Piece: Sonata-Allegro in C Minor
Analyst: Harmony Scholar
Proofreader: Anne Melodia
Time Signature: 4/4
Movement: 0
Key Signature: -3
Minor Sixth / Minor Seventh: quality

m1 b1 c: i b3 VI7
m2 b1 iv b3 V7
Note: Opening with a strong statement in C minor, followed by a VI7 chord, evoking a sense of foreboding and tension. Moving to a dominant that sets up resolution.

m3 b1 i b2 i6 b3 iv
m4 b1 i64 b3 V7
Note: Use of first inversion to create a smooth bass line and build tension toward the cadential i64 V7 progression.

m5 b1 Eb: I b3 ii65
m6 b1 V7 b3 I
Note: Modulation to Eb major for the development section, brightening the mood temporarily with rich harmonic support and classical resolution.

m7 b1 iii6 b3 vi
m8 b1 IV b2 vii°7 b3 I
Note: A playful dance with offbeat chords, emphasizing Neapolitan-like harmony before arriving back to stable ground for dramatic effect.

m9 b1 c: iv6 b3 bVI
Note: Abrupt return to c minor, with surprising bVI for tonal dramatism and creating a foreshadow of the upcoming climax.

m10 b1 vii°7/V b3 V7
m11 b1 i b4 V7
Note: Quickened pace of harmonic rhythm, leading into a climactic drive with a leading-tone chord toward the dominant, creating expectation.

m12 b1 C: I b3 V65/vi
m13 b1 vi b3 bVII9
Note: Sudden bright modulation to C major offering thematic contrast. bVII9 adds unexpected color and complexity.

m14 b1 c: iv b3 VI
m15 b1 V42 b3 Cad64
Note: Return to the home key for the recapitulation, utilizing a surprising switch with V42 moving into a Cadential six-four for grandeur.

m16 b1 V7 b3 i
Note: A strong, resolute conclusion, reinforcing the home key with powerful dominant and tonic affirmations.
"""



# parser = HarmonicsParser()
# tree = parser.parse_to_midi(text, "test.mid")


from harmonics.llms.generate import compose_rntxt
prompt =  """
Create a sonata-allegro reminiscent of Debussy impressionist style.
Post tonality, strong chord colors, no strong harmonic center and no clear dominant tonic relationship.
Assume 4/4. Vary the harmonic rhythm, pace & mood during the piece.
Use eight note duration chords sometimes.
16 bars.
"""
print('Composing ...')
rntxt = compose_rntxt(prompt, model="gpt-4o")
print(rntxt)

print('Correcting ...')
from harmonics.llms.generate import correct_rntxt
corrected_rntxt = correct_rntxt(rntxt, model="gpt-4o")
print(corrected_rntxt)

print('Parsing ...')
parser = HarmonicsParser()
tree = parser.parse_to_midi(corrected_rntxt, "test.mid")

# Generate unique uid
import uuid
uid = str(uuid.uuid4())

# Save the rntxt
with open(f'data/debussy_{uid[:5]}.rntxt', 'w') as f:
    f.write(corrected_rntxt)
