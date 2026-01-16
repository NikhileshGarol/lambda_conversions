import json
from helpers_and_main import fetch_active_patients_with_alerts

def lambda_handler(event, context):
    """
    AWS Lambda entry point to fetch active patients with alerts.
    
    Expects `user_id` in event JSON payload.
    """
    try:
        # Extract user_id from event
        user_id = event.get("user_id")
        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "user_id is required"})
            }

        # Call your main function
        results = fetch_active_patients_with_alerts(user_id)

        # Return results
        return {
            "statusCode": 200,
            "body": json.dumps({"results": results}, default=str)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
