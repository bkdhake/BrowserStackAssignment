import os
import re
from io import BytesIO
from urllib.parse import urlparse
import requests
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from deep_translator import GoogleTranslator  # Import the deep-translator for translation
from collections import Counter  # Import Counter to count word occurrences

# Path to your WebDriver
driver_path = r'D:\ChromeDriver\chromedriver.exe'  # Use raw string to avoid escape sequence issues
service = Service(driver_path)
driver = webdriver.Chrome(service=service)
# Open the El País website
driver.get("https://elpais.com/")
driver.maximize_window()
time.sleep(5)
# Handle cookie consent
try:
    cookie_button = driver.find_element(By.ID, 'didomi-notice-agree-button')  # Adjust the class name based on the actual button
    cookie_button.click()
    time.sleep(3)
    print("Cookie consent accepted.")
except Exception as e:
    print("No cookie consent pop-up or failed to accept:", e)

# Check if the website is in Spanish
html_tag = driver.find_element(By.TAG_NAME, 'html')
lang = html_tag.get_attribute('lang')

if 'es' in lang.lower():  # Check if 'es' is in the language code (case-insensitive)
    print("The website is in Spanish.")
else:
    print(f"The website language is {lang}, switching to Spanish.")

# Navigate to the Opinion section
try:
    opinion_link = driver.find_element(By.LINK_TEXT, 'Opinión')  # You can also use partial link text or another method if the text is different
    opinion_link.click()
    print("Navigated to the Opinion section.")
    time.sleep(5)  # Wait for the Opinion section to load
except Exception as e:
    print("Error navigating to the Opinion section:", e)

# Scroll down to load more articles (if needed)
driver.execute_script("window.scrollBy(0, 350);")  # Scroll down by 300 pixels
time.sleep(3)

def download_image(url, folder_path):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Failed to download image. Status code: {response.status_code}")
            return
        image_name = os.path.basename(urlparse(url).path)
        if not image_name.endswith(('.jpg', '.png', '.jpeg')):
            print(f"Warning: Image URL does not have a valid extension. Appending '.jpg'.")
            image_name += '.jpg'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        image_path = os.path.join(folder_path, image_name)
        with open(image_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded image: {image_name} to {folder_path}")
    except Exception as e:
        print(f"Failed to download image from {url}. Error: {e}")

# Folder to save the images
folder_name = r"D:\BrowserStackAssignment\CoverImages"  # absolute path

# List to store the translated headers
translated_headers = []

try:
    articles = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, 'article'))
    )

    # Check if articles are found
    if len(articles) == 0:
        print("No articles found on the page.")
    else:
        # Loop through the articles (adjust the range for more/less articles)
        for i, article in enumerate(articles[:5]):
            try:
                header = article.find_element(By.XPATH, ".//h2").text
            except NoSuchElementException:
                header = "No header found"

            # Translate the header to English
            translated_header = GoogleTranslator(source='es', target='en').translate(header)
            translated_headers.append(translated_header)

            try:
                content = article.find_element(By.XPATH, ".//p").text
            except NoSuchElementException:
                content = "No content found"

            # Check for the cover image
            try:
                cover_image = article.find_element(By.XPATH, ".//img")
                cover_image_url = cover_image.get_attribute('src')
                cover_image_exists = True
            except NoSuchElementException:
                cover_image_exists = False
                cover_image_url = None

            # Print the article number, header, translated header, content, and whether it has a cover image
            print(f"Article {i + 1} Header: {header}")
            print(f"Translated Header (English): {translated_header}")
            print(f"Content: {content}")
            print(f"Cover Image Attached: {'Yes' if cover_image_exists else 'No'}")
            print("-" * 80)

            # If the article has a cover image, download it
            if cover_image_exists and cover_image_url:
                download_image(cover_image_url, folder_name)

except TimeoutException:
    print("Timed out waiting for the page to load or the articles to appear.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# Identify repeated words in the translated headers
all_words = []

# Function to clean and split words
def split_and_clean(header):
    # Remove punctuation using regular expression
    header = re.sub(r'[^\w\s]', '', header)  # Removes punctuation
    words = header.lower().split()  # Split into words and convert to lowercase
    return words

# Split each translated header into words and add them to the all_words list
for header in translated_headers:
    all_words.extend(split_and_clean(header))

# Count occurrences of each word
word_counts = Counter(all_words)

# Print words repeated more than once
print("\nWords repeated more than twice in the translated headers:")
for word, count in word_counts.items():
    if count > 2:  # Adjusted to print words repeated more than once
        print(f"{word}: {count}")

# Close the browser
driver.quit()
