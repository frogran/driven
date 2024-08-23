import os
import logging
from flask import Flask, render_template, request, redirect, url_for
import openai

app = Flask(__name__)

# Store submissions
text_submissions = []
all_submissions = []
api_output = ""

# Get OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crowd', methods=['GET', 'POST'])
def crowd():
    if request.method == 'POST':
        text = request.form.get('crowd_text')
        logger.info(f"Received submission: {text}")
        if text:
            text_submissions.append(text)
            all_submissions.append(text)
            logger.info(f"Text submissions updated: {text_submissions}")
        return redirect(url_for('crowd'))
    return render_template('crowd.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global api_output
    if request.method == 'POST':
        if 'send_prompt' in request.form:
            combined_text = "\n".join(text_submissions)
            prompt = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": combined_text}
            ]
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
            text_submissions.clear()

    return render_template('admin.html', submissions=all_submissions, api_output=api_output)

@app.route('/dev')
def dev():
    return render_template('dev.html', submissions=all_submissions, api_output=api_output, text_submissions=text_submissions)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
