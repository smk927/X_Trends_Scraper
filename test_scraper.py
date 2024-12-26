from src.scraper import TwitterScraper

scraper = TwitterScraper()
try:
    result = scraper.get_trending_topics()
    print("Success:", result)
except Exception as e:
    print("Error:", str(e))