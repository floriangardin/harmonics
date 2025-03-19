import xml.etree.ElementTree as ET
import os
import zipfile
import shutil


def correct_xml_file(musicxml_file):
    """
    Correct the file by replacing the pedal direction with the correct one.
    """
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    _replace_pedal_direction(root)
    _increment_voices(root)
    _add_sound_pizzicato(root)
    _add_sound_arco(root)
    # Write the modified XML back to the same file
    tree.write(musicxml_file, encoding="utf-8", xml_declaration=True)


def _add_sound_pizzicato(root):
    """
    In element with text "pizz." add the sound element :
    <direction placement="above">
        <direction-type>
          <words relative-y="10">pizz.</words>
          </direction-type>
        <sound pizzicato="yes"/>
    </direction>
    """
    # Find all direction elements in the score that might contain pizz. notation
    for direction in root.findall(".//direction"):
        # Look for words elements that contain "pizz."
        words_elem = direction.find(".//words")
        if (
            words_elem is not None
            and words_elem.text is not None
            and "pizz." in words_elem.text.strip()
        ):
            # Check if the direction already has a sound element
            sound_elem = direction.find("sound")

            # If sound element doesn't exist, add it
            if sound_elem is None:
                # Add sound element with pizzicato="yes" attribute
                sound_elem = ET.Element("sound", {"pizzicato": "yes"})
                direction.append(sound_elem)

                # Also ensure direction has placement="above" attribute if not already specified
                if "placement" not in direction.attrib:
                    direction.set("placement", "above")

                # If words element doesn't have relative-y, add it
                if "relative-y" not in words_elem.attrib:
                    words_elem.set("relative-y", "10")


def _add_sound_arco(root):
    """
    In element with text "arco" add the sound element :
    <direction placement="above">
        <direction-type>
          <words relative-y="10">pizz.</words>
          </direction-type>
        <sound pizzicato="no"/>
    </direction>
    """
    # Find all direction elements in the score that might contain pizz. notation
    for direction in root.findall(".//direction"):
        # Look for words elements that contain "pizz."
        words_elem = direction.find(".//words")
        if (
            words_elem is not None
            and words_elem.text is not None
            and "arco" in words_elem.text.strip()
        ):
            # Check if the direction already has a sound element
            sound_elem = direction.find("sound")

            # If sound element doesn't exist, add it
            if sound_elem is None:
                # Add sound element with pizzicato="yes" attribute
                sound_elem = ET.Element("sound", {"pizzicato": "no"})
                direction.append(sound_elem)

                # Also ensure direction has placement="above" attribute if not already specified
                if "placement" not in direction.attrib:
                    direction.set("placement", "above")

                # If words element doesn't have relative-y, add it
                if "relative-y" not in words_elem.attrib:
                    words_elem.set("relative-y", "10")


def _replace_pedal_direction(root):
    """
    Replace this element :
    <direction>
        <direction-type>
          <words enclosure="none" font-style="italic">$pedal_start</words>
        </direction-type>
      </direction>

    With this one :
    <direction placement="below">
        <direction-type>
          <pedal type="start" sign="yes" line="no"/>
        </direction-type>
    </direction>

    And this one :
    <direction>
        <direction-type>
          <words enclosure="none" font-style="italic">$pedal_stop</words>
        </direction-type>
    </direction>

    By this one :
    <direction placement="below">
        <direction-type>
          <pedal type="stop" sign="yes" line="no"/>
        </direction-type>
    </direction>

    Do this with the comment name '$pedal_start' and '$pedal_stop'
    """
    # Find all measures in the score
    for part in root.findall(".//part"):
        for measure in part.findall("./measure"):
            # Find and process all direction elements within this measure
            directions_to_remove = []
            for i, child in enumerate(measure):
                if child.tag == "direction":
                    words_elem = child.find(".//words")
                    if words_elem is not None and words_elem.text is not None:
                        if words_elem.text.strip() == "$pedal_start":
                            # Create new direction element with proper pedal marking
                            new_direction = ET.Element(
                                "direction", {"placement": "below"}
                            )
                            direction_type = ET.SubElement(
                                new_direction, "direction-type"
                            )
                            ET.SubElement(
                                direction_type,
                                "pedal",
                                {"type": "start", "sign": "yes", "line": "no"},
                            )

                            # Store the index to replace it later
                            directions_to_remove.append((i, new_direction))

                        elif words_elem.text.strip() == "$pedal_stop":
                            # Create new direction element with proper pedal marking
                            new_direction = ET.Element(
                                "direction", {"placement": "below"}
                            )
                            direction_type = ET.SubElement(
                                new_direction, "direction-type"
                            )
                            ET.SubElement(
                                direction_type,
                                "pedal",
                                {"type": "stop", "sign": "yes", "line": "no"},
                            )

                            # Store the index to replace it later
                            directions_to_remove.append((i, new_direction))

            # Now replace the directions (in reverse order to not upset the indices)
            for index, new_elem in sorted(directions_to_remove, reverse=True):
                measure.remove(measure[index])
                measure.insert(index, new_elem)


def _increment_voices(root):
    """
    Increment all <voice> tag values by 1 in a MusicXML file.

    Args:
        musicxml_file (str): Path to the MusicXML file to modify
    """

    # Find all voice elements in the XML
    for voice_elem in root.findall(".//voice"):
        try:
            # Get the current voice value, increment it, and update
            current_value = int(voice_elem.text)
            voice_elem.text = str(current_value + 1)
        except (ValueError, TypeError):
            # Skip if the voice value is not a valid integer
            print(f"Warning: Found non-integer voice value: {voice_elem.text}")


def convert_musicxml_to_mxl(musicxml_file):
    """
    Convert a MusicXML file to a MXL file (compressed MusicXML).

    Args:
        musicxml_file (str): Path to the MusicXML file to convert

    Returns:
        str: Path to the created MXL file
    """
    # Get the base filename without extension
    base_name = os.path.splitext(musicxml_file)[0]
    mxl_file = f"{base_name}.mxl"

    # Create a temporary directory for the ZIP contents
    temp_dir = f"{base_name}_temp"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Copy the MusicXML file to the temp directory
        xml_filename = os.path.basename(musicxml_file)
        shutil.copy(musicxml_file, os.path.join(temp_dir, xml_filename))

        # Create the container.xml file required for MXL format
        container_path = os.path.join(temp_dir, "META-INF")
        os.makedirs(container_path, exist_ok=True)

        container_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<container>
  <rootfiles>
    <rootfile full-path="{xml_filename}"/>
  </rootfiles>
</container>"""

        with open(os.path.join(container_path, "container.xml"), "w") as f:
            f.write(container_content)

        # Create the MXL file (ZIP archive)
        with zipfile.ZipFile(mxl_file, "w") as zipf:
            # Add META-INF/container.xml
            zipf.write(
                os.path.join(container_path, "container.xml"),
                os.path.join("META-INF", "container.xml"),
            )

            # Add the MusicXML file
            zipf.write(os.path.join(temp_dir, xml_filename), xml_filename)

        return mxl_file

    finally:
        # Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
