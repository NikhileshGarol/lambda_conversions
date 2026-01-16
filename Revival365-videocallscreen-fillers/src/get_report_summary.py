'''
import json

def get_report_summary(mobile_number):
    # Health data based on test results
    health_data = {
        "patient_info": {
            "name": "Mani Vannan",
            "age": 49,
            "gender": "Male",
            "tested_by": "Thyrocare",
            "package": "Gutkulture Advanced"
        },
        "lab_results": {
            "abnormal_results": [
                {
                    "test": "LDL Cholesterol",
                    "value": "136 mg/dL",
                    "reference_range": "< 100 mg/dL",
                    "status": "High"
                },
                {
                    "test": "Total Cholesterol",
                    "value": "208 mg/dL",
                    "reference_range": "< 200 mg/dL",
                    "status": "High"
                },
                {
                    "test": "TSH",
                    "value": "34.2 µIU/mL",
                    "reference_range": "0.54 - 5.30 µIU/mL",
                    "status": "High"
                },
                {
                    "test": "Vitamin D",
                    "value": "18.4 ng/mL",
                    "reference_range": "30 - 100 ng/mL",
                    "status": "Low"
                },
                {
                    "test": "SGOT",
                    "value": "48.1 U/L",
                    "reference_range": "< 35 U/L",
                    "status": "Slightly High"
                },
                {
                    "test": "Homocysteine",
                    "value": "15.78 µmol/L",
                    "reference_range": "< 15 µmol/L",
                    "status": "Elevated"
                }
            ],
            "normal_results": [
                {
                    "test": "Vitamin B12",
                    "status": "Normal"
                },
                {
                    "test": "Vitamin B1",
                    "status": "Normal"
                },
                {
                    "test": "Vitamin B2",
                    "status": "Normal"
                },
                {
                    "test": "Free Testosterone",
                    "status": "Normal"
                }
            ],
            "additional_notes": "Elevated homocysteine suggests a mild risk for cardiovascular issues."
        }
    }
    
    # Convert dictionary to JSON if mobile_number is provided
    if mobile_number:
        return health_data
    else:
        return json.dumps({"error": "No data found for this mobile number."})
'''
import json

def get_report_summary(mobile_number):
    # Health data summary as a paragraph
    report_summary = (
        " "
         
    )
    
    # Return the summary in the required format if mobile_number is provided
    if mobile_number:
        return {"report_summary": report_summary}
    else:
        return {"error": "No data found for this mobile number."}
    
    # Convert dictionary to JSON if mobile_number is provided
    if mobile_number:
        return health_data
    else:
        return json.dumps({"error": "No data found for this mobile number."})
