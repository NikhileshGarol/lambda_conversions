import json

def get_medical_condition(mobile_number):
    # Hardcoded mobile number and corresponding medical data
    hardcoded_mobile_number = "1234567890"
    
    # Medical condition summary paragraph
    description = (
         
    )

    # Return the summary if mobile_number matches
    if mobile_number:
        return {"condition": description}
    else:
        return {"error": "No data found for this mobile number."}


    # Check if the provided mobile number matches the hardcoded one
    if mobile_number :
        return patient_data
    else:
        return json.dumps({"error": "No data found for this mobile number."})

 
