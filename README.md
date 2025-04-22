# Brand Shield Application

Brand Shield is a powerful Flask application that analyzes e-commerce websites and product listings for authenticity. It helps detect AI-generated content, fake product images, and plagiarized text to protect brands and consumers from counterfeit products.

## Features

- **AI Content Detection**: Analyzes product descriptions and titles for signs of AI-generated content
- **Image Authentication**: Verifies product images for manipulation or theft using reverse image search and metadata analysis
- **Text Originality Verification**: Checks text content against online sources to detect plagiarism
- **Comprehensive Website Analysis**: Provides an overall trust score based on multiple authenticity factors
- **Clean User Interface**: Simple interface built with Tailwind CSS for easy submission and result display

## Setup

### Prerequisites

- Python 3.6+ installed
- Chrome browser installed (for Selenium)
- Internet connection for web scraping and analysis

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/brand-shield.git
   cd brand-shield
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirments.txt
   ```

4. Download NLTK data (required for text analysis):
   ```python
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

### Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

3. Enter a website URL in the form and submit for analysis

## How It Works

Brand Shield uses a combination of techniques to analyze e-commerce content:

1. **Web Scraping**: Extracts product information, images, and text from the target website
2. **AI Detection**: Uses linguistic patterns and statistical analysis to identify AI-generated content
3. **Image Analysis**: Performs reverse image searches, metadata analysis, and manipulation detection
4. **Text Verification**: Searches the web for similar content to detect plagiarism
5. **Trust Score Calculation**: Combines all factors to produce an overall assessment of authenticity

## Project Structure

- `app.py`: Main Flask application
- `ai_detector.py`: AI content detection algorithms
- `image_finder.py`: Image analysis and authenticity verification
- `text_finder.py`: Text originality checking
- `scraper.py`: Web scraping utilities
- `website_analyzer.py`: Combines all analyses into overall assessment

## License

[Your license information here]

## Contributors

[Your name/team information]
