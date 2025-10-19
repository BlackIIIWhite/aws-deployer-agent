# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import json # Ensure json is imported for s3 policy

app = Flask(__name__)
# CORS allows your frontend (running on a different origin) to call this backend
CORS(app)

# --- IMPORTANT: UPDATE THESE VALUES ---
# Paste the IDs you received after running the setup.py script.
AGENT_ID = "UURDQW5DTE"
AGENT_ALIAS_ID = "1DIM83KAIA"
REGION = "us-east-1" 

# Initialize the Boto3 client for the Bedrock Agent Runtime
# This client is specifically for invoking and interacting with agents.
bedrock_agent_runtime_client = boto3.client(
    'bedrock-agent-runtime',
    region_name=REGION
)

# Initialize the Boto3 client for S3
# This client is used by the /upload-files endpoint
s3_client = boto3.client('s3', region_name=REGION)

@app.route('/invoke-agent', methods=['POST'])
def invoke_agent():
    """
    Receives a prompt from the frontend and invokes the Bedrock Agent.
    """
    data = request.get_json()
    user_prompt = data.get('prompt')
    # The session ID helps the agent remember the context of the conversation
    session_id = data.get('sessionId', 'default-session')

    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        # Invoke the agent with the user's prompt
        response = bedrock_agent_runtime_client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=user_prompt
        )

        # The response from the agent is a stream of events.
        # We need to read this stream to get the final text response.
        event_stream = response['completion']
        agent_response = ""
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                # Decode the chunk of bytes and add it to our full response
                agent_response += chunk['bytes'].decode('utf-8')

        # Return the complete response from the agent to the frontend
        return jsonify({"response": agent_response})

    except Exception as e:
        # Print the error to the console for debugging
        print(f"Error invoking agent: {e}")
        # Return a generic error message to the frontend
        return jsonify({"error": f"Failed to get response from agent: {str(e)}"}), 500

@app.route('/upload-files', methods=['POST'])
def handle_upload():
    """
    Receives files and a bucket name from the frontend and uploads them to S3.
    """
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files') # Get list of files uploaded
    bucket_name = request.form.get('bucketName') # Get bucket name from form data

    if not bucket_name:
         return jsonify({"error": "Bucket name is required"}), 400
    if not files or files[0].filename == '':
        return jsonify({"error": "No selected files"}), 400

    uploaded_count = 0
    errors = []

    for file in files:
        if file and file.filename: # Check if file object and filename exist
            try:
                # Basic Content-Type detection based on extension
                content_type = 'application/octet-stream' # Default
                if file.filename.endswith('.html'):
                    content_type = 'text/html'
                elif file.filename.endswith('.css'):
                    content_type = 'text/css'
                elif file.filename.endswith('.js'):
                    content_type = 'application/javascript'
                elif file.filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Add more image types if needed
                    content_type = f'image/{file.filename.split(".")[-1]}'

                # Upload the file object directly to S3
                s3_client.upload_fileobj(
                    file,                   # The file object stream from Flask request
                    bucket_name,            # Target S3 bucket name
                    file.filename,          # Use the original filename as the S3 object key
                    ExtraArgs={
                        # 'ACL': 'public-read', # Make files publicly readable for website hosting
                        'ContentType': content_type
                        }
                )
                uploaded_count += 1
            except Exception as e:
                print(f"Error uploading {file.filename}: {e}")
                errors.append(f"Failed to upload {file.filename}: {str(e)}")

    if errors:
        return jsonify({
            "message": f"Completed with errors. Uploaded {uploaded_count} files.",
            "errors": errors
        }), 500
    else:
        return jsonify({"message": f"Successfully uploaded {uploaded_count} files to {bucket_name}."}), 200

if __name__ == '__main__':
    # Run the Flask app on port 5001 in debug mode
    # debug=True allows automatic reloading when you save changes
    app.run(debug=True, port=5001)
    
    
    
    
    
    
    
