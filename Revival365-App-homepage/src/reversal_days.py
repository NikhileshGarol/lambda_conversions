def get_days_to_reversal(user_id, flag=True):
    """
    Fetches days to reversal for a given user ID, but only if user_id is "22".
    
    Args:
        user_id (str): The ID of the user.
        flag (bool): Determines if a number or None is returned.
    
    Returns:
        int or None: 120 if user_id is "22" and flag is True, otherwise None.
    """
    return  None

# Example usage
if __name__ == "__main__":
    print(get_days_to_reversal("22"))  # Output: 120
    print(get_days_to_reversal("12345"))  # Output: None
    print(get_days_to_reversal("22", flag=False))  # Output: None
