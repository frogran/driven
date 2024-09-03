import os
import logging
import openai
from flask import Flask, render_template, request, session, redirect, url_for
import random
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for session management

participants = {}
reader_id = None

# Store submissions
text_submissions = []
all_submissions = []
api_output = ""
agent_role = "You are a blind choreographer that's given a 'prompt' to a dancer. The crowd is your eyes and it is giving you inputs about what is happening. Change what you planned to adapt the dance section according to what they see."

# Get OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


socketio = SocketIO(app, async_mode='eventlet')

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to the server'})

@socketio.on('set_reader')
def set_reader(data):
    global reader_id
    reader_id = data['reader_id']
    emit('reader_selected', {'reader_id': reader_id}, broadcast=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crowd', methods=['GET', 'POST'])
def crowd():
    session_id = session.get('id')
    if not session_id:
        session_id = str(random.randint(1000, 9999))
        session['id'] = session_id

    if request.method == 'POST':
        text = request.form.get('crowd_text')
        logger.info(f"Received submission: {text}")
        if text:
            text_submissions.append(text)
            all_submissions.append(text)
            participants[session_id] = {'submission': text}
            logger.info(f"Text submissions updated: {text_submissions}")
        return redirect(url_for('crowd'))
    return render_template('crowd.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global api_output
    global agent_role
    global reader_id
    if request.method == 'POST':
        reader_id = random.choice(list(participants.keys()))
        socketio.emit('reader_selected', {'reader_id': reader_id}, broadcast=True)
        if 'send_prompt' in request.form:
            combined_text = "\n".join(text_submissions)
            prompt = [
                {"role": "system", "content": agent_role},
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

    return render_template('admin.html', reader_id=reader_id, submissions=all_submissions, api_output=api_output, text_submissions=text_submissions)

@app.route('/dev', methods=['GET', 'POST'])
def dev():
    global api_output
    global agent_role
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'crowd':
            text = request.form.get('crowd_text')
            logger.info(f"Received submission: {text}")
            if text:
                text_submissions.append(text)
                all_submissions.append(text)
                logger.info(f"Text submissions updated: {text_submissions}")
        elif form_type == 'admin' and 'send_prompt' in request.form:
            combined_text = "\n".join(text_submissions)
            prompt = [
                {"role": "system", "content": agent_role},
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

    return render_template('dev.html', submissions=all_submissions, api_output=api_output, text_submissions=text_submissions)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
