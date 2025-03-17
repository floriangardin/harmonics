import xml.etree.ElementTree as ET
import os
import zipfile
import shutil

def increment_voices(musicxml_file):
    """
    Increment all <voice> tag values by 1 in a MusicXML file.
    
    Args:
        musicxml_file (str): Path to the MusicXML file to modify
    """
    # Parse the XML file
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    
    # Find all voice elements in the XML
    for voice_elem in root.findall('.//voice'):
        try:
            # Get the current voice value, increment it, and update
            current_value = int(voice_elem.text)
            voice_elem.text = str(current_value + 1)
        except (ValueError, TypeError):
            # Skip if the voice value is not a valid integer
            print(f"Warning: Found non-integer voice value: {voice_elem.text}")
    
    # Write the modified XML back to the same file
    tree.write(musicxml_file, encoding='utf-8', xml_declaration=True)

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
        with zipfile.ZipFile(mxl_file, 'w') as zipf:
            # Add META-INF/container.xml
            zipf.write(
                os.path.join(container_path, "container.xml"), 
                os.path.join("META-INF", "container.xml")
            )
            
            # Add the MusicXML file
            zipf.write(
                os.path.join(temp_dir, xml_filename),
                xml_filename
            )
        
        return mxl_file
    
    finally:
        # Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


