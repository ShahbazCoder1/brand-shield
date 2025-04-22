import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import random
import traceback
from ai_detector import AIContentDetector, detect_ecommerce_product
from text_finder import verify_product_content
from image_finder import calculate_fakeness_score

def analyze_website(url):
    """
    Combined function to extract content and analyze it using multiple tools
    Returns structured results of AI detection, text originality and image analysis
    """
    try:
        extracted_content = extract_website_content(url)
        
        ai_analysis = {}
        if extracted_content.get('title') or extracted_content.get('description'):
            ai_analysis = detect_ecommerce_product({
                'title': extracted_content.get('title', ''),
                'description': extracted_content.get('description', '')
            })
        
        text_originality = verify_product_content(url)
        
        image_analysis = analyze_extracted_images(extracted_content.get('image_paths', []))
        
        return {
            'url': url,
            'extracted_content': extracted_content,
            'ai_analysis': ai_analysis,
            'text_originality': text_originality,
            'image_analysis': image_analysis,
            'success': True
        }
        
    except Exception as e:
        print(f"Error in website analysis: {str(e)}")
        traceback.print_exc()
        return {
            'url': url,
            'success': False,
            'error': str(e)
        }

def extract_website_content(url):
    """
    Extract website content including images, title, and text
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
    finally:
        if driver:
            driver.quit()
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract title
    title = ""
    if soup.title:
        title = soup.title.string
    
    # Extract description
    description = ""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        description = meta_desc.get('content', '')
    
    if not description:
        main_content_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '.product-info', '.product-description'
        ]
        
        for selector in main_content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                paragraphs = content_area.find_all('p')
                if paragraphs:
                    description = " ".join([p.get_text().strip() for p in paragraphs])
                    break
    
    priority_1_elements = soup.find_all(['h1', 'h2', 'h3'])
    priority_1 = "\n".join([el.get_text().strip() for el in priority_1_elements if el.get_text().strip()])
   
    priority_2_elements = soup.find_all(['p', 'div.description', 'span.product-info'])
    priority_2 = "\n".join([el.get_text().strip() for el in priority_2_elements 
                           if el.get_text().strip() and len(el.get_text().strip()) > 20])
    
    with open("priority_1.txt", "w", encoding="utf-8") as f:
        f.write(priority_1)
    
    with open("priority_2.txt", "w", encoding="utf-8") as f:
        f.write(priority_2)
    
    base_folder = "downloaded_images"
    jpg_png_folder = os.path.join(base_folder, "jpg_png")
    os.makedirs(jpg_png_folder, exist_ok=True)
    
    for file in os.listdir(jpg_png_folder):
        os.remove(os.path.join(jpg_png_folder, file))
    
    all_images = soup.find_all("img")
    image_paths = []
    downloaded_count = 0
    
    for i, img in enumerate(all_images):
        img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not img_url:
            continue
            
        width = img.get('width')
        height = img.get('height')
        if width and height:
            try:
                if int(width) < 100 or int(height) < 100:
                    continue
            except ValueError:
                pass
              
        img_class = ' '.join(img.get('class', [])).lower()
        img_id = img.get('id', '').lower()
        if any(x in img_class for x in ['icon', 'logo', 'avatar', 'thumbnail']):
            continue
        if any(x in img_id for x in ['icon', 'logo', 'avatar', 'thumbnail']):
            continue
          
        try:
            full_url = urljoin(url, img_url)
            response = requests.get(full_url, stream=True, timeout=10)
            
            if 'image' not in response.headers.get('Content-Type', '').lower():
                continue
                
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length < 5000: 
                continue
                
            ext = os.path.splitext(urlparse(full_url).path)[1].lower().lstrip(".")
            if not ext or ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = "jpg"
                
            filename = os.path.join(jpg_png_folder, f"image_{i+1}.{ext}")
            with open(filename, "wb") as f:
                f.write(response.content)
                
            image_paths.append(f"/downloaded_images/jpg_png/image_{i+1}.{ext}")
            downloaded_count += 1
            
            # Limit to 10 images
            if downloaded_count >= 10:
                break
                
        except Exception as e:
            print(f"Error downloading image {full_url}: {str(e)}")
    
    return {
        'title': title,
        'description': description,
        'priority_1': priority_1,
        'priority_2': priority_2,
        'image_paths': image_paths
    }

def analyze_extracted_images(image_paths, base_dir=''):
    """
    Analyze downloaded images using the image_finder module
    """
    if not image_paths:
        return []
        
    results = []
    for i, path in enumerate(image_paths):
        full_path = os.path.join(os.getcwd(), path.lstrip('/'))
        if not os.path.exists(full_path):
            continue
            
        try:
            analysis = calculate_fakeness_score(full_path, is_local=True)
            results.append({
                'path': path,
                'index': i,
                'analysis': analysis
            })
        except Exception as e:
            print(f"Error analyzing image {path}: {str(e)}")
    
    return results

def get_overall_trust_score(analysis_results):
    """
    Calculate an overall trust score based on all analyses
    """
    scores = []
    weights = {
        'ai_content': 0.3,
        'text_originality': 0.4,
        'image_authenticity': 0.3
    }
    
    if analysis_results.get('ai_analysis') and analysis_results['ai_analysis'].get('overall_score') is not None:
        ai_score = 1 - analysis_results['ai_analysis']['overall_score']
        scores.append(('ai_content', ai_score))
    
    if analysis_results.get('text_originality') and analysis_results['text_originality'].get('trust_analysis'):
        text_score = analysis_results['text_originality']['trust_analysis'].get('overall_score', 0.5)
        scores.append(('text_originality', text_score))
    
    if analysis_results.get('image_analysis'):
        image_scores = [1 - img['analysis']['score'] for img in analysis_results['image_analysis'] if 'analysis' in img]
        if image_scores:
            avg_image_score = sum(image_scores) / len(image_scores)
            scores.append(('image_authenticity', avg_image_score))
    
    if not scores:
        return 0.5
    
    weighted_sum = 0
    total_weight = 0
    
    for category, score in scores:
        weight = weights.get(category, 1)
        weighted_sum += score * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.5
