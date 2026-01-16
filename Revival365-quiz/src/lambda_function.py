import json
import logging
import random  # Import random module to select random questions

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Log the incoming event for debugging
    logger.info(f"Received event: {json.dumps(event)}")

    # Get the stage from the request context
    stage = event.get('requestContext', {}).get('stage', '$default')
    logger.info(f"Running in stage: {stage}")

    # Stage-specific configuration
    if stage == 'dev':
        logger.setLevel(logging.DEBUG)
        logger.debug("Running in DEVELOPMENT mode with detailed logging")
    elif stage == 'uat':
        logger.setLevel(logging.INFO)
        logger.info("Running in UAT mode")
    else:  # $default or any other stage
        logger.setLevel(logging.INFO)
        logger.info("Running in DEFAULT/PRODUCTION mode")

    # Get the full rawPath and query parameters
    raw_path = event.get('rawPath', '')
    query_params = event.get('queryStringParameters', {}) or {}
    patient_id = query_params.get('patientId')
    quiz_type = query_params.get('type', 'personal')  # Default to 'personal' if not specified

    logger.info(f"Request path: {raw_path}")
    logger.info(f"Patient ID: {patient_id}")
    logger.info(f"Quiz Type: {quiz_type}")

    # Remove stage prefix and /quiz-api prefix to get the actual endpoint
    # Handles paths like: /dev/quiz-api/quiz, /uat/quiz-api/quiz, /quiz-api/quiz
    clean_path = raw_path
    # Remove stage prefix if present (dev, uat, or $default)
    for stage_prefix in ['/dev', '/uat', '/$default']:
        if clean_path.startswith(stage_prefix):
            clean_path = clean_path[len(stage_prefix):]
            break
    # Remove /quiz-api prefix if present
    if clean_path.startswith('/quiz-api'):
        clean_path = clean_path[9:]  # Remove '/quiz-api'

    logger.info(f"Clean path after removing prefixes: {clean_path}")

    # Define the paths for the different JSON files based on path and quiz type
    json_files = {
        '/quiz': {
            'personal': 'personal_quiz.json',
            'general': 'general_quiz.json'
        },
        '/progress': 'progress.json',
        '/avatar_feedback': 'avatar_feedback.json',
        '/insights': 'insights.json'
    }

    # Get the file path based on clean_path and quiz type
    if clean_path == '/quiz':
        file_name = json_files.get('/quiz', {}).get(quiz_type)
    else:
        file_name = json_files.get(clean_path)

    # Check if the path and file_name are valid
    if not file_name:
        # Log if an invalid path or type is provided
        logger.warning(f"Invalid path or quiz type provided. Raw path: {raw_path}, Clean path: {clean_path}, Quiz type: {quiz_type}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                "error": "Invalid path or quiz type. Please use '/quiz' with type 'personal' or 'general', or other valid paths."
            }),
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Stage': stage
            }
        }

    # Try to read the corresponding JSON file
    try:
        logger.info(f"Attempting to read file: {file_name}")
        with open(file_name, 'r') as file:
            data = json.load(file)
        
        # Check if the data is a list of questions
        if isinstance(data, list):
            random_question = random.choice(data)  # Select a random question from the list
        else:
            # If the data is not a list, return an error
            logger.error(f"Data in {file_name} is not a list of questions.")
            return {
                'statusCode': 500,
                'body': json.dumps({"error": "The JSON data is not in the expected format."}),
                'headers': {
                    'Content-Type': 'application/json',
                    'X-API-Stage': stage
                }
            }

        # Add patientId to response if available
        if patient_id:
            random_question['patientId'] = patient_id

        # Log the success of reading data
        logger.info(f"Successfully read data from {file_name}. Returning random question.")

        # Return the random question
        return {
            'statusCode': 200,
            'body': json.dumps(random_question),
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Stage': stage  # Add stage info to response headers
            }
        }

    except Exception as e:
        # Log the error message
        logger.error(f"Error reading file {file_name}: {str(e)}")
        
        # Return error response
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"Error reading file: {str(e)}"}),
            'headers': {
                'Content-Type': 'application/json',
                'X-API-Stage': stage
            }
        }
