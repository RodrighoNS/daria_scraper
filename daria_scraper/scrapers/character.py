"""
Character scraper for extracting character information from the Daria website.
"""

import re
from daria_scraper.scrapers.base import BaseScraper
from daria_scraper.models.character import Character

class CharacterScraper(BaseScraper):
    """Specialized scraper for character information."""

    def __init__(self, http_service, parser, logger, config):
        """
        Initialize the character scraper.

        Args:
            http_service: Service for making HTTP requests
            parser: HTML parser for processing responses
            logger: Logger instance for recording activity
            config: Configuration object
        """
        BaseScraper.__init__(self, http_service, parser, logger, config)

    def find_character_link(self, characters_url, character_name):
        """
        Find a character's page link from the characters index page.

        Args:
            characters_url: URL of the characters index page
            character_name: Name of the character to find

        Returns:
            URL of the character's page or None if not found
        """
        self.logger.info("Looking for %s's character page link", character_name)

        soup = self.fetch_and_parse(characters_url)
        if not soup:
            return None

        # Try to find by href pattern first (more specific)
        href_pattern = f"ch_{character_name.lower()}.html"
        character_link = self.find_link_by_href(soup, href_pattern)

        # If not found by href, try by text
        if not character_link:
            character_link = self.find_link_by_text(soup, character_name)

        if character_link:
            self.logger.info("Found %s's character page: %s", character_name, character_link)
        else:
            self.logger.error("Could not find %s's character page link", character_name)

        return character_link

    def scrape_character_info(self, character_url):
        """
        Scrape character information from a character page.

        Args:
            character_url: URL of the character's page

        Returns:
            Character model with extracted information
        """
        self.logger.info("Scraping character info from: %s", character_url)

        soup = self.fetch_and_parse(character_url)
        if not soup:
            return None

        # Create a character model
        character = Character(character_url)

        # Extract character name
        self._extract_character_name(soup, character)

        return character

    def _extract_character_name(self, soup, character):
        """
        Extract character name from the soup.

        Args:
            soup: BeautifulSoup object of the character page
            character: Character model to populate
        """
        # Look for the full name in bold text
        for bold in soup.find_all(['strong', 'b']):
            bold_text = self.extract_text(bold)
            if "Full Name:" in bold_text:
                parent = bold.parent
                if parent:
                    parent_text = self.extract_text(parent)
                    if "Full Name:" in parent_text:
                        full_name = parent_text.split("Full Name:", 1)[1].strip()
                        # Clean up the name if it contains other text
                        if "Current Age:" in full_name:
                            full_name = full_name.split("Current Age:", 1)[0].strip()
                        character.full_name = full_name
                        self.logger.info("Found Full Name: %s", full_name)
                        return

        # If name not found yet, try broader search
        for element in soup.find_all(text=re.compile("Full Name:", re.IGNORECASE)):
            parent = element.parent
            if parent:
                parent_text = self.extract_text(parent)
                if "Full Name:" in parent_text:
                    full_name = parent_text.split("Full Name:", 1)[1].strip()
                    if "Current Age:" in full_name:
                        full_name = full_name.split("Current Age:", 1)[0].strip()
                    character.full_name = full_name
                    self.logger.info("Found Full Name: %s", full_name)
                    return

    def find_alter_egos_link(self, character_url):
        """
        Find the link to alter egos page from a character page.

        Args:
            character_url: URL of the character's page

        Returns:
            Tuple of (alter_egos_url, fragment_identifier) or (None, None) if not found
        """
        self.logger.info("Looking for alter egos link from: %s", character_url)

        soup = self.fetch_and_parse(character_url)
        if not soup:
            return None, None

        # Look for links containing "alter-egos" in href
        for link in soup.find_all('a'):
            href = link.get('href')

            if href and "art_alter-egos.html" in href:
                # Extract the fragment identifier if present
                fragment = None
                if "#" in href:
                    href, fragment = href.split("#", 1)

                full_url = self.build_full_url(href)
                self.logger.info("Found alter egos link: %s (fragment: %s)", full_url, fragment)
                return full_url, fragment

        self.logger.error("Could not find alter egos link")
        return None, None

    def scrape_alter_egos(self, alter_egos_url, fragment, character):
        """
        Scrape alter egos images from the alter egos page.

        Args:
            alter_egos_url: URL of the alter egos page
            fragment: Fragment identifier for the character's section
            character: Character model to update with alter ego images

        Returns:
            Updated character model with alter egos images
        """
        self.logger.info("Scraping alter egos from: %s (fragment: %s)", alter_egos_url, fragment)

        soup = self.fetch_and_parse(alter_egos_url)
        if not soup:
            return character

        # Get character name part for filtering images
        character_id = self._get_character_id(character.full_name)

        # Find the section for this character
        section = None
        if fragment:
            # Try to find by fragment first
            section = soup.find(id=fragment)
            if not section:
                # Try to find anchor with name attribute
                section = soup.find('a', {'name': fragment})
                if section:
                    section = section.parent

        # If section not found, search the entire page
        if not section:
            section = soup

        # Extract all image links that match the character
        for img in section.find_all('img'):
            src = img.get('src')
            if src and f"{character_id}_" in src.lower():
                width = img.get('width', '')
                height = img.get('height', '')

                full_url = self.build_full_url(src)

                # Add image info to character
                image_info = {
                    "link": full_url,
                    "width": width,
                    "height": height
                }
                character.alter_egos_images.append(image_info)
                self.logger.info("Found alter ego image: %s", full_url)

        return character

    def _get_character_id(self, full_name):
        """
        Get character ID from full name for matching alter ego images.

        Args:
            full_name: Character's full name

        Returns:
            Character ID string for matching images
        """
        if not full_name:
            return ""

        # Extract first name from full name
        first_name = full_name.split()[0].lower()

        # Special case handling (example: "daria" -> "daria")
        return first_name
