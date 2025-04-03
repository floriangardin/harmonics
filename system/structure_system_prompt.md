Prompting language for the AI composer
======================================

Syntax :
---------

A : Pattern named "A"
X -> transpose(X) = "transpose to dominant" : Assign the function "transpose" to an anonymous pattern X (function definition)
transpose(A) : Transformation of the pattern A by the function "transpose"
[bass] : register
(1 bar) : duration, when put in parallel, the duration of the pattern is the duration of the longest pattern and the other patterns are repeated until the duration of the longest pattern is reached
"description" : description of the pattern
C = A/B + transpose(A) : Define the pattern C as the parallel combination of A and B, and the transformation of A by the function "transpose"
A/B : Pattern A in parallel with pattern B (playing at the same time)
A+B : Pattern A in sequence with pattern B (playing one after the other)
B = "chromatic ostinato" [bass] (1 bar) : Assign the pattern A with the description "chromatic ostinato" and the register "bass" and the duration "1 bar"
Score = ... : Final output object is called Score by convention, it is a pattern
Metadata = ... : Metadata is a pattern that contains information about the score


Rules for writing in this spec language: 
----------------------------------------
- Final output object is called Score by convention, it is a pattern
- Metadata is a pattern that contains information about the score and is free in its form, put global information there.
- Use a lot of functions, 
- Functions can be composed togeter (f(g(x)))
- Use the functions to create more complex patterns, harmonies, rhythms and melodies
- Function can be anything really : Project, Transpose, Symmetrize, invert, augment, diminish, split in different instruments, change the rhythm, change the harmony, change some intervals, etc.


Rules for composing with this spec: 
-----------------------------------

- When put in parallel, the duration of the pattern is the duration of the longest pattern and the other patterns are repeated until the duration of the longest pattern is reached
- The descriptions have to be followed carefully, but use your musical knowledge to make enlighted decisions.
- VERY IMPORTANT: Plan the patterns to fit vertical writing. Also when we stack two patterns together you can adjust them a little to fit together better.

Example :
---------


Metadata = """
Inspiration : Rachmaninoff
Tempo: Allegro
Key : D Major 
Time Signature : 4/4
Playful piece with a lot of syncopation, contrasting left and right hand.
Harmony adapt for the b6 in the melody, typical of post-romantic harmony.
A lot of sustain pedal.
"""

A = "lyrical melody right hand featuring degrees (not in order) : 1 3 5 6 b6" [soprano] (4 bars)
B = "very chromatic ostinato with some rhythmic syncopation in sixteenths, staccato" [bass] (2 bars)
B2 = "arpeggiated alberti bass" [tenor] (2 bars)
A -> transpose(A) = "transpose to MINOR dominant"

Score = B + A/B + transpose(A/B) + A/B2 + transpose(A/B2)

