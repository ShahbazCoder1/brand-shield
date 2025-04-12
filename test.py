"""
Old code for image and text extraction from a webpage using Selenium and BeautifulSoup.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin, urlparse

def extract_images_and_text(url, base_folder="downloaded_images"):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    visible_tags = ['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'a', 'strong', 'em', 'b', 'i', 'u']
    blacklist = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script', 'style']

    def clean_text(soup):
        output = []
        for element in soup.find_all(text=True):
            if element.parent.name in blacklist:
                continue
            text = element.strip()
            if text and element.parent.name in visible_tags:
                output.append((element.parent.name, text))
        return output

    text_content = clean_text(soup)

    priority_1 = [text for tag, text in text_content if tag != 'p']
    priority_2 = [text for tag, text in text_content if tag == 'p']

    with open("priority_1.txt", "w", encoding="utf-8") as f1:
        f1.write("\n".join(priority_1))
    with open("priority_2.txt", "w", encoding="utf-8") as f2:
        f2.write("\n".join(priority_2))

    print("[✓] Text saved to priority_1.txt and priority_2.txt")

    os.makedirs(base_folder, exist_ok=True)
    jpg_png_folder = os.path.join(base_folder, "jpg_png")
    os.makedirs(jpg_png_folder, exist_ok=True)

    img_tags = soup.find_all("img")
    for i, img in enumerate(img_tags):
        img_url = img.get("src")
        if not img_url:
            continue
        full_url = urljoin(url, img_url)
        try:
            response = requests.get(full_url)
            ext = os.path.splitext(urlparse(full_url).path)[1].lower().lstrip(".")

            if not ext:
                ext = "jpg"

            if ext in ["jpg", "jpeg", "png"]:
                save_folder = jpg_png_folder
            else:
                save_folder = os.path.join(base_folder, ext)
                os.makedirs(save_folder, exist_ok=True)

            filename = os.path.join(save_folder, f"image_{i+1}.{ext}")
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[✓] Downloaded {filename}")
        except Exception as e:
            print(f"[✗] Failed to download {full_url}: {e}")

# <<<<<<< HEAD
# extract_images_and_text("http://localhost:8000/")
# =======
# extract_images_and_text("https://shahbazcoder1.github.io/brand-shield/")
# >>>>>>> 98f47a1 (Add keyword extraction and brand name generation script)
