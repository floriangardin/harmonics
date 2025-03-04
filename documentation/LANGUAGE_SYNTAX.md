# Harmonics Language Syntax

Harmonics uses Extended Roman Text Numeral Notation (ERNTXT) for music composition. This document covers the core syntax elements and how to use them.

## Basic Syntax

Harmonics documents consist of:
- **Metadata lines** - Provide general information about the piece
- **Statement lines** - Define harmony, melody, and accompaniment
- **Events** - Modify performance parameters

Each line type has a specific prefix:
- `m` for measures (harmony)
- `mel` for melody
- `acc` for accompaniment
- `e` for events

### Example of Basic Structure

```erntxt
Composer: Johann Sebastian Bach
Piece: Simple Chorale
Time Signature: 4/4
Tempo: 100

m1 b1 C: I b3 V7 ||
mel1 V1 b1 C5 b2 E5 b3 G5 b4 E5
acc1 b1 1 b2 234 b3 1 b4 234
```

## Metadata

Metadata provides context for the piece. Essential metadata includes:

- **Composer**: `Composer: Johannes Brahms`
- **Piece**: `Piece: Symphony No. 1 in C minor (excerpt)`
- **Time Signature**: `Time Signature: 3/4`
- **Tempo**: `Tempo: 120` (quarter notes per minute)

Optional metadata:
- **Form**: `Form: Sonata`
- **Note**: `Note: Section A - Main theme`
- **Instrument**: `Instrument: V1=41, V2=74, B=1` (Maps voices to General MIDI instruments)

## Harmony Rules (m\<index>)

Harmony is expressed using Roman numeral notation with the `m` prefix followed by a measure number:

```erntxt
m1 b1 C: I b3 V7 ||
```

Key features:
- **Roman numerals** represent scale degrees (I, ii, V7, etc.)
- **Uppercase** for major chords, **lowercase** for minor
- **Colons** indicate key changes (`C:` for C major, `c:` for C minor)
- **b\<number>** indicates the beat where a chord occurs
- **||** indicates phrase boundaries
- **Secondary dominants** are supported (V7/V, V7/ii, etc.)
- **Chord alterations** can be specified in brackets: `[add9]`, `[b5]`, `[no3]`
- **Inversions** can be specified with numbers: `I6`, `V43`, etc.

### Harmony Examples

```erntxt
m1 b1 C: I b3 V6 ||                      // C major chord on beat 1, G major first inversion on beat 3
m2 b1.5 vi b2 IV b3 ii b4 V7 ||          // A minor on beat 1.5, F major on beat 2, etc.
m3 b1 I b3 G: V7/V ||                    // C major chord, then A7 (V7/V in G major)
m4 b1 C: iiø7[b5] b3 V7[add9] b4 i ||    // D half-diminished with flat 5, G7 with added 9th, C minor
```

## Melody Rules (mel\<index>)

Melody lines define the individual melodic voices with the `mel` prefix:

```erntxt
mel1 V1 b1 C5 b2 E5 b3 G5 b4 E5
```

Key features:
- **V\<number>** specifies the voice number (V1, V2, etc.)
- **b\<number>** indicates the beat where a note occurs
- **Pitch notation** uses absolute notation (C5, F#4, etc.)
- **R** or **r** indicates rests
- Notes last until the next specified beat or end of measure
- Octave alterations can be added with `o<number>` (e.g., `E5o1` raises E5 by one octave)

### Melody Examples

```erntxt
mel1 V1 b1 C5 b2 E5 b3 G5 b4 E5          // Simple C major arpeggio
mel2 V1 b1 D5 b1.5 E5 b2 F#5 b3 A5 b4 r  // Melody with sixteenth notes and rest
mel3 V2 b1 G4 b2.5 A4 b3 B4 b4.75 C5     // Second voice with varied rhythm
```

## Accompaniment Rules (acc\<index>)

Accompaniment patterns define which voices participate at each beat, numbered 1-4:

```erntxt
acc1 b1 1 b2 234 b3 1 b4 234
```

Key features:
- **1** = Bass, **2** = Tenor, **3** = Alto, **4** = Soprano (SATB notation)
- The parser automatically handles voice leading for the specified chord
- Patterns can define arpeggios, block chords, or rhythmic patterns
- Octave shifts can be specified with `o<number>` (e.g., `1o1` = bass one octave higher)

### Accompaniment Examples

```erntxt
acc1 b1 1234 b2 1234 b3 1234 b4 1234     // Block chords on each beat
acc2 b1 1 b1.5 3 b2 4 b2.5 2 b3 1 b4 34  // Arpeggiated pattern
acc3 b1 1 b2 3 b3 24 b4 13               // Mixed pattern
```

By default the parser generate a SATB voicing from the defined harmony.

## Event Rules (e\<index>)

Events control performance aspects like tempo and dynamics:

```erntxt
e1 b1 tempo(120) b1 velocity(mf)
```

Key event functions:
- **tempo(number)** - Sets the tempo in BPM
- **velocity(value)** - Sets the dynamic level (pp, p, mp, mf, f, ff, etc.)
- **start_crescendo(value)** - Begins a crescendo from the specified dynamic
- **end_crescendo(value)** - Ends a crescendo at the specified dynamic
- **start_ritardando(value)** - Begins slowing down
- **end_ritardando(value)** - Ends slowing down

### Event Examples

```erntxt
e1 b1 tempo(72) b1 velocity(mp)
e2 b1 start_crescendo(p) b4 end_crescendo(f)
e3 b1 start_ritardando(72) b4 end_ritardando(60)
```

## Variables and Control Flow

Variables allow you to define reusable patterns of one bar:

```erntxt
arpeggiated_acc = b1 1 b1.5 3 b2 4 b2.5 2 b3 1 b3.5 3 b4 4 b4.5 2
```

To use a variable, reference it with the `@` symbol:

```erntxt
acc1 @arpeggiated_acc
```

Variables work with:
- Accompaniment patterns
- Melody fragments
- Harmonic progressions

### Variable Examples

```erntxt
// Define variables
basic_arpeggio = b1 1 b1.5 3 b2 4 b2.5 3 b3 1 b3.5 3 b4 4 b4.5 3
melody_fragment = V1 b1 C5 b2 E5 b3 G5 b4 E5

// Use variables
acc1 @basic_arpeggio
mel1 @melody_fragment
```

## Beat Numbering

Beat numbers follow the conventions for each time signature:

- **4/4**: 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5
- **3/4**: 1, 1.5, 2, 2.5, 3, 3.5
- **6/8**: 1, 1.33, 1.67, 2, 2.33, 2.67
- **2/2**: 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75

The time signature determines the interpretation of beat numbers throughout the piece.
