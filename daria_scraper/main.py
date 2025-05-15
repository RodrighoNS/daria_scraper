"""
Main entry point for the Daria Outpost Reborn web scraper.
This script provides a focused approach to scrape character
information and alter ego images.
"""
import time
import logging
import json
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
# import re
import requests
from bs4 import BeautifulSoup

# Import from our package
from daria_scraper import config

class DariaScraper:
    """Scraper class focused on extracting character info and alter ego images."""

    def __init__(self):
        """Initialize the scraper with configuration settings."""
        self.logger = self._setup_logging()
        self.target = config.TARGETS[0]
        self.session = requests.Session()
        self.session.headers.update(config.REQUEST_CONFIG["HEADERS"])
        self.data_dir = Path(config.OUTPUT_CONFIG["DATA_DIR"])
        self.data_dir.mkdir(exist_ok=True)

        self.logger.info("Initialized scraper for %s", self.target['name'])

    def _setup_logging(self):
        """Set up logging configuration."""
        log_config = config.LOGGING_CONFIG
        logging.basicConfig(
            level=getattr(logging, log_config["LEVEL"]),
            format=log_config["LOG_FORMAT"],
            handlers=[
                logging.FileHandler(log_config["LOG_FILE"]),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger("daria_scraper")

    def fetch_page(self, url, retry_count=0):
        """Fetch a page with retry logic."""
        try:
            self.logger.info("Requesting: %s", url)
            response = self.session.get(
                url,
                timeout=config.REQUEST_CONFIG["TIMEOUT"]
            )
            response.raise_for_status()

            # Add delay to avoid hammering the server
            time.sleep(config.REQUEST_CONFIG["REQUEST_DELAY"])

            return response
        except requests.exceptions.RequestException as e:
            self.logger.error("Error fetching %s: %s", url, e)
            if retry_count < config.REQUEST_CONFIG["RETRIES"]:
                self.logger.info("Retrying (%d/%d)...", retry_count + 1, config.REQUEST_CONFIG['RETRIES'])
                time.sleep(config.REQUEST_CONFIG["RETRY_DELAY"])
                return self.fetch_page(url, retry_count + 1)
            else:
                self.logger.error("Max retries reached. Giving up.")
                return None

    def parse_html(self, html_content):
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html_content, 'html.parser')

    def save_data(self, data, filename_prefix):
        """Save the scraped data to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = self.data_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            self.logger.error("Error saving data: %s", e)
            return None

    def find_character_page(self, character_name):
        """
        Find a character's page URL from the characters index page.

        Args:
            character_name: Name of the character to find (e.g., 'daria', 'jane')

        Returns:
            Character page URL or None if not found
        """
        characters_url = urljoin(self.target['base_url'], "characters.html")
        self.logger.info("Looking for %s's character page on %s", character_name, characters_url)

        response = self.fetch_page(characters_url)
        if not response:
            self.logger.error("Failed to retrieve the characters page.")
            return None

        soup = self.parse_html(response.text)

        # First, try to find by specific href pattern (e.g., ch_daria.html)
        for link in soup.select("a"):
            href = link.get('href', '')
            if href and f"ch_{character_name.lower()}.html" in href.lower():
                char_url = urljoin(self.target['base_url'], href)
                self.logger.info("Found %s's character page by href: %s", character_name, char_url)
                return char_url

        # If not found by href, try by link text
        for link in soup.select("a"):
            text = link.text.strip()
            if text.lower() == character_name.lower():
                href = link.get('href', '')
                if href:
                    char_url = urljoin(self.target['base_url'], href)
                    self.logger.info("Found %s's character page by text: %s", character_name, char_url)
                    return char_url

        self.logger.error("Could not find %s's character page", character_name)
        return None

    def extract_character_name(self, soup):
        """
        Extract a character's full name from their page.

        Args:
            soup: BeautifulSoup object of the character's page

        Returns:
            Character's full name or empty string if not found
        """
        # Look for "Full Name:" in bold text
        for bold in soup.find_all(['strong', 'b']):
            if "Full Name:" in bold.get_text():
                # Get the parent element that contains the full text
                parent = bold.parent
                if parent:
                    full_text = parent.get_text()
                    # Extract the name after "Full Name:"
                    if "Full Name:" in full_text:
                        name_part = full_text.split("Full Name:", 1)[1].strip()
                        # If there's another field after the name, cut it off
                        if "Current Age:" in name_part:
                            name_part = name_part.split("Current Age:", 1)[0].strip()
                        return name_part

        return ""

    def find_alter_egos_link(self, soup, character_name):
        """
        Find the alter egos page link and fragment identifier from a character page.

        Args:
            soup: BeautifulSoup object of the character's page
            character_name: Name of the character for logging

        Returns:
            Tuple of (alter_egos_url, fragment_identifier) or (None, None) if not found
        """
        alter_egos_link = None
        fragment = None

        # Look for links to the alter egos page
        for link in soup.select("a"):
            href = link.get('href', '')
            if href and "art_alter-egos.html" in href:
                # If the link has a fragment identifier (#daria), extract it
                if "#" in href:
                    base_href, fragment = href.split("#", 1)
                    alter_egos_link = urljoin(self.target['base_url'], base_href)
                else:
                    alter_egos_link = urljoin(self.target['base_url'], href)

                self.logger.info("Found alter egos link for %s: %s (fragment: %s)",
                                character_name, alter_egos_link, fragment)
                return alter_egos_link, fragment

        self.logger.warning("Could not find alter egos link for %s", character_name)
        return None, None

    def extract_character_alter_egos(self, soup, character_name, fragment):
        """
        Extract alter ego images for a specific character from the alter egos page.

        Args:
            soup: BeautifulSoup object of the alter egos page
            character_name: Name of the character to extract images for
            fragment: Fragment identifier for the character's section

        Returns:
            List of alter ego image data for the character
        """
        alter_egos = []
        character_id = character_name.lower()

        # Try to find the character's section using the fragment
        section = None
        if fragment:
            # First try by id
            section = soup.find(id=fragment)

            # Then try by name attribute (for <a name="...">)
            if not section:
                anchor = soup.find("a", {"name": fragment})
                if anchor:
                    section = anchor.parent

        # If we found a specific section, search within it
        elements_to_search = section.find_all('img') if section else soup.find_all('img')

        for img in elements_to_search:
            src = img.get('src', '')
            if src and f"{character_id}_" in src.lower():
                # This is an image for our character
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(self.target['base_url'], src)

                image_data = {
                    "link": src,
                    "width": img.get('width', ''),
                    "height": img.get('height', '')
                }

                alter_egos.append(image_data)

        self.logger.info("Found %d alter ego images for %s", len(alter_egos), character_name)
        return alter_egos

    def scrape_character(self, character_name):
        """
        Scrape a character's basic info and alter ego images.

        Args:
            character_name: Name of the character to scrape

        Returns:
            Dictionary with character data or None if failed
        """
        self.logger.info("Starting scrape for character: %s", character_name)

        # Step 1: Find the character's page
        character_url = self.find_character_page(character_name)
        if not character_url:
            return None

        # Step 2: Get the character's page content
        response = self.fetch_page(character_url)
        if not response:
            self.logger.error("Failed to retrieve %s's character page", character_name)
            return None

        soup = self.parse_html(response.text)

        # Step 3: Extract the character's full name
        full_name = self.extract_character_name(soup)
        if not full_name:
            self.logger.warning("Could not extract full name for %s, using provided name", character_name)
            full_name = character_name.title()  # Capitalize first letter

        # Step 4: Find link to alter egos page
        alter_egos_url, fragment = self.find_alter_egos_link(soup, character_name)

        alter_egos_images = []
        if alter_egos_url:
            # Step 5: Get the alter egos page
            response = self.fetch_page(alter_egos_url)
            if response:
                alter_egos_soup = self.parse_html(response.text)

                # Step 6: Extract character's alter ego images
                alter_egos_images = self.extract_character_alter_egos(
                    alter_egos_soup, character_name, fragment
                )
            else:
                self.logger.error("Failed to retrieve the alter egos page")

        # Create the character data structure
        character_data = {
            "url": character_url,
            "full_name": full_name,
            "alter_egos_images": alter_egos_images
        }

        return character_data

    def display_character_json(self, character_data):
        """Display character data in JSON format for debugging."""
        if not character_data:
            print("No data found for character.")
            return

        # Convert to JSON and print
        json_data = json.dumps(character_data, indent=2)
        print("\n" + "="*70)
        print(f"{character_data.get('full_name', 'Character')} Data with Alter Ego Images")
        print("="*70)
        print(json_data)
        print("="*70)

    def run(self, character_name=None):
        """
        Run the scraper for a specific character or default to Daria.

        Args:
            character_name: Name of the character to scrape (defaults to 'daria')

        Returns:
            True if successful, False otherwise
        """
        # Default to Daria if no character specified
        character_name = character_name or "daria"
        self.logger.info("Starting web scraper for character: %s", character_name)

        # Scrape character info and alter ego images
        character_data = self.scrape_character(character_name)

        if character_data:
            # Display character data in JSON format
            self.display_character_json(character_data)

            # Save the data
            output_file = self.save_data(
                character_data,
                f"{config.OUTPUT_CONFIG['FILENAME_PREFIX']}_{character_name.lower()}_character"
            )

            if output_file:
                self.logger.info("%s's character data saved to %s", character_name, output_file)
                return True
        else:
            self.logger.error("Failed to scrape %s's character information", character_name)

        self.logger.info("Scraping complete")
        return False


def main():
    """Main entry point for the scraper."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Scrape Daria character information")
    parser.add_argument("character", nargs="?", default="daria",
                        help="Name of the character to scrape (default: daria)")
    args = parser.parse_args()

    # Create and run the scraper
    scraper = DariaScraper()
    scraper.run(args.character)

if __name__ == "__main__":
    main()
