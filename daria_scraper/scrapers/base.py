"""
Base scraper class providing common functionality for all scrapers.
"""

class BaseScraper:
    """
    Base class for all scrapers with common functionality.

    This class provides the foundation for specialized scrapers,
    handling common operations like fetching and parsing pages.
    """

    def __init__(self, http_service, parser, logger, config):
        """
        Initialize the base scraper.

        Args:
            http_service: Service for making HTTP requests
            parser: HTML parser for processing responses
            logger: Logger instance for recording activity
            config: Configuration object
        """
        self.http_service = http_service
        self.parser = parser
        self.logger = logger
        self.config = config
        self.base_url = config.TARGETS[0]['base_url']

    def fetch_and_parse(self, url):
        """
        Fetch a page and parse it.

        Args:
            url: URL to fetch and parse

        Returns:
            BeautifulSoup object on success, None on failure
        """
        response = self.http_service.fetch(url)
        if not response:
            self.logger.error("Failed to fetch page: %s", url)
            return None

        return self.parser.parse(response.text)

    def build_full_url(self, path):
        """
        Build a full URL from a relative path.

        Args:
            path: Relative path to join with base URL

        Returns:
            Full URL
        """
        return self.http_service.build_url(self.base_url, path)

    def extract_text(self, element, strip=True):
        """
        Safely extract text from an element.

        Args:
            element: BeautifulSoup element
            strip: Whether to strip whitespace

        Returns:
            Text content or empty string if element is None
        """
        if element is None:
            return ""

        text = element.get_text()
        return text.strip() if strip else text

    def find_link_by_text(self, soup, text, partial=True):
        """
        Find a link by its text content.

        Args:
            soup: BeautifulSoup object to search in
            text: Text to search for
            partial: Whether to match partial text

        Returns:
            URL of the first matching link, or None if not found
        """
        for link in soup.find_all('a'):
            link_text = self.extract_text(link)

            if (partial and text.lower() in link_text.lower()) or \
               (not partial and text.lower() == link_text.lower()):
                href = link.get('href')
                if href:
                    return self.build_full_url(href)

        return None

    def find_link_by_href(self, soup, href_pattern):
        """
        Find a link by a pattern in its href attribute.

        Args:
            soup: BeautifulSoup object to search in
            href_pattern: String pattern to search for in href

        Returns:
            URL of the first matching link, or None if not found
        """
        for link in soup.find_all('a'):
            href = link.get('href')

            if href and href_pattern in href:
                return self.build_full_url(href)

        return None
