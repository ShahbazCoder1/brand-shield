from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from extract_images_and_text import extract_images_and_text

app = Flask(__name__, static_folder='downloaded_images')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    url = request.form.get('url')
    try:
        # Process the URL with our extraction function
        extract_images_and_text(url)
        
        # Read the extracted text files
        priority_1_text = ""
        priority_2_text = ""
        
        if os.path.exists("priority_1.txt"):
            with open("priority_1.txt", "r", encoding="utf-8") as f:
                priority_1_text = f.read()
                
        if os.path.exists("priority_2.txt"):
            with open("priority_2.txt", "r", encoding="utf-8") as f:
                priority_2_text = f.read()
        
        # Get image file paths
        image_folder = os.path.join("downloaded_images", "jpg_png")
        images = []
        if os.path.exists(image_folder):
            images = [f"/downloaded_images/jpg_png/{img}" for img in os.listdir(image_folder) 
                     if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        return render_template('results.html', 
                            url=url,
                            priority_1=priority_1_text, 
                            priority_2=priority_2_text, 
                            images=images)
    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/process', methods=['POST'])
def process():
    url = request.json.get('url')
    try:
        # Process the URL with our extraction function
        extract_images_and_text(url)
        
        # Read the extracted text files
        priority_1_text = ""
        priority_2_text = ""
        
        if os.path.exists("priority_1.txt"):
            with open("priority_1.txt", "r", encoding="utf-8") as f:
                priority_1_text = f.read()
                
        if os.path.exists("priority_2.txt"):
            with open("priority_2.txt", "r", encoding="utf-8") as f:
                priority_2_text = f.read()
        
        # Get image file paths
        image_folder = os.path.join("downloaded_images", "jpg_png")
        images = []
        if os.path.exists(image_folder):
            images = [f"/downloaded_images/jpg_png/{img}" for img in os.listdir(image_folder) 
                     if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        return jsonify({
            'success': True,
            'priority_1': priority_1_text,
            'priority_2': priority_2_text,
            'images': images
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
