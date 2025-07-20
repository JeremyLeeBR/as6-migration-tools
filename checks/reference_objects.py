import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List


@dataclass
class ReferenceObject:
    object_name: str        # The text content between XML tags (file name or path)
    object_type: str        # The Type attribute value
    pkg_file_path: str      # Source .pkg file location
    line_number: int        # Optional: XML line number for debugging


def process_pkg_for_references(file_path: str) -> List[ReferenceObject]:
    """
    Processes single .pkg file to extract reference objects
    
    Args:
        file_path: Path to .pkg file to analyze
        
    Returns:
        List of ReferenceObject instances from this file
    """
    results = []
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Try to parse as XML
        try:
            root = ET.fromstring(content)
            
            # Find all Object elements
            for obj_elem in root.iter():
                if obj_elem.tag.endswith('Object') or obj_elem.tag == 'Object':
                    # Check if Reference attribute is present and equals "true"
                    reference_attr = obj_elem.get('Reference')
                    if reference_attr == 'true':
                        object_type = obj_elem.get('Type', 'Unknown')
                        object_name = obj_elem.text.strip() if obj_elem.text else ''
                        
                        if object_name:  # Only add if we have a name
                            results.append(ReferenceObject(
                                object_name=object_name,
                                object_type=object_type,
                                pkg_file_path=file_path,
                                line_number=0  # XML parsing doesn't easily give line numbers
                            ))
        
        except ET.ParseError:
            # Fallback to regex parsing for malformed XML
            import re
            
            # Pattern to match <Object Type="..." Reference="true">content</Object>
            pattern = r'<Object[^>]*Type="([^"]*)"[^>]*Reference="true"[^>]*>([^<]*)</Object>'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for object_type, object_name in matches:
                object_name = object_name.strip()
                if object_name:
                    results.append(ReferenceObject(
                        object_name=object_name,
                        object_type=object_type,
                        pkg_file_path=file_path,
                        line_number=0
                    ))
            
            # Also try the reverse pattern (Reference before Type)
            pattern_reverse = r'<Object[^>]*Reference="true"[^>]*Type="([^"]*)"[^>]*>([^<]*)</Object>'
            matches_reverse = re.findall(pattern_reverse, content, re.IGNORECASE)
            
            for object_type, object_name in matches_reverse:
                object_name = object_name.strip()
                if object_name:
                    # Check if this object was already found to avoid duplicates
                    existing = any(
                        ref.object_name == object_name and 
                        ref.object_type == object_type and 
                        ref.pkg_file_path == file_path 
                        for ref in results
                    )
                    if not existing:
                        results.append(ReferenceObject(
                            object_name=object_name,
                            object_type=object_type,
                            pkg_file_path=file_path,
                            line_number=0
                        ))
    
    except Exception as e:
        # Log error but continue processing other files
        print(f"Warning: Error processing {file_path}: {e}")
    
    return results


def check_reference_objects(project_path: str) -> List[ReferenceObject]:
    """
    Scans all .pkg files in project for objects with Reference="true"
    
    Args:
        project_path: Root directory of AS4 project
        
    Returns:
        List of ReferenceObject instances found
    """
    all_references = []
    
    # Walk through the project directory looking for .pkg files
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith('.pkg'):
                file_path = os.path.join(root, file)
                references = process_pkg_for_references(file_path)
                all_references.extend(references)
    
    return all_references