import requests
from datetime import datetime, timedelta, timezone

EMAIL = "pythonapi@yopmail.com"
PASSWORD = "Stixis@123"
LOGIN_URL = "https://devapi.revival365ai.com/admin/user/login"

# Define IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_access_token():
    login_payload = {"email": EMAIL, "password": PASSWORD}
    try:
        response = requests.post(LOGIN_URL, json=login_payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 200 and "accessToken" in data.get("content", {}):
            return data["content"]["accessToken"]
    except requests.exceptions.RequestException as e:
        print("❌ Login failed:", e)
    return None


def get_cgm_days(user_id):
    token = get_access_token()
    if not token:
        return "Error: Access token retrieval failed"

    api_url = f"https://devapi.revival365ai.com/plan/sessionStartDate/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
    except (requests.RequestException, ValueError):
        return "Error fetching data"

    # Validate API response
    if data.get("status") != 200 or not data.get("content"):
        return "null"

    try:
        # Convert API date string to datetime and set IST timezone
        activation_datetime = datetime.strptime(data["content"], "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    except ValueError:
        return "Invalid date format in API response"

    expiration_datetime = activation_datetime + timedelta(days=15)
    current_datetime = datetime.now(IST)

    # If session is expired
    if current_datetime >= expiration_datetime:
        return "Expired"

    # Calculate remaining time
    time_left = expiration_datetime - current_datetime
    days_left = time_left.total_seconds() / 86400  # seconds in a day

    if days_left >= 1:
        return f"{int(days_left) + 1} days left"
    else:
        hours_left = time_left.total_seconds() // 3600
        return f"{int(hours_left)} hours left" if hours_left >= 1 else "1 hour left"


# Example usage
if __name__ == "__main__":
    user_id = 111
    print("⏳ CGM Time Left:", get_cgm_days(user_id))
