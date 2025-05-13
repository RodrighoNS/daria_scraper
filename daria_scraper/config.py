"""
Configuration settings for the Daria scraper.
"""

# Logging configuration
LOGGING_CONFIG = {
    "LOG_FILE": "logs/daria_scraper.log",
    "LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# Request configuration
REQUEST_CONFIG = {
    "HEADERS": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "TIMEOUT": 30,
    "REQUEST_DELAY": 1,
    "RETRY_DELAY": 5,
    "RETRIES": 3
}

# Output configuration
OUTPUT_CONFIG = {
    "DATA_DIR": "data",
    "FILENAME_PREFIX": "daria_scraper"
}

# Target websites
TARGETS = [
    {
        "name": "Outpost Daria Reborn",
        "base_url": "https://outpost-daria-reborn.info",
        "characters_url": "https://outpost-daria-reborn.info/characters.html"
    }
]
