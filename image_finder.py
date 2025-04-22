import requests
from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO
import imagehash
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def reverse_image_search(image_path, is_local=False):
    """
    Perform reverse image search using TinEye API (free tier) or Google Images through Selenium
    Returns a similarity score from 0 to 1 (higher means more likely to be stolen)
    """
    try:
        # Handle image loading differently based on whether it's a URL or local file
        if is_local:
            img = Image.open(image_path)
        else:
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
        
        # Convert RGBA to RGB if needed before saving as JPEG
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Save temporarily
        temp_path = os.path.abspath("temp_img.jpg")
        img.save(temp_path)
        
        # Using Selenium to automate Google reverse image search
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Go to Google Images
        driver.get("https://images.google.com")
        
        # Click on camera icon
        camera_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Search by image']"))
        )
        camera_button.click()
        
        # Upload image
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(temp_path)
        
        # Wait for results
        time.sleep(5)
        
        # Count results to determine how common the image is
        results = driver.find_elements(By.CSS_SELECTOR, ".g")
        num_results = len(results)
        
        # Calculate score based on number of matches
        if num_results > 10:
            score = 0.9  # Likely stolen if many matches
        elif num_results > 5:
            score = 0.7
        elif num_results > 2:
            score = 0.5
        elif num_results > 0:
            score = 0.3
        else:
            score = 0.1  # Likely original if no matches
            
        driver.quit()
        return score
        
    except Exception as e:
        print(f"Error in reverse image search: {e}")
        return 0.5  # Neutral score if error occurs

def analyze_metadata(image_path, is_local=False):
    """
    Analyze image metadata for signs of manipulation
    Returns a suspicion score from 0 to 1
    """
    try:
        # Handle image loading differently based on whether it's a URL or local file
        if is_local:
            img = Image.open(image_path)
        else:
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
        
        # Get EXIF data
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif():
            for tag_id, value in img._getexif().items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
        
        # Check for metadata removal (suspicious)
        if len(exif_data) < 5:
            return 0.7  # Suspicious if little metadata
            
        # Check for software used (Photoshop, etc.)
        if 'Software' in exif_data:
            if 'photoshop' in exif_data['Software'].lower():
                return 0.6  # More likely to be edited
        
        # Check for original date
        if 'DateTimeOriginal' not in exif_data:
            return 0.5  # Moderately suspicious if no original date
            
        return 0.2  # Low suspicion if metadata seems normal
        
    except Exception as e:
        print(f"Error in metadata analysis: {e}")
        return 0.4  # Neutral-suspicious if error occurs

def compare_image_hash(image_path, database_urls, is_local=False):
    """
    Compare image perceptual hash with a database of images
    Returns similarity score from 0 to 1
    """
    try:
        # Handle image loading differently based on whether it's a URL or local file
        if is_local:
            target_img = Image.open(image_path)
        else:
            response = requests.get(image_path)
            target_img = Image.open(BytesIO(response.content))
        
        # Calculate perceptual hash
        target_hash = imagehash.phash(target_img)
        
        # Compare with database images
        similarity_scores = []
        
        for db_url in database_urls:
            try:
                db_response = requests.get(db_url)
                db_img = Image.open(BytesIO(db_response.content))
                db_hash = imagehash.phash(db_img)
                
                # Calculate hash difference (0 is identical, higher is different)
                hash_diff = target_hash - db_hash
                
                # Convert to similarity score (0 to 1)
                similarity = 1.0 if hash_diff == 0 else 1.0 / (1.0 + hash_diff)
                similarity_scores.append(similarity)
            except:
                continue
        
        # Return maximum similarity if any found
        if similarity_scores:
            return max(similarity_scores)
        return 0.0  # No similarity if no valid comparisons
        
    except Exception as e:
        print(f"Error in hash comparison: {e}")
        return 0.0

def detect_manipulation(image_path, is_local=False):
    """
    Detect image manipulation using simple analysis
    Returns a suspicion score from 0 to 1
    """
    try:
        # Handle image loading differently based on whether it's a URL or local file
        if is_local:
            img = Image.open(image_path)
        else:
            response = requests.get(image_path)
            img = Image.open(BytesIO(response.content))
        
        # Convert to array for analysis
        img_array = np.array(img)
        
        # Simple error level analysis
        # Look for inconsistencies in compression artifacts
        if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
            # Check color distribution for anomalies
            r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
            
            # Check for unusual color correlations (potential sign of manipulation)
            correlation_rg = np.corrcoef(r.flatten(), g.flatten())[0,1]
            correlation_rb = np.corrcoef(r.flatten(), b.flatten())[0,1]
            correlation_gb = np.corrcoef(g.flatten(), b.flatten())[0,1]
            
            avg_correlation = (correlation_rg + correlation_rb + correlation_gb) / 3
            
            # Very high or very low correlation can indicate manipulation
            if avg_correlation > 0.98 or avg_correlation < 0.4:
                return 0.7
            
        # Check image dimensions - unusually perfect dimensions sometimes indicate stock/generated images
        width, height = img.size
        if width % 100 == 0 and height % 100 == 0:
            return 0.6
            
        return 0.3  # Low suspicion by default
        
    except Exception as e:
        print(f"Error in manipulation detection: {e}")
        return 0.5  # Neutral score if error occurs

