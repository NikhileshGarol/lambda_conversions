'''import json

def get_health_data():
    # Example percentages; you can adjust these as needed
    health_data = {
        "physical_health": 85.0,  # Physical health percentage
        "metabolic_health": 76.5, # Metabolic health percentage
        "diabetic_risk": 20.0     # Diabetic risk percentage
    }
    # Convert dictionary to JSON
    return json.dumps(health_data)

# Example usage
print(get_health_data())'''

import json

def get_variant(mobile_number):
    # Example health parameters with their values
    variant_data = {
        "good_variants": {
             
             
        },
        "bad_variants": {
              
        }
    }

    if mobile_number :
        return variant_data
    else:
        return json.dumps({"error": "No data found for this mobile number."})

