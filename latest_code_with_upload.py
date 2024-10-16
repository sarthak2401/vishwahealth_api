from flask import Flask, request, jsonify, render_template
import uuid
import json
import os
import datetime
from google.cloud import storage  # GCP Storage
from questions import questions_flow  # Import the questions flow from the separate file
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json(
    '/Users/sarthakagarwal/Downloads/health-management-438009-f73296f7cb5e.json')  # Replace with your GCS credentials
bucket_name_logs = "user-chat-log"  # Bucket for saving chatbot logs

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
    return render_template('upload_chatbot.html')


# Endpoint for handling chat interaction
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '').strip().lower()  # Normalize user input (lowercase and strip whitespace)
    user_id = data.get('user_id', str(uuid.uuid4()))  # Generate a new user_id if not provided

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

        # Check if conversation is over or we are at the 'thank_you' step
        if session['step'] is None or session['step'] == 'thank_you':
            response = "Thank you for your responses. We will update your doctor."
            # Log conversation to GCS
            try:
                log_conversation_to_gcs(user_id, session['email'], session['conversation'])
            except Exception as e:
                app.logger.error(f"Failed to log conversation to GCS: {e}")
            del user_sessions[user_id]  # Clear session after completing conversation
        else:
            next_question = questions_flow[session['step']]
            # Handle response with or without options
            if 'options' in next_question:
                response = f"{next_question['question']} Options: {', '.join(next_question['options'])}"
            else:
                response = next_question['question']

    return jsonify({"response": response, "user_id": user_id})


# Function to log conversation and upload to Google Cloud Storage (GCS)
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

    # Upload the conversation log to GCS
    app.logger.debug(f"Attempting to upload conversation log for {user_id} to GCS.")
    upload_to_gcs(log_filename, log_data, bucket_name_logs)

# Function to upload the conversation log to GCS
def upload_to_gcs(filename, data, bucket_name):
    try:
        # Convert data to JSON string
        json_data = json.dumps(data)

        # Upload to GCS
        app.logger.debug(f"Connecting to GCS bucket: {bucket_name}")
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f'logs/{filename}')
        blob.upload_from_string(json_data, content_type='application/json')

        app.logger.debug(f"Uploaded {filename} to GCS bucket {bucket_name}")
    except Exception as e:
        app.logger.error(f"Error uploading conversation log to GCS: {e}")
        raise


# Endpoint to handle file uploads (prescriptions, medical reports)
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')  # Extract the file from the request
    user_id = request.form.get('user_id')  # Extract the user_id from the form

    # Log the file and user_id to confirm they were received
    app.logger.debug(f"Received file: {file}")
    app.logger.debug(f"Received user_id: {user_id}")

    if not file:
        app.logger.error("File missing!")
    if not user_id:
        app.logger.error("user_id missing!")

    if file and user_id:
        try:
            # Log the file and filename details before upload
            app.logger.debug(f"Preparing to upload file: {file.filename} for user: {user_id}")

            # Generate a unique filename
            filename = f"{user_id}_{file.filename}"

            # Log the target GCS path
            app.logger.debug(f"Target GCS path: uploads/{filename}")

            # Upload file to the GCS bucket for files
            upload_file_to_gcs(file, filename, bucket_name_files)

            app.logger.debug(f"File {file.filename} uploaded successfully to GCS.")
            return jsonify({"response": f"File {file.filename} uploaded successfully.", "user_id": user_id})
        except Exception as e:
            app.logger.error(f"File upload failed: {e}")
            return jsonify({"response": "File upload failed.", "user_id": user_id}), 500
    else:
        app.logger.warning("No file or user_id provided.")
        return jsonify({"response": "No file or user_id provided.", "user_id": user_id}), 400

# Function to upload the file to GCS bucket
def upload_file_to_gcs(file, filename, bucket_name):
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f'uploads/{filename}')

        # Log before starting the file upload
        app.logger.debug(f"Uploading file to GCS: {filename}")

        blob.upload_from_file(file.stream)  # Upload the file stream directly

        # Log successful upload
        app.logger.debug(f"File {filename} uploaded to GCS bucket {bucket_name}.")
    except Exception as e:
        app.logger.error(f"Error uploading file to GCS: {e}")
        raise


if __name__ == '__main__':
    app.run(debug=True)
