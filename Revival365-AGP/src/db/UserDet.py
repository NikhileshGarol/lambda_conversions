from db.db_connection import Session, User, Medications
from sqlalchemy.orm import joinedload

def fetch_patient_details(mobile_number):
    """
    Fetch the user ID associated with a given mobile number.

    Args:
        mobile_number (str): The mobile number to search.

    Returns:
        tuple: A tuple containing the user ID (or None if not found) and an error message (or None if no error).
    """
    session = Session()
    try:
        # Fetch the user ID by matching the mobile number in the User table
        user_id = (
            session.query(User.id)  # Select the User ID
            .filter(User.mobile_number == mobile_number)
            .scalar()
        )
         
        if user_id is None:
            return None, "No user found associated with this mobile number"

        return user_id, None
    except Exception as e:
        print(f"An error occurred while fetching user details: {e}")
        return None, "Error fetching user details"
    finally:
        session.close()


def fetch_user_details(mobile_number):
    """
    Fetch the user details based on the mobile number, including personal details.

    Args:
        mobile_number (str): The mobile number to search.

    Returns:
        dict: A dictionary of user details, or None if the user is not found or an error occurs.
    """
    session = Session()
    try:
        # Fetch the user based on the mobile number
        user = (
            session.query(User)
            .filter(User.mobile_number == mobile_number)
            .one_or_none()
        )
        
        if user is None:
            return None  # No user found

        # Return a dictionary of user details
        return {
            "id": user.id,          # User ID
            "first_name": user.first_name,
            "last_name": user.last_name,
            # Add other fields as necessary
        }
    except Exception as e:
        print(f"An error occurred while fetching user details: {e}")
        return None  # Return None on exception
    finally:
        session.close()


def fetch_medication_details(patient_id):
    """
    Retrieve medication details associated with a user.

    Args:
        patient_id (int): The ID of the user.

    Returns:
        tuple: A tuple containing a list of medication dictionaries and an error message, if any.
    """
    session = Session()
    try:
        medications = (
            session.query(Medications)
            .filter(Medications.patient_id == patient_id)
            .all()
        )

        # Create a list of medication details
        medication_list = [
            {
                "medication_name": med.medication_name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "note": med.note,
            }
            for med in medications
        ]

        return medication_list, None  # Return medications and no error
    except Exception as e:
        print(f"An error occurred while fetching medication details: {e}")
        return [], str(e)  # Return empty list and the error message
    finally:
        session.close()
