def beat_to_ern(beat):
    if beat == int(beat):
        return f"b{int(beat)}"
    else:
        # Round to 2 decimal places
        rounded_beat = round(beat, 2)
        # Convert to string and remove trailing zeros
        beat_str = str(rounded_beat)
        if beat_str.endswith(".0"):
            return f"b{int(rounded_beat)}"
        elif "." in beat_str and beat_str.endswith("0"):
            return f"b{beat_str.rstrip('0').rstrip('.')}"
        else:
            return f"b{rounded_beat}"


def to_beat_fraction(beat):
    return to_quarter_fraction(beat, (4, 4))


def to_quarter_fraction(beat, current_ts=(4, 4)):
    ratio_beat = Fraction(4, current_ts[1])
    if beat == int(beat):
        return int(beat) * ratio_beat
    else:
        fractional_part = beat - int(beat)
        fraction = to_fraction(fractional_part, (4, 4))
        return (int(beat) + fraction) * ratio_beat


from fractions import Fraction


def to_fraction(duration, current_ts=(4, 4)):
    """Convert a float duration to a Fraction for better MusicXML representation."""
    # Handle common durations
    threshold = 0.015
    ratio_beat = Fraction(4, current_ts[1])
    if abs(duration - 0.25) < threshold:
        return Fraction(1, 4) * ratio_beat  # Sixteenth note
    elif abs(duration - 0.5) < threshold:
        return Fraction(1, 2) * ratio_beat  # Eighth note
    elif abs(duration - 0.75) < threshold:
        return Fraction(3, 4) * ratio_beat  # Dotted eighth note
    elif abs(duration - 1.0) < threshold:
        return Fraction(1, 1) * ratio_beat  # Quarter note
    elif abs(duration - 1.5) < threshold:
        return Fraction(3, 2) * ratio_beat  # Dotted quarter note
    elif abs(duration - 2.0) < threshold:
        return Fraction(2, 1) * ratio_beat  # Half note
    elif abs(duration - 3.0) < threshold:
        return Fraction(3, 1) * ratio_beat  # Dotted half note
    elif abs(duration - 4.0) < threshold:
        return Fraction(4, 1) * ratio_beat  # Whole note

    # For triplets and other complex rhythms
    if abs(duration - 1 / 3) < threshold:
        return Fraction(1, 3) * ratio_beat
    elif abs(duration - 2 / 3) < threshold:
        return Fraction(2, 3) * ratio_beat

    # For other durations, convert to fraction
    return Fraction(duration).limit_denominator(12) * ratio_beat
