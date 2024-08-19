from flask import Flask, render_template, request, redirect, url_for

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

if __name__ == '__main__':
    app.run(debug=True)

