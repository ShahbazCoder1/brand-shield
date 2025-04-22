import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
from difflib import SequenceMatcher
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    nltk.download('punkt')
    nltk.download('stopwords')
except Exception as e:
    print(f"Error downloading NLTK data: {e}")

def verify_product_content(url):
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    ]
    search_engines = [
        'https://www.google.com/search?q=',
        'https://www.bing.com/search?q='
    ]
    stop_words = set(stopwords.words('english'))

    def _get_headers():
        import random
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def get_page_content(url):
        try:
            response = requests.get(url, headers=_get_headers(), timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    def extract_content(html_content):
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else ""
        description = ""
        desc_selectors = ['meta[name="description"]', 'div[class*="description"]', 
                         'div[id*="description"]', 'p[class*="description"]']
        for selector in desc_selectors:
            elements = soup.select(selector)
            if elements:
                if selector.startswith('meta'):
                    description = elements[0].get('content', '')
                else:
                    description = elements[0].text.strip()
                break
        return {'title': title, 'description': description}

    def _search_web(query):
        results = []
        for engine in search_engines:
            try:
                search_url = engine + urllib.parse.quote(query)
                response = requests.get(search_url, headers=_get_headers(), timeout=10)
                if response.status_code == 200:
                    results.append(response.text)
                time.sleep(2)
            except Exception as e:
                print(f"Search error: {e}")
        return results

    def _get_significant_phrases(text, min_length=5, max_phrases=3):
        if not text:
            return []
        try:
            words = word_tokenize(text.lower())
        except LookupError as e:
            print(f"NLTK tokenization error: {e}")
            words = text.lower().split()
        except Exception as e:
            print(f"Error in tokenization: {e}")
            words = text.lower().split()
        try:
            filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        except Exception as e:
            print(f"Error filtering stop words: {e}")
            filtered_words = [word for word in words if word.isalnum()]
        phrases = []
        for i in range(len(filtered_words) - min_length + 1):
            phrase = ' '.join(filtered_words[i:i+min_length])
            phrases.append(phrase)
        if not phrases and filtered_words:
            phrases = [' '.join(filtered_words[:min(len(filtered_words), min_length)])]
        return phrases[:max_phrases]

    def check_text_originality(text):
        if not text or len(text.strip()) < 20:
            return {'score': 0.5, 'reason': "Text too short for meaningful originality check"}
        search_phrases = _get_significant_phrases(text)
        if not search_phrases:
            return {'score': 0.5, 'reason': "Could not extract meaningful phrases for searching"}
        matched_content = []
        highest_similarity = 0
        for phrase in search_phrases:
            search_results = _search_web(f'"{phrase}"')
            for result in search_results:
                soup = BeautifulSoup(result, 'html.parser')
                for script in soup(["script", "style"]):
                    script.extract()
                page_text = soup.get_text()
                similarity = SequenceMatcher(None, text.lower(), page_text.lower()).ratio()
                highest_similarity = max(highest_similarity, similarity)
                if similarity > 0.7:
                    matched_content.append({"phrase": phrase, "similarity": similarity})
        if matched_content:
            originality_score = max(0, 1 - highest_similarity)
            reason = f"Found {len(matched_content)} similar content matches online"
        else:
            originality_score = 0.9
            reason = "No significant matches found online"
        return {'score': originality_score, 'reason': reason, 'matches': matched_content}

    def calculate_trust_score(content):
        if not content:
            return {'overall_score': 0, 'reason': "Could not extract content"}
        results = {}
        if content.get('title'):
            results['title'] = check_text_originality(content['title'])
        if content.get('description'):
            results['description'] = check_text_originality(content['description'])
        weights = {'title': 0.4, 'description': 0.6}
        overall_score = 0
        score_components = []
        if 'title' in results:
            overall_score += results['title']['score'] * weights['title']
            score_components.append(f"Title: {results['title']['score']:.2f}")
        if 'description' in results:
            overall_score += results['description']['score'] * weights['description']
            score_components.append(f"Description: {results['description']['score']:.2f}")
        if overall_score > 0.8:
            trust_level = "High - Content appears to be original"
        elif overall_score > 0.6:
            trust_level = "Moderate - Some elements may be borrowed"
        elif overall_score > 0.4:
            trust_level = "Low - Multiple elements appear to be taken from elsewhere"
        else:
            trust_level = "Very low - Content likely copied from other sources"
        return {'overall_score': overall_score, 'trust_level': trust_level, 'component_scores': score_components, 'details': results}

    html_content = get_page_content(url)
    if not html_content:
        return {"error": "Could not fetch page content"}
    content = extract_content(html_content)
    if not content:
        return {"error": "Could not extract product content"}
    trust_score = calculate_trust_score(content)
    return {"url": url, "content_found": content, "trust_analysis": trust_score}

if __name__ == "__main__":
	product_url = "https://pypi.org/project/nltk/"
	result = verify_product_content(product_url)
	print(f"Trust score: {result['trust_analysis']['overall_score']:.2f}")
	print(f"Trust level: {result['trust_analysis']['trust_level']}")
	print("Component scores:")
	for component in result['trust_analysis']['component_scores']:
		print(f"- {component}")
