#!/usr/bin/env python3
import re
import sys
from collections import defaultdict

def format_ern_file(input_file, output_file):
    """
    Formats an ERN file to align beats vertically within measures.
    
    Args:
        input_file (str): Path to the input ERN file
        output_file (str): Path to the output formatted ERN file
    """
    with open(input_file, 'r') as f:
        content = f.readlines()
    
    # Separate header lines (metadata, tech, events) from measure lines
    header_lines = []
    measure_lines = []
    in_header = True
    
    for line in content:
        line = line.rstrip()
        if not line.strip():
            if in_header:
                header_lines.append(line)  # Keep empty lines in header
            continue
            
        # If line starts with m, mel, or acc, it's a measure line
        if re.match(r'^(m|mel|acc)\d+', line.strip()):
            in_header = False
            measure_lines.append(line)
        elif in_header:
            header_lines.append(line)
        else:
            measure_lines.append(line)
    
    # Group measure lines by measure number
    measure_groups = defaultdict(list)
    for line in measure_lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        match = re.match(r'^(m|mel|acc)(\d+)', line.strip())
        if match:
            measure_num = int(match.group(2))
            measure_groups[measure_num].append(line)
    
    # Format each measure group
    formatted_measures = []
    
    for measure_num in sorted(measure_groups.keys()):
        measure_group = measure_groups[measure_num]
        formatted_group = format_measure_group(measure_group)
        
        # Only add an empty line if this isn't the first group and if there 
        # are already some formatted measures
        if formatted_measures:
            formatted_measures.append('')
            
        formatted_measures.extend(formatted_group)
    
    # Combine header and formatted measures
    # Only add an empty separator line if there are header lines
    if header_lines:
        formatted_content = header_lines + [''] + formatted_measures
    else:
        formatted_content = formatted_measures
    
    # Write the formatted content to the output file
    with open(output_file, 'w') as f:
        f.write('\n'.join(formatted_content))

def format_measure_group(measure_group):
    """
    Formats a group of lines belonging to the same measure to align beats vertically.
    
    Args:
        measure_group (list): List of lines belonging to the same measure
        
    Returns:
        list: Formatted lines with beats aligned vertically
    """
    # Parse each line to extract beat positions and content
    parsed_lines = []
    all_beats = set()
    variable_calling_lines = []  # Track lines that call variables
    
    for line_idx, line in enumerate(measure_group):
        # Check if this line is a variable calling line (contains @variable_name)
        if '@' in line and not re.search(r'b\d+(?:\.\d+)?', line):
            # This is a variable calling line without beats - keep as is
            variable_calling_lines.append((line_idx, line))
            parsed_lines.append((line, {}))  # Empty beats dict
            continue
        
        # Extract the prefix (everything before the first beat)
        prefix_match = re.match(r'^([^b]*?)(?=b\d+|\Z)', line)
        prefix = prefix_match.group(1).rstrip() if prefix_match else line
        
        # Extract all beats and their content
        beat_matches = re.finditer(r'b(\d+(?:\.\d+)?)\s+(.*?)(?=\s+b\d+|\Z)', line)
        beats = {}
        
        for match in beat_matches:
            beat_num = match.group(1)
            content = match.group(2).rstrip()
            beats[beat_num] = content
            all_beats.add(beat_num)
        
        parsed_lines.append((prefix, beats))
    
    # Sort beats by their numerical value
    sorted_beats = sorted(all_beats, key=lambda x: float(x))
    
    # Determine the column positions for each beat
    beat_columns = {}
    current_column = 0
    
    # First, determine the maximum prefix length for non-variable calling lines
    max_prefix_length = 0
    for i, (prefix, _) in enumerate(parsed_lines):
        # Skip variable calling lines when determining max prefix length
        if i not in [idx for idx, _ in variable_calling_lines]:
            max_prefix_length = max(max_prefix_length, len(prefix))
    
    current_column = max_prefix_length + 1  # +1 for space
    
    # Then, determine column positions for each beat
    for beat in sorted_beats:
        beat_columns[beat] = current_column
        
        # Find the maximum content length for this beat across all lines
        max_content_length = 0
        for _, beats in parsed_lines:
            if beat in beats:
                max_content_length = max(max_content_length, len(beats[beat]))
        
        # Update current column position for the next beat
        # +2 for "b" and space after beat number, +1 for space after content
        current_column += len(f"b{beat}") + max_content_length + 3
    
    # Format each line
    formatted_lines = []
    
    for i, (prefix, beats) in enumerate(parsed_lines):
        # If this is a variable calling line, keep it as is
        if i in [idx for idx, _ in variable_calling_lines]:
            formatted_lines.append(prefix)
            continue
        
        # Start with the prefix, padded to align with the maximum prefix length
        formatted_line = prefix.ljust(max_prefix_length)
        
        # Add each beat at its column position
        for beat in sorted_beats:
            if beat in beats:
                content = beats[beat]
                beat_text = f"b{beat} {content}"
                
                # Calculate padding needed before this beat
                beat_column = beat_columns[beat]
                padding = beat_column - len(formatted_line)
                
                if padding > 0:
                    formatted_line += " " * padding
                
                formatted_line += beat_text
        
        formatted_lines.append(formatted_line)
    
    return formatted_lines

def main():
    if len(sys.argv) != 3:
        print("Usage: python formatter.py input.ern output.ern")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    format_ern_file(input_file, output_file)
    print(f"Formatted ERN file written to {output_file}")

if __name__ == "__main__":
    main() 