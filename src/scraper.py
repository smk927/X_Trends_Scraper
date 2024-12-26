
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import random
import time
from pymongo import MongoClient
from .config import Config
import uuid
import logging
from .config import Config
import uuid
import logging
import os
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwitterScraper:
    def __init__(self):
        self.config = Config()
        self.setup_mongodb_connection()

    def setup_mongodb_connection(self):
        try:
            # Try connecting to MongoDB
            self.mongo_client = MongoClient(self.config.MONGODB_URI)
            # Test the connection
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client['twitter_trends']
            self.collection = self.db['trends']
            logger.info("Successfully connected to MongoDB")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            # Setup fallback to local JSON storage
            self.mongo_client = None
            self.db = None
            self.collection = None
            logger.info("Falling back to local JSON storage")

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Disable proxy for testing
        # proxy = self.get_proxy()
        # chrome_options.add_argument(f'--proxy-server={proxy["http"]}')

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def login_twitter(self, driver):
        try:
            logger.info("Attempting to log in to Twitter...")
            driver.get('https://twitter.com/i/flow/login')
            time.sleep(5)

            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.clear()
            username_input.send_keys(self.config.TWITTER_USERNAME)
            time.sleep(1)

            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()
            time.sleep(2)

            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
            )
            password_input.clear()
            password_input.send_keys(self.config.TWITTER_PASSWORD)
            time.sleep(1)

            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
            )
            login_button.click()
            time.sleep(5)

            logger.info("Successfully logged in to Twitter")

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            driver.save_screenshot('login_error.png')
            raise

    def save_record(self, record):
        """Save record to either MongoDB or local JSON file"""
        if self.collection:
            try:
                self.collection.insert_one(record)
                logger.info("Successfully saved record to MongoDB")
            except Exception as e:
                logger.error(f"Failed to save to MongoDB: {str(e)}")
                self._save_to_json(record)
        else:
            self._save_to_json(record)

    def _save_to_json(self, record):
        """Fallback method to save records locally"""
        try:
            # Convert datetime to string for JSON serialization
            record['timestamp'] = record['timestamp'].isoformat()

            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)

            # Save to JSON file
            filename = f"data/trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(record, f, indent=2)
            logger.info(f"Successfully saved record to {filename}")
        except Exception as e:
            logger.error(f"Failed to save to JSON: {str(e)}")
            raise

    def get_trending_topics(self):
        driver = None
        try:
            logger.info("Starting trending topics scraping...")
            driver = self.setup_driver()
            self.login_twitter(driver)

            driver.get('https://twitter.com/explore/tabs/trending')
            time.sleep(5)

            driver.execute_script("window.scrollBy(0, 300)")
            time.sleep(2)

            trends_section = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="trend"]'))
            )

            trends = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="trend"]'))
            )

            trending_topics = []
            for trend in trends[:5]:
                try:
                    text_elements = trend.text.split('\n')

                    trend_text = None
                    for text in text_elements:
                        if not any(header in text.lower() for header in ['trending', 'posts', '·', 'k posts']):
                            if text.strip() and not text.strip().isdigit():
                                trend_text = text.strip()
                                break

                    if not trend_text:
                        hashtags = trend.find_elements(By.CSS_SELECTOR, '[href*="hashtag"]')
                        if hashtags:
                            trend_text = hashtags[0].text.strip()

                    if not trend_text:
                        spans = trend.find_elements(By.TAG_NAME, 'span')
                        for span in spans:
                            text = span.text.strip()
                            if text and not any(
                                    header in text.lower() for header in ['trending', 'posts', '·', 'k posts']):
                                trend_text = text
                                break

                    if not trend_text:
                        trend_text = "Unable to fetch trend name"

                    trending_topics.append(trend_text)
                    logger.info(f"Found trend: {trend_text}")

                except Exception as e:
                    logger.error(f"Error extracting trend text: {str(e)}")
                    trending_topics.append("Unable to fetch trend name")

            while len(trending_topics) < 5:
                trending_topics.append("Unable to fetch trend name")
            trending_topics = trending_topics[:5]  # Limit to 5 trends

            record = {
                "_id": str(uuid.uuid4()),
                "nameoftrend1": trending_topics[0],
                "nameoftrend2": trending_topics[1],
                "nameoftrend3": trending_topics[2],
                "nameoftrend4": trending_topics[3],
                "nameoftrend5": trending_topics[4],
                "timestamp": datetime.now(),
                "ip_address": "127.0.0.1"
            }

            self.save_record(record)
            logger.info("Successfully scraped trending topics")
            return record

        except Exception as e:
            logger.error(f"Error in get_trending_topics: {str(e)}")
            if driver:
                driver.save_screenshot('scraping_error.png')
            raise

        finally:
            if driver:
                driver.quit()