import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess

def find_chrome_binary():
    # List of possible Chrome/Chromium binary names and locations
    possible_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
        "/usr/lib/chromium-browser/chromium-browser",
        "/usr/lib/chromium/chromium",
        # Add Snap installation path
        "/snap/bin/chromium",
        # Add Flatpak installation path
        "/var/lib/flatpak/app/org.chromium.Chromium/current/active/files/bin/chromium"
    ]
    
    # Try to get Chrome location using 'which' command
    try:
        chrome_path = subprocess.check_output(["which", "chromium-browser"]).decode().strip()
        if os.path.exists(chrome_path):
            return chrome_path
    except subprocess.CalledProcessError:
        pass

    # Check all possible paths
    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    # If we get here, we couldn't find Chrome
    existing_paths = "\n".join([f"Checked {p} - {'Exists' if os.path.exists(p) else 'Not Found'}" for p in possible_paths])
    raise Exception(f"Chrome/Chromium browser binary not found. Checked locations:\n{existing_paths}\n\nPlease install Chrome or Chromium using:\nsudo apt update && sudo apt install chromium-browser chromium-chromedriver")

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Find and set Chrome binary location
    chrome_path = find_chrome_binary()
    print(f"Using Chrome binary at: {chrome_path}")
    options.binary_location = chrome_path
    
    return uc.Chrome(options=options)

def reverse_image_search(driver, image_path):
    driver.get("https://lens.google.com/upload")

    try:
        upload_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        upload_input.send_keys(os.path.abspath(image_path))

        # Wait for result page
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        )

        print(f"[FOUND] {os.path.basename(image_path)} found on web ✅")
    except Exception as e:
        print(f"[ERROR] {os.path.basename(image_path)}: {e}")
        driver.save_screenshot("error_screenshot.png")

def main():
    # First check if the image folder exists
    image_folder = "downloaded_images/jpg_png"
    if not os.path.exists(image_folder):
        raise Exception(f"Image folder not found: {image_folder}")

    image_paths = [
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    if not image_paths:
        raise Exception(f"No images found in {image_folder}")

    for img in image_paths:
        try:
            driver = get_driver()
            reverse_image_search(driver, img)
        finally:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
