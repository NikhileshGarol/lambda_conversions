import json

def get_health_data(mobile_number):
    # Example percentages; you can adjust these as needed
    health_data = {
        "physical_health": 85.0,  # Physical health percentage
        "metabolic_health": 76.5, # Metabolic health percentage
        "diabetic_health": 20.0     # Diabetic risk percentage
    }
    # Convert dictionary to JSON
    if mobile_number :
        return health_data
    else:
        return json.dumps({"error": "No data found for this mobile number."})
