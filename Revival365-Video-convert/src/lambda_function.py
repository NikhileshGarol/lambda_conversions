import boto3
import json
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_mediaconvert_client():
    """Discover account-specific MediaConvert endpoint"""
    mc = boto3.client("mediaconvert", region_name="ap-south-1")
    endpoint = mc.describe_endpoints()["Endpoints"][0]["Url"]
    return boto3.client("mediaconvert", endpoint_url=endpoint, region_name="ap-south-1")

def create_job_with_template(input_s3, output_s3):
    try:
        mediaconvert_client = get_mediaconvert_client()

        # Replace with your actual MediaConvert_Default_Role from account 827164363142
        job_settings = {
            "Role": "arn:aws:iam::827164363142:role/service-role/Media-convert-lambda",
            "JobTemplate": "hls",  # must already exist in AWS console
            "Settings": {
                "Inputs": [
                    {
                        "FileInput": input_s3,
                        "AudioSelectors": {
                            "Audio Selector 1": {"DefaultSelection": "DEFAULT"}
                        },
                        "TimecodeSource": "EMBEDDED"
                    }
                ],
                "OutputGroups": [
                    {
                        "OutputGroupSettings": {
                            "Type": "HLS_GROUP_SETTINGS",
                            "HlsGroupSettings": {
                                "Destination": output_s3
                            }
                        }
                    }
                ]
            }
        }

        response = mediaconvert_client.create_job(**job_settings)
        print("Job created:", response["Job"]["Id"])
        return True
    except Exception as e:
        print(f"Error creating job: {e}")
        return False

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        input_file = body.get("input_file")
        output_path = body.get("output_path")

        if not input_file or not output_path:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "input_file and output_path are required"})
            }

        job_created = create_job_with_template(input_file, output_path)

        if job_created:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Job created successfully"})
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Error creating MediaConvert job"})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error processing the request",
                "error": str(e)
            })
        }
