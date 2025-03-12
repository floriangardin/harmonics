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
