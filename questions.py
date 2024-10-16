# questions.py

questions_flow = {
    "email": {
        "question": "Enter your email ID.",  # Email is asked first
        "next": "name"
    },
    "name": {
        "question": "Confirm your name.",
        "next": "age"
    },
    "age": {
        "question": "What is your age?",
        "next": "gender"
    },
    "gender": {
        "question": "What is your gender?",
        "next": "diabetes"
    },
    "diabetes": {
        "question": "Are you suffering from diabetes?",
        "options": ["Yes", "No"],  # Define Yes/No options
        "next": {
            "yes": "diabetes_type",  # Go to "diabetes_type" question if "Yes"
            "no": "sorry"  # End conversation if "No"
        }
    },
    "diabetes_type": {
        "question": "Do you have Type 1 or Type 2 diabetes?",
        "options": ["Type 1", "Type 2"],  # Define Type 1/Type 2 options
        "next": "symptoms"  # After diabetes_type, proceed to symptoms
    },
    "symptoms": {
        "question": "Please select your symptoms (you can select multiple):",
        "options": [
            "Frequent urination", "Increased thirst", "Fatigue", "Blurred vision", "Slow-healing wounds",
            "Unexplained weight loss", "Frequent infections", "Shakiness or tremors", "Sweating", "Hunger",
            "Irritability or anxiety", "Dizziness or lightheadedness", "Confusion", "Headaches", "Paleness",
            "Seizures or loss of consciousness"
        ],
        "next": "smoker"
    },
    "smoker": {
        "question": "Are you a smoker?",
        "options": ["Yes", "No"],
        "next": "hypertension"
    },
    "hypertension": {
        "question": "Do you have hypertension or High BP?",
        "options": ["Yes", "No"],
        "next": "heart_problems"
    },
    "heart_problems": {
        "question": "Have you had heart-related problems?",
        "options": ["Yes", "No"],
        "next": "aspirin"
    },
    "aspirin": {
        "question": "Do you take aspirin?",
        "options": ["Yes", "No"],
        "next": "weight"
    },
    "weight": {
        "question": "What is your weight?",
        "next": "height"
    },
    "height": {
        "question": "What is your height?",
        "next": "low_blood_sugar"
    },
    "low_blood_sugar": {
        "question": "Do you experience low blood sugar?",
        "options": ["Yes", "No"],
        "next": "sleep_issues"
    },
    "sleep_issues": {
        "question": "Do you have sleep-related issues?",
        "options": ["Yes", "No"],
        "next": "examinations"
    },
    "examinations": {
        "question": "Have you had any of the following examinations in the last year?",
        "options": ["Eye check-up", "Foot examination", "Dental examination","No"],
        "next": "prescriptions"
    },
    "prescriptions": {
        "question": "Can you upload your prescriptions?",
        "options": ["Yes", "No"],
        "next": "medical_reports"
    },
    "medical_reports": {
        "question": "Can you upload your medical reports?",
        "options": ["Yes", "No"],
        "next": "thank_you"
    },
    "thank_you": {
        "question": "Thank you for your responses. We will update your doctor.",
        "next": None  # End of conversation
    },
    "sorry": {
        "question": "Sorry, we are only serving diabetics currently.",
        "next": None  # End conversation for non-diabetic users
    }
}
