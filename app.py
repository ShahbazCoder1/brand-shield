from flask import Flask, render_template, request, jsonify
import os
from website_analyzer import analyze_website, get_overall_trust_score

app = Flask(__name__, static_folder='downloaded_images')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    url = request.json.get('url')
    if not url:
        return jsonify({
            'success': False,
            'error': 'URL is required'
        })
    
    try:
        # Analyze the website
        analysis_results = analyze_website(url)
        
        if not analysis_results.get('success'):
            return jsonify({
                'success': False,
                'error': analysis_results.get('error', 'Unknown error occurred')
            })
        
        # Get images and text
        images = analysis_results.get('extracted_content', {}).get('image_paths', [])
        priority_1_text = analysis_results.get('extracted_content', {}).get('priority_1', '')
        priority_2_text = analysis_results.get('extracted_content', {}).get('priority_2', '')
        
        # Calculate overall trust score
        overall_trust_score = get_overall_trust_score(analysis_results)
        
        # Format the response
        response = {
            'success': True,
            'url': url,
            'images': images,
            'priority_1': priority_1_text,
            'priority_2': priority_2_text,
            'overall_trust_score': overall_trust_score,
            'trust_level': get_trust_level(overall_trust_score),
            'analysis': {
                'ai_content': analysis_results.get('ai_analysis', {}),
                'text_originality': analysis_results.get('text_originality', {}).get('trust_analysis', {}),
                'image_analysis': analysis_results.get('image_analysis', [])
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_trust_level(score):
    """Convert numeric score to descriptive trust level"""
    if score >= 0.8:
        return "Very High - Content appears to be authentic"
    elif score >= 0.6:
        return "High - Content is mostly authentic"
    elif score >= 0.4:
        return "Moderate - Some authenticity concerns"
    elif score >= 0.2:
        return "Low - Multiple authenticity issues detected"
    else:
        return "Very Low - Content appears to be inauthentic"

if __name__ == '__main__':
    os.makedirs('downloaded_images/jpg_png', exist_ok=True)
    app.run(debug=True)
