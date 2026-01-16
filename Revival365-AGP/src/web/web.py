"""
web.py
-----------
This module uses Flask to expose a web endpoint that returns 
the final JSON data.
"""

from flask import Flask, jsonify
import pandas as pd

from data_ingest.ingest import ingest_data
from data_preprocessing.preprocess import preprocess_data
from data_processing.process import process_data
from data_formatting.format_to_json import format_to_json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # Add project root to sys.path

app = Flask(__name__)

@app.route("/", methods=["GET"])
def get_glucose_data():
    """
    Main endpoint to fetch, preprocess, process, and return 
    the glucose data as JSON.
    """
    # 1. Ingest data
    raw_df = ingest_data()

    # 2. Preprocess data
    cleaned_df = preprocess_data(raw_df)

    # 3. Process data
    processed = process_data(cleaned_df)

    # 4. Format to JSON (as string)
    json_str = format_to_json(processed)

    # 5. Return as application/json
    return jsonify(processed)  # or return json_str if you prefer

