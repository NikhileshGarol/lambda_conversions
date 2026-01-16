import time

# Medical recommendation text
recommendation_lines = [
    "1. Dietary Habits:",
    " - What does a typical day of meals look like for you? Please describe your breakfast, lunch, dinner, and snacks.",
    " - Have you made any changes to your diet recently, such as reducing sugar or carbohydrate intake? If so, please describe.",
    " - Do you often experience symptoms like excessive thirst, frequent urination, or fatigue after eating?",
    "2. Physical Activity:",
    " - How many days per week do you engage in physical activity? What types of exercise do you prefer (e.g., walking, jogging, cycling)?",
    " - Have you experienced any physical symptoms during exercise, such as dizziness, unusual fatigue, or rapid heartbeat?",
    "3. Blood Sugar Monitoring:",
    " - How frequently do you monitor your blood glucose levels? What have your recent readings been?",
    " - Have you noticed any patterns in your blood sugar levels related to your meals, activities, or stress?",
    "4. Weight Management:",
    " - What is your current weight, and have you noticed any recent changes (gain or loss)?",
    " - Have you struggled with maintaining a healthy weight, and if so, what challenges have you faced?",
    "5. Medication Adherence:",
    " - Are you currently taking any medications for diabetes? If yes, are you adhering to your prescribed regimen?",
    " - Have you experienced any side effects or concerns related to your diabetes medications?",
    "6. Symptoms of Hyperglycemia and Hypoglycemia:",
    " - Have you ever experienced symptoms of high blood sugar (hyperglycemia), such as blurred vision, headaches, or extreme thirst?",
    " - Have you ever experienced low blood sugar (hypoglycemia)? If so, what symptoms did you notice (e.g., shakiness, sweating, confusion)?",
    "7. Stress and Mental Health:",
    " - How would you rate your stress levels on a scale from 1 to 10? What are the primary sources of stress in your life?",
    " - Have you noticed any changes in your mood or mental health that could affect your diabetes management, such as increased anxiety or depression?",
]

def get_recommendations(mobile_number):
    """
    Generates medical recommendations for a given patient and returns them as a dictionary.

    Args:
        mobile_number (str): Mobile number of the patient.

    Returns:
        dict: Recommendations wrapped in a Python dictionary.
    """
    recommendations = {
        "recommendations": []
    }
    
    for line in recommendation_lines:
        time.sleep(0.1)  # Simulating delay
        recommendations["recommendations"].append(line)

    return recommendations


