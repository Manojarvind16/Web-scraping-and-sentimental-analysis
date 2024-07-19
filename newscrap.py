import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
import time
import os
import re
import sys
import numpy as np
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI
import logging

# Setup logging
logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger()

#function for scraping
def scrap_flipkart_reviews(url, product_name):

    # Initialize the WebDriver
    browser = webdriver.Chrome()

    browser.get(url)

    # Lists to hold the collected data
    reviews_data = []

    while True:
        try:
            # Wait for the review section to be visible
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//div[@class='DOjaWF gdgoEp col-9-12']"))
            )

            # Find and click all "Read More" buttons to expand the reviews
            read_more_buttons = browser.find_elements(By.XPATH, "//span[@class='b4x-fr']")
            for button in read_more_buttons:
                try:
                    # Scroll the button into view
                    browser.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)  # Slight pause to ensure smooth scrolling
                    
                    # Attempt to click the button
                    try:
                        WebDriverWait(browser, 5).until(EC.element_to_be_clickable(button))
                        button.click()
                        time.sleep(2)  # Allow some time for the expanded content to load
                    except (ElementClickInterceptedException, ElementNotInteractableException):
                        logger.warning(f"Direct click failed, trying JavaScript click for button at location ({button.location['x']}, {button.location['y']}).")
                        browser.execute_script("arguments[0].click();", button)
                        time.sleep(2)  # Allow some time for the expanded content to load

                except Exception as e:
                    logger.error(f"Could not click 'Read More' button: {e}")

            # Extract individual ratings and reviews
            ratings = browser.find_elements(By.XPATH, "//div[@class='XQDdHH Ga3i8K']")
            reviews = browser.find_elements(By.XPATH, "//div[@class='ZmyHeo']")

            # Append each review and rating to the respective lists with the product name
            for review, rating in zip(reviews, ratings):
                reviews_data.append({
                    "Product": product_name,
                    "Rating": rating.text.strip(),
                    "Review": review.text.strip()
                })

            # Find and click the "Next" button
            next_buttons = browser.find_elements(By.XPATH, "//span[contains(text(),'Next')]")

            if len(next_buttons) > 0:
                next_button = next_buttons[0]
                # Check if the button's parent is clickable (the <a> tag containing the "Next" span)
                next_button_parent = next_button.find_element(By.XPATH, "..")
                if next_button_parent.tag_name == 'a' and next_button_parent.get_attribute('href'):
                    next_button_parent.click()
                    logger.info("Navigating to the next page...")
                    time.sleep(3)  # Allow some time for the next page to load
                else:
                    logger.info("Next button is not clickable or no more pages.")
                    break
            else:
                logger.info("No 'Next' button found. Reached the last page.")
                break

        except NoSuchElementException:
            logger.error("No more pages or error navigating to the next page.")
            break

        except TimeoutException:
            logger.error("Loading timeout or no 'Next' button found, exiting.")
            break

    # Close the browser
    browser.quit()

# Create a DataFrame from the collected data
    df = pd.DataFrame(reviews_data)

    # Data Cleaning
    # Clearing the Special Character
    pattern = re.compile(r'[^\x00-\x7F]+')
    df["Review"] = df["Review"].replace({pattern: ' '}, regex=True)
    # Trim spaces from the values in the Neighborhood_Overview column
    df['Review'] = df['Review'].str.strip()
    # Replace empty strings with NaN
    df['Review'] = df['Review'].replace({'': np.nan})
    # Drop rows where Review is NaN
    df = df.dropna(subset=['Review'])
    # Optionally, reset the index if you want a clean DataFrame without gaps in the index
    df = df.reset_index(drop=True)
    csv_filename = f"{product_name}_reviews.csv"
    df.to_csv(csv_filename, index=False)

url = "https://www.flipkart.com/samsung-galaxy-s22-5g-green-128-gb/product-reviews/itm92c75094f3b93?pid=MOBGGG2YKYPWPCNP&lid=LSTMOBGGG2YKYPWPCNPJQJIS6&marketplace=FLIPKART"
product_name = "SAMSUNG Galaxy S22 5G"

scrap_flipkart_reviews(url, product_name)
