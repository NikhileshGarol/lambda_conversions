import json
import boto3


def lambda_handler(event, context):
    # Log the incoming event for debugging
    print("Received event:", json.dumps(event))
    
    # Initialize the IVS client
    ivs_client = boto3.client('ivs')
    
    print("Received event:", json.dumps(event))
    
    # Extract 'channel_id' from various sources
    channel_id = None
    
    # Check queryStringParameters (used by API Gateway for GET/POST query params)
    if 'queryStringParameters' in event and event['queryStringParameters']:
        channel_id = event['queryStringParameters'].get('channel_id')
    
    # Check the body (used by API Gateway for POST with JSON payload)
    if not channel_id and 'body' in event and event['body']:
        try:
            body = json.loads(event['body'])
            channel_id = body.get('channel_id')
        except json.JSONDecodeError:
            print("Failed to parse body as JSON.")
    
    # Fallback if no channel_id found
    if not channel_id:
        channel_id = 'default_channel_id'  # Or generate a UUID
    
    print("Resolved channel_id:", channel_id)
    
    try:
        # Create the IVS channel
        response = ivs_client.create_channel(
            name=channel_id,
            latencyMode='LOW',  # 'LOW' or 'NORMAL'
            type='STANDARD'     # 'BASIC' or 'STANDARD'
        )
        
        # Extract information
        rtmp_ingest_url = f"rtmps://{response['channel']['ingestEndpoint']}:443/app/"
        distribution_url = response['channel']['playbackUrl']
        stream_key = response['streamKey']['value']
        channel_name = response['channel']['name']
        
        # Return the URLs, stream key, and channel name
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'ChannelName': channel_name,
                'RTMPIngestURL': rtmp_ingest_url,
                'DistributionURL': distribution_url,
                'StreamKey': stream_key
            })
        }
    except Exception as e:
        # Handle errors with proper headers
        print("Error creating channel:", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
