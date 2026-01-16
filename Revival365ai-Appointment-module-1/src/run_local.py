import json
from lambda_function import lambda_handler

# Load the test event
with open('event.json') as f:
    event = json.load(f)

# Call the real lambda handler with the full event
result = lambda_handler(event, None)
print('\nResult (API response):')
try:
    print(json.dumps(result, indent=2))
except Exception:
    print(result)