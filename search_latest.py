import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
from difflib import SequenceMatcher
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download necessary NLTK data - adding 'punkt' download explicitly
try:
    nltk.download('punkt')
    nltk.download('stopwords')
except Exception as e:
    print(f"Error downloading NLTK data: {e}")

class ContentVerifier:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        ]
        self.search_engines = [
            'https://www.google.com/search?q=',
            'https://www.bing.com/search?q='
        ]
        self.stop_words = set(stopwords.words('english'))
        
    def _get_headers(self):
        """Return random user agent headers to avoid blocking"""
        import random
        return {
            'User-Agent': random.choice(self.user_agents),
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
    
    def get_page_content(self, url):
        """Fetch the webpage content"""
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None
    
    def extract_content(self, html_content):
        """Extract product information from HTML content"""
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title (different sites may require different selectors)
        title = soup.title.string if soup.title else ""
        
        # Try to find product description
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
        
        return {
            'title': title,
            'description': description
        }
    
    def _search_web(self, query):
        """Search for content on the web"""
        results = []
        
        for engine in self.search_engines:
            try:
                search_url = engine + urllib.parse.quote(query)
                response = requests.get(search_url, headers=self._get_headers(), timeout=10)
                if response.status_code == 200:
                    results.append(response.text)
                # Be nice to search engines
                time.sleep(2)
            except Exception as e:
                print(f"Search error: {e}")
                
        return results
    
    def _get_significant_phrases(self, text, min_length=5, max_phrases=3):
        """Extract meaningful phrases from text for searching"""
        if not text:
            return []
            
        try:
            # Tokenize and remove stop words
            words = word_tokenize(text.lower())
        except LookupError as e:
            # Fall back to simple word splitting if NLTK tokenization fails
            print(f"NLTK tokenization error: {e}")
            words = text.lower().split()
        except Exception as e:
            print(f"Error in tokenization: {e}")
            words = text.lower().split()
            
        # Filter stop words if available
        try:
            filtered_words = [word for word in words if word.isalnum() and word not in self.stop_words]
        except Exception as e:
            print(f"Error filtering stop words: {e}")
            filtered_words = [word for word in words if word.isalnum()]
        
        # Create phrases (sliding window)
        phrases = []
        for i in range(len(filtered_words) - min_length + 1):
            phrase = ' '.join(filtered_words[i:i+min_length])
            phrases.append(phrase)
        
        # If no phrases were created but we have some words, use the words
        if not phrases and filtered_words:
            phrases = [' '.join(filtered_words[:min(len(filtered_words), min_length)])]
        
        # Return top phrases (by word significance)
        return phrases[:max_phrases]
    
    def check_text_originality(self, text):
        """Check if text content appears elsewhere on the web"""
        if not text or len(text.strip()) < 20:  # Too short to meaningfully check
            return {
                'score': 0.5,  # Neutral score
                'reason': "Text too short for meaningful originality check"
            }
        
        # Get search phrases from the text
        search_phrases = self._get_significant_phrases(text)
        if not search_phrases:
            return {
                'score': 0.5,
                'reason': "Could not extract meaningful phrases for searching"
            }
        
        # Search for each phrase
        matched_content = []
        highest_similarity = 0
        
        for phrase in search_phrases:
            search_results = self._search_web(f'"{phrase}"')  # Exact match search with quotes
            
            for result in search_results:
                soup = BeautifulSoup(result, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text content
                page_text = soup.get_text()
                
                # Check similarity
                similarity = SequenceMatcher(None, text.lower(), page_text.lower()).ratio()
                highest_similarity = max(highest_similarity, similarity)
                
                if similarity > 0.7:  # High similarity threshold
                    matched_content.append({"phrase": phrase, "similarity": similarity})
        
        # Calculate originality score (0 = likely copied, 1 = likely original)
        if matched_content:
            originality_score = max(0, 1 - highest_similarity)
            reason = f"Found {len(matched_content)} similar content matches online"
        else:
            originality_score = 0.9  # Likely original
            reason = "No significant matches found online"
        
        return {
            'score': originality_score,
            'reason': reason,
            'matches': matched_content
        }
    
    def calculate_trust_score(self, content):
        """Calculate overall trust score for product content"""
        if not content:
            return {
                'overall_score': 0,
                'reason': "Could not extract content"
            }
        
        results = {}
        
        # Check title
        if content.get('title'):
            results['title'] = self.check_text_originality(content['title'])
        
        # Check description
        if content.get('description'):
            results['description'] = self.check_text_originality(content['description'])
        
        # Calculate weighted overall score
        weights = {
            'title': 0.4,
            'description': 0.6
        }
        
        overall_score = 0
        score_components = []
        
        if 'title' in results:
            overall_score += results['title']['score'] * weights['title']
            score_components.append(f"Title: {results['title']['score']:.2f}")
            
        if 'description' in results:
            overall_score += results['description']['score'] * weights['description']
            score_components.append(f"Description: {results['description']['score']:.2f}")
        
        # Interpret score
        if overall_score > 0.8:
            trust_level = "High - Content appears to be original"
        elif overall_score > 0.6:
            trust_level = "Moderate - Some elements may be borrowed"
        elif overall_score > 0.4:
            trust_level = "Low - Multiple elements appear to be taken from elsewhere"
        else:
            trust_level = "Very low - Content likely copied from other sources"
        
        return {
            'overall_score': overall_score,
            'trust_level': trust_level,
            'component_scores': score_components,
            'details': results
        }

# Example usage function
def verify_product_content(url):
    verifier = ContentVerifier()
    
    # Get and extract content
    html_content = verifier.get_page_content(url)
    if not html_content:
        return {"error": "Could not fetch page content"}
    
    content = verifier.extract_content(html_content)
    if not content:
        return {"error": "Could not extract product content"}
    
    # Calculate trust score
    trust_score = verifier.calculate_trust_score(content)
    
    return {
        "url": url,
        "content_found": content,
        "trust_analysis": trust_score
    }

# Example call
if __name__ == "__main__":
    product_url = "https://www.amazon.com/Redragon-Programmable-Hot-Swappable-Anti-Ghosting-Double-Shot/dp/B0CF3VGQFL/ref=sr_1_1?_encoding=UTF8&content-id=amzn1.sym.12129333-2117-4490-9c17-6d31baf0582a&dib=eyJ2IjoiMSJ9.Z9I9mJPxaeCv6Lxtlail774TKoOJxQGgBCl7sb9n2w38m1XsN9GyBJOwczltm8MEbcIAkx_El34aSY42K_qwBFbyoKSU0tF6bBwMNJiCKpPnYkUkvKw6J2YjEU7Mhxp8Q2vGBcrv9i11oNYiX3nkG8daH93dMSz6ZPRBTunlUzomb4Dy_gf3vXKbCbGRSKRk8tFfWPcP5VqLSDXwrjUX09-k2yfNaqxT9UwQLw834gg.TW_AN-HD7GHrYJZfsYC9A9FivTHzbZhleJ3SmV9bMTY&dib_tag=se&keywords=gaming%2Bkeyboard&pd_rd_r=95497851-719b-439c-8802-92b8e9abb61c&pd_rd_w=wdRxG&pd_rd_wg=bidjt&qid=1745306846&sr=8-1&th=1"  # Replace with actual product URL
    result = verify_product_content(product_url)
    print(f"Trust score: {result['trust_analysis']['overall_score']:.2f}")
    print(f"Trust level: {result['trust_analysis']['trust_level']}")
    print("Component scores:")
    for component in result['trust_analysis']['component_scores']:
        print(f"- {component}")