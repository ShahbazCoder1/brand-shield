from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    url = request.form.get('url')
    # Here you can add logic to process the URL
    # For now, we'll just print it and redirect back to the home page
    print(f"Received URL: {url}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
