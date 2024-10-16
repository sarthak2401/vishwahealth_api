from flask import Flask, request, jsonify, render_template
import os
import json
from google.cloud import storage
import uuid
import datetime

app = Flask(__name__)

# Setting up the conversation flow, starting with email
questions = [
    "What is your email address?",
    "What is your name?",
    "What is your primary disease?",
    "Do you have a family history?",
]

# Dictionary to hold user sessions and responses
user_sessions = {}


# Function to initialize a new user session
def initialize_session(user_id):
    return {
        "step": 0,
        "conversation": [],
        "email": None  # To store the email for file naming
    }


# Route for serving the frontend
@app.route('/')
def index():
    return render_template('chatbot.html')


# Endpoint for handling chat interaction
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    user_id = data.get('user_id', str(uuid.uuid4()))  # Generating a new user_id if not provided

    # Check if user has an existing session
    if user_id not in user_sessions:
        user_sessions[user_id] = initialize_session(user_id)

    session = user_sessions[user_id]
    step = session['step']

    # Start asking questions
    if step == 0:
        # First question: Ask for the email address
        if user_input.strip() == "":  # Check if this is the first interaction
            response = "What is your email address?"  # Ask for email address
        else:
            # Store the email
            session['email'] = user_input
            session['conversation'].append({"question": "What is your email address?", "response": user_input})
            session['step'] += 1  # Move to the next step
            response = questions[1]  # Ask for name
    else:
        # For all other questions
        session['conversation'].append({"question": questions[step], "response": user_input})
        session['step'] += 1

        # If all questions are answered, log and save the conversation
        if step >= len(questions) - 1:
            response = "Thank you! Your information has been saved."
            log_conversation_to_gcs(user_id, session['email'], session['conversation'])
            del user_sessions[user_id]  # Clear session after completing conversation
        else:
            # Ask the next question
            response = questions[session['step']]

    return jsonify({"response": response, "user_id": user_id})


# Function to log conversation and upload to Google Cloud Storage
def log_conversation_to_gcs(user_id, email, conversation):
    # Extract username from email
    username = email.split('@')[0]

    # Generate a timestamp for file naming
    timestamp = datetime.datetime.now().strftime('%Y%m%d')

    # Create a structured log in JSON format
    log_data = {
        "user_id": user_id,
        "email": email,
        "timestamp": str(datetime.datetime.now()),
        "conversation": conversation
    }

    # Create the file name in the format username_timestamp.json
    log_filename = f"{username}_{timestamp}.json"

    # Save log file locally
    with open(log_filename, 'w') as f:
        json.dump(log_data, f)

    # Upload log file to GCS
    upload_to_gcs(log_filename)

    # Remove the local file after uploading
    os.remove(log_filename)


def upload_to_gcs(filename):
    bucket_name = "user-chat-log"  # Replace with your GCS bucket name
    #client = storage.Client()
    client = storage.Client.from_service_account_json("/Users/sarthakagarwal/Downloads/health-management-438009-f73296f7cb5e.json")

    bucket = client.get_bucket(bucket_name)
    print("The bucket is ",bucket)
    blob = bucket.blob(f'logs/{filename}')

    blob.upload_from_filename(filename)
    print(f"Uploaded {filename} to GCS bucket {bucket_name}")

if __name__ == '__main__':
    app.run(debug=True)
