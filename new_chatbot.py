from flask import Flask, request, jsonify, render_template
import uuid
from questions import questions_flow  # Import the questions flow from the separate file

app = Flask(__name__)

# Dictionary to hold user sessions and responses
user_sessions = {}

# Function to initialize a new user session
def initialize_session(user_id):
    print(f"Initializing session for user {user_id}")
    return {
        "step": "email",  # Ensure we start by asking for email
        "conversation": [],
        "email": None
    }

# Route for serving the frontend
@app.route('/')
def index():
    return render_template('new_chatbot.html')

# Endpoint for handling chat interaction
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '').strip().lower()  # Normalize user input (lowercase and strip whitespace)
    user_id = data.get('user_id', str(uuid.uuid4()))  # Generating a new user_id if not provided

    # Check if user has an existing session
    if user_id not in user_sessions:
        print(f"Starting a new session for {user_id}")
        user_sessions[user_id] = initialize_session(user_id)
        session = user_sessions[user_id]

        # Automatically prompt the first question (asking for email) as soon as the session starts
        first_question = questions_flow[session['step']]['question']
        print(f"Asking the first question: {first_question}")
        return jsonify({"response": first_question, "user_id": user_id})

    # Handle user input after the first prompt
    session = user_sessions[user_id]
    step = session['step']
    print(f"Current step for user {user_id}: {step}")

    # Process the current step
    current_question = questions_flow[step]

    # Ensure proper handling of options if any
    if 'options' in current_question and user_input not in [opt.lower() for opt in current_question['options']]:
        response = f"Please select a valid option: {', '.join(current_question['options'])}"
    else:
        # Save the user's response (handle multi-select as well)
        session['conversation'].append({"question": current_question["question"], "response": user_input})

        # If email step, capture the email
        if step == 'email':
            session['email'] = user_input

        # Determine the next step dynamically
        if isinstance(current_question['next'], dict):
            next_step = current_question['next'].get(user_input, "sorry")  # Get next step based on input
        else:
            next_step = current_question['next']

        # Update session to next step
        session['step'] = next_step
        print(f"Next step for user {user_id}: {next_step}")

        # Check if conversation is over
        if session['step'] is None:
            response = "Thank you for your responses. We will update your doctor."
            del user_sessions[user_id]  # Clear session after completing conversation
        else:
            next_question = questions_flow[session['step']]
            # Handle response with or without options
            if 'options' in next_question:
                response = f"{next_question['question']} Options: {', '.join(next_question['options'])}"
            else:
                response = next_question['question']

    return jsonify({"response": response, "user_id": user_id})

if __name__ == '__main__':
    app.run(debug=True)
