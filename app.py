import os
import logging
from flask import Flask, render_template, request, redirect, url_for
import threading
import time
import openai

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store submissions in memory (simple implementation)
text_submissions = []
api_output = ""

# Get OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API Key: {openai.api_key[:4]}...")  # Log the first few characters to confirm it's set

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crowd', methods=['GET', 'POST'])
def crowd():
    global api_output
    if request.method == 'POST':
        text = request.form.get('crowd_text')
        logger.info(f"Received submission: {text}")
        if text:
            text_submissions.append(text)
            logger.info(f"Text submissions updated: {text_submissions}")
        return redirect(url_for('crowd'))
    logger.info(f"Rendering crowd page with API output: {api_output}")
    return render_template('crowd.html', api_output=api_output)

@app.route('/admin')
def admin():
    logger.info(f"Rendering admin page with submissions: {text_submissions}")
    return render_template('admin.html', submissions=text_submissions)

def process_submissions():
    logger.info("Started process_submissions thread.")
    global api_output
    while True:
        time.sleep(60)  # Wait for 1 minute
        if text_submissions:
            logger.info(f"Processing submissions: {text_submissions}")
            # Append new submissions to all_submissions.txt
            with open("all_submissions.txt", "a") as all_file:
                for submission in text_submissions:
                    all_file.write(submission + "\n")

            # Write current round submissions to submissions.txt
            with open("submissions.txt", "w") as current_file:
                for submission in text_submissions:
                    current_file.write(submission + "\n")

            # Prepare the input text for OpenAI
            with open("submissions.txt", "r") as current_file:
                input_text = current_file.read()
                logger.info(f"Input text for OpenAI: {input_text}")

            # Define the prompt and log it
            prompt = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": input_text}
            ]
            logger.info(f"Prompt sent to OpenAI: {prompt}")


	    try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=prompt,
                    max_tokens=100,
                    temperature=0.7
                )
                api_output = response['choices'][0]['message']['content'].strip()
                logger.info(f"API output received: {api_output}")
            except Exception as e:
   	        logger.error(f"Error calling OpenAI API: {e}")
   	        api_output = "There was an error processing the request."
            
            # Clear the in-memory submissions list for the next round
            text_submissions.clear()
            logger.info("Cleared text submissions.")

if __name__ == '__main__':
    # Start the background thread to process submissions
    thread = threading.Thread(target=process_submissions)
    thread.daemon = True  # Daemonize thread
    thread.start()
    
    # Start the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