def get_image_urls_from_page(product_url):
    """
    Extract image URLs from a product page using Selenium
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.get(product_url)
        time.sleep(3)  # Wait for page to load
        
        # Find image elements - adjust selectors based on the website structure
        image_elements = driver.find_elements(By.CSS_SELECTOR, "img")
        
        # Extract URLs
        image_urls = []
        for img in image_elements:
            src = img.get_attribute("src")
            if src and (src.endswith('.jpg') or src.endswith('.jpeg') or src.endswith('.png')):
                image_urls.append(src)
                
        driver.quit()
        return image_urls
        
    except Exception as e:
        print(f"Error extracting images: {e}")
        return []

def calculate_fakeness_score(image_path, database_urls=None, is_local=False):
    """
    Calculate an overall fakeness/stolen score from 0 to 1
    Higher scores indicate higher likelihood of being fake/stolen
    """
    if database_urls is None:
        database_urls = []
    
    # Get individual scores
    reverse_search_score = reverse_image_search(image_path, is_local)
    metadata_score = analyze_metadata(image_path, is_local)
    manipulation_score = detect_manipulation(image_path, is_local)
    
    # Get hash comparison score if database provided
    hash_score = compare_image_hash(image_path, database_urls, is_local) if database_urls else 0.0
    
    # Weighted average (you can adjust weights based on reliability)
    weights = {
        'reverse_search': 0.4,  # Most reliable indicator for stolen images
        'metadata': 0.2,
        'manipulation': 0.3,
        'hash_comparison': 0.1
    }
    
    final_score = (
        weights['reverse_search'] * reverse_search_score +
        weights['metadata'] * metadata_score +
        weights['manipulation'] * manipulation_score +
        weights['hash_comparison'] * hash_score
    )
    
    confidence = {
        0.0: "Very likely original",
        0.2: "Probably original",
        0.4: "Uncertain",
        0.6: "Possibly fake/stolen",
        0.8: "Likely fake/stolen",
        1.0: "Almost certainly fake/stolen"
    }
    
    # Find closest confidence level
    closest_key = min(confidence.keys(), key=lambda k: abs(k - final_score))
    
    return {
        'score': final_score,
        'assessment': confidence[closest_key],
        'component_scores': {
            'reverse_search': reverse_search_score,
            'metadata': metadata_score,
            'manipulation': manipulation_score,
            'hash_comparison': hash_score
        }
    }

def check_product_images(product_url):
    """
    Check all images from a product page
    """
    image_urls = get_image_urls_from_page(product_url)
    
    results = {}
    for i, img_url in enumerate(image_urls):
        results[f"image_{i}"] = calculate_fakeness_score(img_url)
    
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test.py <image_path_or_url>")
        sys.exit(1)
    
    image_input = sys.argv[1]
    
    # Check if input is URL or local file
    if image_input.startswith(('http://', 'https://')):
        # Input is a URL
        if 'product' in image_input.lower() or '/' in image_input.split('.')[-1]:
            # Looks like a product page
            print("Analyzing product page images...")
            results = check_product_images(image_input)
            for img_key, result in results.items():
                print(f"\n{img_key}:")
                print(f"Fakeness score: {result['score']:.2f}")
                print(f"Assessment: {result['assessment']}")
        else:
            # Single image URL
            print("Analyzing single image...")
            result = calculate_fakeness_score(image_input)
            print(f"Fakeness score: {result['score']:.2f}")
            print(f"Assessment: {result['assessment']}")
            print("\nComponent scores:")
            for key, score in result['component_scores'].items():
                print(f"- {key}: {score:.2f}")
    else:
        # Input is a local file path
        try:
            local_path = os.path.abspath(image_input)
            if not os.path.exists(local_path):
                print(f"Error: File not found - {local_path}")
                sys.exit(1)
                
            print("Analyzing local image...")
            # Pass the local path directly instead of trying to convert to a URL format
            result = calculate_fakeness_score(local_path, is_local=True)
            print(f"Fakeness score: {result['score']:.2f}")
            print(f"Assessment: {result['assessment']}")
            print("\nComponent scores:")
            for key, score in result['component_scores'].items():
                print(f"- {key}: {score:.2f}")
        except Exception as e:
            print(f"Error processing local file: {e}")
            sys.exit(1)