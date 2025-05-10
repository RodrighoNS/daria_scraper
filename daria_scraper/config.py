"""
Configuration settings for the web scraper.
"""

# Target website configuration
TARGETS = [
    {
        "url": "https://outpost-daria-reborn.info",
        "name": "Daria Outpost Reborn",
        "base_url": "https://outpost-daria-reborn.info",
        "selectors": {
            "links": "a",
            "titles": "h1, h2, h3",
            "content": "article p, div.content p",
            "navigation": "nav a, div.menu a",
            "episodes": "div.episode, div.episode-list li",
            "characters": "div.character, div.character-list li",
        }
    }
]

# Request configuration
REQUEST_CONFIG = {
    "USER_AGENT": "DariaScraper/1.0 (educational purposes)",
    "REQUEST_DELAY": 2,  # Time in seconds between requests to avoid overloading the server
    "TIMEOUT": 30,  # Request timeout in seconds
    "RETRIES": 3,  # Number of times to retry a failed request
    "RETRY_DELAY": 5,  # Delay between retries
    "HEADERS": {
        "User-Agent": "DariaScraper/1.0 (educational purposes)",
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
}

# Output configuration
OUTPUT_CONFIG = {
    "FORMAT": "csv",  # Options: csv, json
    "DATA_DIR": "data",  # Directory to store scraped data
    "FILENAME_PREFIX": "daria_scrape",  # Prefix for output files
    "OVERWRITE_EXISTING": False,  # Whether to overwrite existing files
}

# Logging configuration
LOGGING_CONFIG = {
    "LEVEL": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "LOG_FILE": "scraper.log",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# Scraping depth configuration
DEPTH_CONFIG = {
    "MAX_PAGES": 100,  # Maximum number of pages to scrape
    "MAX_DEPTH": 3,  # Maximum link depth to follow from starting URL
}
