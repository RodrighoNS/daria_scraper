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
        super().__init__(http_service, parser, logger, config)

        # Define the character info keys we're looking for
        self.character_info_keys = [
            "Full Name:", "Current Age:", "Current Vocation:",
            "Season One Age:", "Season One Vocation:", "Parents:",
            "Siblings:", "First Appearance:", "Status at end of series:",
            "Daria on herself:"
        ]

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

        # Extract character information
        self._extract_character_details(soup, character)

        # Extract character description
        self._extract_character_description(soup, character)

        return character

    def _extract_character_details(self, soup, character):
        """
        Extract specific character details from the soup.

        Args:
            soup: BeautifulSoup object of the character page
            character: Character model to populate
        """
        # Initialize mapping from info keys to model attributes
        key_to_attr = {
            "Full Name:": "full_name",
            "Current Age:": "current_age",
            "Current Vocation:": "current_vocation",
            "Season One Age:": "season_one_age",
            "Season One Vocation:": "season_one_vocation",
            "Parents:": "parents",
            "Siblings:": "siblings",
            "First Appearance:": "first_appearance",
            "Status at end of series:": "status_at_end_of_series",
            "Daria on herself:": "character_on_self"
        }

        # Method 1: Look for bold/strong tags containing our keys
        for bold in soup.find_all(['strong', 'b']):
            bold_text = self.extract_text(bold)

            for key in self.character_info_keys:
                if key.lower() in bold_text.lower():
                    # Found a key, now get the value from parent element
                    parent = bold.parent
                    if parent:
                        parent_text = self.extract_text(parent)
                        if key in parent_text:
                            value = parent_text.split(key, 1)[1].strip()
                            attr_name = key_to_attr.get(key)
                            if attr_name:
                                setattr(character, attr_name, value)
                                self.logger.info("Found %s: %s", key, value)

        # Method 2: Look for text containing our keys anywhere
        for key in self.character_info_keys:
            attr_name = key_to_attr.get(key)
            if attr_name and not getattr(character, attr_name):
                # Only if we haven't found it yet
                for element in soup.find_all(text=re.compile(re.escape(key), re.IGNORECASE)):
                    parent = element.parent
                    if parent:
                        parent_text = self.extract_text(parent)
                        if key in parent_text:
                            value = parent_text.split(key, 1)[1].strip()
                            setattr(character, attr_name, value)
                            self.logger.info("Found %s: %s", key, value)
                            break

        # Method 3: Look for paragraphs containing our keys
        for p in soup.find_all('p'):
            p_text = self.extract_text(p)
            for key in self.character_info_keys:
                attr_name = key_to_attr.get(key)
                if attr_name and not getattr(character, attr_name) and key in p_text:
                    value = p_text.split(key, 1)[1].strip()
                    setattr(character, attr_name, value)
                    self.logger.info("Found %s: %s", key, value)

    def _extract_character_description(self, soup, character):
        """
        Extract character description paragraphs.

        Args:
            soup: BeautifulSoup object of the character page
            character: Character model to populate
        """
        # Look for longer paragraphs that don't contain our info keys
        for p in soup.find_all('p'):
            text = self.extract_text(p)

            # Consider it a description if it's a longer paragraph
            # and doesn't contain any of our specific info keys
            if text and len(text) > 50 and not any(key in text for key in self.character_info_keys):
                character.description.append(text)

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
