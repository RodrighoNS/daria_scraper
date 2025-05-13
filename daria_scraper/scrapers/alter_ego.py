"""
Alter ego scraper for extracting character alter ego images from the Daria website.
"""

from daria_scraper.scrapers.base import BaseScraper

class AlterEgoScraper(BaseScraper):
    """Specialized scraper for character alter ego images."""

    def __init__(self, http_service, parser, logger, config):
        """
        Initialize the alter ego scraper.

        Args:
            http_service: Service for making HTTP requests
            parser: HTML parser for processing responses
            logger: Logger instance for recording activity
            config: Configuration object
        """
        super().__init__(http_service, parser, logger, config)
        self.base_url = config.get('alter_ego_base_url')

    def scrape_alter_egos(self, alter_egos_url, fragment=None):
        """
        Scrape alter ego images for a character.

        Args:
            alter_egos_url: URL of the alter egos page
            fragment: Fragment identifier for the character's section (optional)

        Returns:
            List of alter ego image data dictionaries
        """
        self.logger.info("Scraping alter ego images from: %s (fragment: %s)",
                         alter_egos_url, fragment)

        soup = self.fetch_and_parse(alter_egos_url)
        if not soup:
            return []

        alter_ego_images = []

        # If we have a fragment identifier, try to find that specific section
        if fragment:
            section = self._find_character_section(soup, fragment)
            if section:
                alter_ego_images = self._extract_images_from_section(section)
            else:
                self.logger.warning("Could not find section with fragment: %s", fragment)
                # Fall back to searching the entire page for images related to the character
                alter_ego_images = self._extract_images_by_character_name(soup, fragment)
        else:
            # If no fragment, just extract all images
            self.logger.info("No fragment identifier provided, extracting all images")
            alter_ego_images = self._extract_all_images(soup)

        self.logger.info("Found %d alter ego images", len(alter_ego_images))
        return alter_ego_images

    def _find_character_section(self, soup, fragment):
        """
        Find a character's section using the fragment identifier.

        Args:
            soup: BeautifulSoup object of the alter egos page
            fragment: Fragment identifier for the character's section

        Returns:
            Section element or None if not found
        """
        # Try to find by id first
        section = soup.find(id=fragment)

        # If not found by id, try to find by name attribute (for <a name="fragment">)
        if not section:
            section = soup.find("a", {"name": fragment})

        # If we found an anchor but not a section, use the parent or next elements
        if section and section.name == 'a':
            # Try parent first
            if section.parent and section.parent.name != 'body':
                return section.parent

            # Otherwise use the anchor as the starting point
            return section

        return section

    def _extract_images_from_section(self, section):
        """
        Extract images from a section and its siblings until the next section.

        Args:
            section: Starting section element

        Returns:
            List of image data dictionaries
        """
        images = []
        current = section
        in_section = True

        while current and in_section:
            # Check if this is a new section header (stop when we hit one)
            if current != section and current.name in ['h1', 'h2', 'h3', 'h4'] and self.extract_text(current):
                in_section = False
                break

            # Extract images from this element
            for img in current.find_all('img'):
                image_data = self._extract_image_data(img)
                if image_data:
                    images.append(image_data)

            # Move to next sibling
            current = current.next_sibling

        return images

    def _extract_images_by_character_name(self, soup, character_name):
        """
        Extract images related to a character by name.

        Args:
            soup: BeautifulSoup object of the alter egos page
            character_name: Name of the character

        Returns:
            List of image data dictionaries
        """
        images = []

        # Look for images with character name in src, alt, or parent text
        for img in soup.find_all('img'):
            src = img.get('src', '').lower()
            alt = img.get('alt', '').lower()

            # Check if image seems related to the character
            if character_name.lower() in src or character_name.lower() in alt:
                image_data = self._extract_image_data(img)
                if image_data:
                    images.append(image_data)
                continue

            # Check parent element text
            parent = img.parent
            if parent:
                parent_text = self.extract_text(parent).lower()
                if character_name.lower() in parent_text:
                    image_data = self._extract_image_data(img)
                    if image_data:
                        images.append(image_data)

        return images

    def _extract_all_images(self, soup):
        """
        Extract all images from the page.

        Args:
            soup: BeautifulSoup object of the alter egos page

        Returns:
            List of image data dictionaries
        """
        images = []

        for img in soup.find_all('img'):
            image_data = self._extract_image_data(img)
            if image_data:
                images.append(image_data)

        return images

    def _extract_image_data(self, img):
        """
        Extract data from an image element.

        Args:
            img: BeautifulSoup img element

        Returns:
            Image data dictionary or None if invalid
        """
        src = img.get('src')
        if not src:
            return None

        # Get parent link if image is within an <a> tag
        parent_link = img.find_parent('a')

        if parent_link and parent_link.get('href'):
            href = parent_link.get('href')
            link = self.build_full_url(href)

            # Only include the link key as requested
            image_data = {
                "link": link,
                "width": img.get('width', ''),
                "height": img.get('height', '')
            }
        else:
            # If no parent link, use the image source as the link
            src_url = self.build_full_url(src)

            image_data = {
                "link": src_url,
                "width": img.get('width', ''),
                "height": img.get('height', '')
            }

        return image_data
