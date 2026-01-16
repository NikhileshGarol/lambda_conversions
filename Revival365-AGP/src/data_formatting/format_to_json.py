"""
format_to_json.py
-----------
This module takes the processed data (Python dictionaries, etc.) 
and returns a JSON-formatted string.
"""

import json

def format_to_json(data):
    """
    Take a dictionary (or any serializable data) and return 
    a pretty JSON string.
    """
    return json.dumps(data, indent=4)
