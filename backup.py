from flask import Flask, request, jsonify,render_template
import os
import json
from google.cloud import storage
import uuid
import datetime

app = Flask(__name__)

# Setting up the conversation flow
questions = [
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
        "conversation": []
    }

# Route for the home page
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

    # Save user input in conversation log
    if step > 0:
        session['conversation'].append({"question": questions[step - 1], "response": user_input})

    # If there are more questions to ask, ask the next one
    if step < len(questions):
        response = questions[step]
        session['step'] += 1
    else:
        # No more questions; upload the conversation log to GCS
        response = "Thank you! Your information has been saved."
        log_conversation_to_gcs(user_id, session['conversation'])
        del user_sessions[user_id]  # Clear session after completing conversation

    return jsonify({"response": response, "user_id": user_id})

# Route to handle favicon.ico requests (optional)
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return an empty response with 204 status

# Function to log conversation and upload to Google Cloud Storage
def log_conversation_to_gcs(user_id, conversation):
    # Create a structured log in JSON format
    log_data = {
        "user_id": user_id,
        "timestamp": str(datetime.datetime.now()),
        "conversation": conversation
    }

    # Save log file locally
    log_filename = f"{user_id}.json"
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
