"""
HTTP service for handling web requests with retry logic and rate limiting.
"""

from urllib.parse import urljoin
import time
import requests

class Http:
    """Service for handling HTTP requests with built-in retry logic and rate limiting."""

    def __init__(self, config, logger):
        """
        Initialize the HTTP service.

        Args:
            config: Configuration object with request settings
            logger: Logger instance for recording activity
        """
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(config.REQUEST_CONFIG["HEADERS"])

    def fetch(self, url, retry_count=0):
        """
        Fetch a URL with retry logic and rate limiting.

        Args:
            url: URL to fetch
            retry_count: Current retry attempt (used internally for recursion)

        Returns:
            Response object on success, None on failure
        """
        try:
            self.logger.info("Requesting: %s", url)
            response = self.session.get(
                url,
                timeout=self.config.REQUEST_CONFIG["TIMEOUT"]
            )
            response.raise_for_status()

            # Add delay to avoid hammering the server
            time.sleep(self.config.REQUEST_CONFIG["REQUEST_DELAY"])

            return response
        except requests.exceptions.RequestException as e:
            self.logger.error("Error fetching %s: %s", url, e)
            if retry_count < self.config.REQUEST_CONFIG["RETRIES"]:
                self.logger.info("Retrying (%d/%d)...",
                                retry_count + 1,
                                self.config.REQUEST_CONFIG['RETRIES'])
                time.sleep(self.config.REQUEST_CONFIG["RETRY_DELAY"])
                return self.fetch(url, retry_count + 1)
            else:
                self.logger.error("Max retries reached. Giving up.")
                return None

    def build_url(self, base_url, path):
        """
        Build a complete URL from a base URL and a path.

        Args:
            base_url: Base URL (e.g., 'https://example.com')
            path: Path to join (e.g., '/page.html')

        Returns:
            Complete URL
        """
        return urljoin(base_url, path)
