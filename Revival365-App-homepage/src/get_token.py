import requests

# Hardcoded credentials
EMAIL = "pythonapi@yopmail.com"
PASSWORD = "Stixis@123"

# Base URLs
LOGIN_URL = "https://devapi.revival365ai.com/admin/user/login"
GLUCOSE_CONFIG_URL = "https://devapi.revival365ai.com/user/getPatientGlucoseConfig"
TIMEZONE_URL = "https://devapi.revival365ai.com/timezone"


def get_access_token():
    """
    Fetch access token using hardcoded email and password.

    Returns:
    - str: Access token or None if login fails.
    """
    login_payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    try:
        # Perform login request
        login_response = requests.post(LOGIN_URL, json=login_payload)
        login_response.raise_for_status()

        login_data = login_response.json()

        if login_data.get("status") == 200:
            # Extract Access Token
            return login_data["content"]["accessToken"]
        else:
            print("❌ Login failed:", login_data)
            return None

    except requests.exceptions.RequestException as e:
        print("❌ Request failed:", str(e))
        return None


def get_patient_glucose_config(patient_id):
    """
    Fetch patient glucose configuration using a hardcoded email and password.
    
    Args:
    - patient_id (int): The patient ID to fetch glucose config.
    
    Returns:
    - dict: API response containing glucose configuration or error message.
    """
    access_token = get_access_token()

    if not access_token:
        return {"error": "Failed to get access token"}

    # Step 2: Fetch Patient Glucose Config
    api_url = f"{GLUCOSE_CONFIG_URL}/{patient_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # Perform API call to fetch glucose config
        api_response = requests.get(api_url, headers=headers)
        api_response.raise_for_status()
        return api_response.json()

    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "details": str(e)}


def get_user_timezone(patient_id):
    """
    Fetch user timezone configuration using user_id.

    Args:
    - user_id (int): The user ID to fetch timezone config.
    
    Returns:
    - dict: API response containing timezone details or error message.
    """
    access_token = get_access_token()

    if not access_token:
        return {"error": "Failed to get access token"}

    # Step 2: Fetch User Timezone
    api_url = f"{TIMEZONE_URL}/{patient_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # Perform API call to fetch timezone config
        api_response = requests.get(api_url, headers=headers)
        api_response.raise_for_status()
        return api_response.json()

    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "details": str(e)}


# Example usage
if __name__ == "__main__":
    patient_id = 132
    
    print("✅ Fetching Patient Glucose Config...")
    glucose_response = get_patient_glucose_config(patient_id)
    print(glucose_response)
    
    print("\n✅ Fetching User Timezone Config...")
    timezone_response = get_user_timezone(patient_id)
    print(timezone_response)
