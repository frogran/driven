import os
import logging
from flask import Flask, render_template, request, redirect, url_for
import threading
import time
import openai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store submissions in memory (simple implementation)
text_submissions = []
api_output = ""

# Get OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

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

            # Call OpenAI API using the new ChatCompletion method
            with open("submissions.txt", "r") as current_file:
                input_text = current_file.read()
                logger.info(f"Input text for OpenAI: {input_text}")

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": input_text}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )

                api_output = response['choices'][0]['message']['content'].strip()
                logger.info(f"Received API output: {api_output}")

            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}")

            # Clear the in-memory submissions list for the next round
            text_submissions.clear()
            logger.info("Cleared text submissions.")

if __name__ == '__main__':
    # Start the background thread to process submissions
    thread = threading.Thread(target=process_submissions)
    thread.daemon = True  # Daemonize thread
    thread.start()
    
    # Start the Flask app
    app.run(debug=True)

