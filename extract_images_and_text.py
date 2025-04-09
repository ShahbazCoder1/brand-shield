from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urljoin

def extract_images_and_text(url, download_folder="downloaded_images"):
    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Get page source and close browser
    html = driver.page_source
    driver.quit()

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")

    # Create folder for images
    os.makedirs(download_folder, exist_ok=True)

    for i, img in enumerate(img_tags):
        img_url = img.get("src")
        if not img_url:
            continue
        # Make absolute URL
        full_url = urljoin(url, img_url)

        try:
            img_data = requests.get(full_url).content
            filename = os.path.join(download_folder, f"image_{i+1}.jpg")
            with open(filename, "wb") as f:
                f.write(img_data)
            print(f"[+] Downloaded {filename}")
        except Exception as e:
            print(f"[!] Failed to download {full_url}: {e}")

    # Text scraping section
    priority_1 = []
    priority_2 = []
    priority_3 = []

    for h1 in soup.find_all("h1"):
        priority_1.append(h1.get_text(strip=True))

    for h in soup.find_all(["h2", "h3"]):
        priority_2.append(h.get_text(strip=True))

    for p in soup.find_all("p"):
        priority_3.append(p.get_text(strip=True))

    # Save text to files
    with open("priority_1.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(priority_1))

    with open("priority_2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(priority_2))

    with open("priority_3.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(priority_3))

    print("[✓] Text content saved into priority files.")

