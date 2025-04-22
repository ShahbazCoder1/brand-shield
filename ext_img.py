from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin, urlparse

def save_images(url, base_folder="downloaded_images"):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    os.makedirs(base_folder, exist_ok=True)
    jpg_png_folder = os.path.join(base_folder, "jpg_png")
    os.makedirs(jpg_png_folder, exist_ok=True)

    product_images = []
    product_image_containers = [
        '.product-image-container', '.product-gallery', '#imageBlock', '.pdp-image-container',
        '[data-component-type="s-product-image"]', '.product-media-gallery', '.image-wrapper',
        '#product-images', '.main-image', '.image-gallery', '.carousel', '.product-image'
    ]

    for container in product_image_containers:
        image_container = soup.select(container)
        if image_container:
            for container_elem in image_container:
                container_images = container_elem.find_all('img')
                if container_images:
                    product_images.extend(container_images)

    if not product_images:
        all_images = soup.find_all("img")
        for img in all_images:
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 150 or int(height) < 150:
                        continue
                except ValueError:
                    pass
            img_class = ' '.join(img.get('class', [])).lower()
            img_id = img.get('id', '').lower()
            img_alt = img.get('alt', '').lower()
            if any(x in img_class for x in ['icon', 'logo', 'avatar', 'review', 'thumbnail', 'nav']):
                continue
            if any(x in img_id for x in ['icon', 'logo', 'avatar', 'review', 'thumbnail', 'nav']):
                continue
            if any(x in img_class for x in ['product', 'main', 'primary', 'hero']):
                product_images.insert(0, img)
            elif any(x in img_id for x in ['product', 'main', 'primary', 'hero']):
                product_images.insert(0, img)
            elif any(x in img_alt for x in ['product']):
                product_images.insert(0, img)
            elif 'star' not in img_alt and 'rating' not in img_alt:
                product_images.append(img)

    product_images = product_images[:5]

    downloaded_count = 0
    for i, img in enumerate(product_images):
        img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not img_url:
            continue
        full_url = urljoin(url, img_url)
        try:
            response = requests.get(full_url, stream=True, timeout=10)
            if 'image' not in response.headers.get('Content-Type', ''):
                continue
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length < 10000:
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

save_images("https://www.nearbymedi.store/")
