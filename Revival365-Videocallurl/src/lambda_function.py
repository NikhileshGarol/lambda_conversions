import json
import os

def lambda_handler(event, context):
    # Detect environment from API Gateway stage
    stage = event.get("requestContext", {}).get("stage", "dev")

    # Environment-specific URLs
    url_mapping = {
        "dev": "https://webrtc1.ddns.net",
        "uat": "https://webrtc1.ddns.net",
        "prod": "https://webrtc1.ddns.net"
    }

    # Get URL based on stage, default to dev URL
    video_call_url = url_mapping.get(stage, "https://webrtc1.ddns.net")
    allowed_origin = os.environ.get("ALLOWED_ORIGIN", "*")

    # Standard CORS headers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }

    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "CORS preflight"})
        }

    # Actual GET/POST request
    response_body = {
        "VideoCallURL": video_call_url
     }

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(response_body)
    }
