from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import os
import re
from urllib.parse import urljoin, urlparse
import time

def extract_images_and_text(url, base_folder="downloaded_images"):
    # Setup Chrome options with improved performance settings
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Initialize driver with optimized settings
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        # Wait for page to fully load
        time.sleep(3)  # Allow JS to execute
        
        # Wait for content to be loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )
        
        html = driver.page_source
        domain = urlparse(url).netloc
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    
    # Text extraction with improved filter
    visible_tags = ['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'a', 'strong', 'em', 'b', 'i', 'u']
    blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script', 'style', 'footer', 'nav']
    
    # E-commerce specific selectors to prioritize
    ecommerce_selectors = {
        'product_title': ['h1.product-title', '.product-title', '.product_title', '#productTitle', 
                          '.product-name', '[data-testid="product-title"]', '.pdp-title', '.title',
                          '[class*="product"][class*="title"]', '[class*="product"][class*="name"]'],
        'product_description': ['.product-description', '#productDescription', '.product-details', 
                                '[data-testid="product-description"]', '.pdp-description', '#feature-bullets',
                                '[class*="product"][class*="description"]', '[class*="product"][class*="details"]',
                                '[class*="description"]', '.details', '.overview', '.features'],
        'product_price': ['.product-price', '.price', '#priceblock_ourprice', '[data-testid="price"]', 
                          '.pdp-price', '.price-box', '[class*="product"][class*="price"]', 
                          '[class*="price"]', '.offer', '.discount'],
        'product_category': ['.breadcrumbs', '.breadcrumb', '.product-category', '.category',
                             '[class*="breadcrumb"]', '[class*="category"]', '.path']
    }
    
    def clean_text(soup):
        output = []
        
        # First try to extract structured data for e-commerce
        for category, selectors in ecommerce_selectors.items():
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        for element in elements:
                            text = element.get_text().strip()
                            if text:
                                # Remove excessive whitespace
                                text = re.sub(r'\s+', ' ', text)
                                output.append((category, text))
                except Exception:
                    continue
        
        # Try to identify the main content area
        main_content = None
        for main_selector in ['main', '#main', '.main', '#content', '.content', '.product-main', '.product-content', '#product-page']:
            main_area = soup.select(main_selector)
            if main_area:
                main_content = main_area[0]
                break
        
        # If we found a main content area, prioritize text from there
        if main_content:
            content_to_search = main_content
        else:
            content_to_search = soup
        
        # Explicitly exclude header/footer/nav areas
        excluded_areas = []
        for exclude_selector in ['header', 'footer', 'nav', '.header', '.footer', '.nav', '.navigation', '.menu', '.sidebar']:
            excluded = soup.select(exclude_selector)
            excluded_areas.extend(excluded)
        
        # Then get general text content from the main area
        for element in content_to_search.find_all(text=True):
            # Skip if element is inside excluded areas
            if any(element in excluded_area.descendants for excluded_area in excluded_areas):
                continue
                
            if element.parent.name in blacklist:
                continue
                
            # Skip if parent has a class that suggests it's not product content
            if element.parent.get('class'):
                parent_class = ' '.join(element.parent.get('class')).lower()
                if any(x in parent_class for x in ['footer', 'nav', 'menu', 'cookie', 'popup', 'banner', 'review', 'comment', 'header']):
                    continue
                    
            text = element.strip()
            if text and element.parent.name in visible_tags:
                # Remove repeated whitespace
                text = re.sub(r'\s+', ' ', text)
                # Only include text that seems meaningful (not just short button text, etc.)
                if len(text) > 5:  # Increase minimum text length
                    # Try to classify the text
                    if element.parent.name in ['h1'] or (element.parent.get('class') and any('title' in c.lower() for c in element.parent.get('class'))):
                        output.append(('product_title', text))
                    elif element.parent.name in ['h2', 'h3'] and len(text) < 100:
                        # Short headings likely to be product features or specs
                        output.append(('product_feature', text))
                    elif len(text) > 100:
                        # Longer paragraphs likely to be descriptions
                        output.append(('product_description', text))
                    else:
                        # Other elements - only include if they seem relevant to products
                        lower_text = text.lower()
                        if any(keyword in lower_text for keyword in ['product', 'item', 'price', 'cost', 'shipping', 'delivery', 'discount', 'features', 'specifications']):
                            output.append(('general_product_info', text))
        
        return output

    text_content = clean_text(soup)
    
    # Better prioritization for text content
    priority_1 = []  # Most important product info (title, price, category)
    priority_2 = []  # Secondary info (descriptions, features, details)
    
    # Define what goes into which priority
    priority_1_categories = ['product_title', 'product_price', 'product_category', 'product_feature']
    priority_2_categories = ['product_description', 'general_product_info']
    
    # Process the extracted text
    for category, text in text_content:
        # Skip duplicate text
        if text in priority_1 or text in priority_2:
            continue
            
        if category in priority_1_categories:
            priority_1.append(text)
        elif category in priority_2_categories:
            priority_2.append(text)
    
    # Remove duplicates while preserving order
    priority_1 = list(dict.fromkeys(priority_1))
    priority_2 = list(dict.fromkeys(priority_2))
    
    # Write output files
    with open("priority_1.txt", "w", encoding="utf-8") as f1:
        f1.write("\n".join(priority_1))
    with open("priority_2.txt", "w", encoding="utf-8") as f2:
        f2.write("\n".join(priority_2))

    print("[✓] Text saved to priority_1.txt and priority_2.txt")

    # Create folders for images
    os.makedirs(base_folder, exist_ok=True)
    jpg_png_folder = os.path.join(base_folder, "jpg_png")
    os.makedirs(jpg_png_folder, exist_ok=True)

    # Image extraction with e-commerce optimizations
    product_images = []
    
    # Common patterns for product image containers
    product_image_containers = [
        '.product-image-container', '.product-gallery', '#imageBlock', '.pdp-image-container',
        '[data-component-type="s-product-image"]', '.product-media-gallery', '.image-wrapper',
        '#product-images', '.main-image', '.image-gallery', '.carousel', '.product-image'
    ]
    
    # Try to find product images in dedicated containers first
    for container in product_image_containers:
        image_container = soup.select(container)
        if image_container:
            for container_elem in image_container:
                container_images = container_elem.find_all('img')
                if container_images:
                    product_images.extend(container_images)
    
    # If no images found in containers, fallback to other heuristics
    if not product_images:
        all_images = soup.find_all("img")
        
        # Filter images based on attributes that suggest product images
        for img in all_images:
            # Skip tiny images (likely icons)
            width = img.get('width')
            height = img.get('height')
            
            if width and height:
                try:
                    if int(width) < 150 or int(height) < 150:
                        continue
                except ValueError:
                    pass
            
            # Look for class/id suggesting product image
            img_class = ' '.join(img.get('class', [])).lower()
            img_id = img.get('id', '').lower()
            img_alt = img.get('alt', '').lower()
            
            # Skip obvious non-product images
            if any(x in img_class for x in ['icon', 'logo', 'avatar', 'review', 'thumbnail', 'nav']):
                continue
            
            if any(x in img_id for x in ['icon', 'logo', 'avatar', 'review', 'thumbnail', 'nav']):
                continue
            
            # Prioritize images with product in their attributes
            if any(x in img_class for x in ['product', 'main', 'primary', 'hero']):
                product_images.insert(0, img)
            elif any(x in img_id for x in ['product', 'main', 'primary', 'hero']):
                product_images.insert(0, img)
            elif any(x in img_alt for x in ['product']):
                product_images.insert(0, img)
            # Filter out common review/icon patterns
            elif 'star' not in img_alt and 'rating' not in img_alt:
                product_images.append(img)
    
    # Limit to top 5 most likely product images
    product_images = product_images[:5]
    
    # Download the images
    downloaded_count = 0
    for i, img in enumerate(product_images):
        img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not img_url:
            continue
            
        full_url = urljoin(url, img_url)
        try:
            response = requests.get(full_url, stream=True, timeout=10)
            
            # Check content type to verify it's an image
            if 'image' not in response.headers.get('Content-Type', ''):
                continue
                
            # Check size - skip very small images
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length < 10000:  # Skip images smaller than ~10KB
                continue
                
            ext = os.path.splitext(urlparse(full_url).path)[1].lower().lstrip(".")
            if not ext or ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = "jpg"

            filename = os.path.join(jpg_png_folder, f"product_image_{i+1}.{ext}")
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[✓] Downloaded {filename}")
            downloaded_count += 1
        except Exception as e:
            print(f"[✗] Failed to download {full_url}: {e}")
    
    if downloaded_count == 0:
        print("[!] No product images found or downloaded.")
    else:
        print(f"[✓] Downloaded {downloaded_count} product images.")
