from flask import Flask, render_template, request, redirect, url_for
import threading
import time

app = Flask(__name__)

# Store submissions in memory (simple implementation)
text_submissions = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crowd', methods=['GET', 'POST'])
def crowd():
    if request.method == 'POST':
        text = request.form.get('crowd_text')
        if text:
            text_submissions.append(text)
        return redirect(url_for('crowd'))
    return render_template('crowd.html')

@app.route('/admin')
def admin():
    return render_template('admin.html', submissions=text_submissions)

def write_and_clear_submissions():
    while True:
        time.sleep(60)  # Wait for 1 minute
        if text_submissions:
            with open("submissions.txt", "a") as f:
                for submission in text_submissions:
                    f.write(submission + "\n")
            text_submissions.clear()

if __name__ == '__main__':
    # Start the background thread to write and clear submissions
    thread = threading.Thread(target=write_and_clear_submissions)
    thread.daemon = True  # Daemonize thread
    thread.start()
    
    # Start the Flask app
    app.run(debug=True)

