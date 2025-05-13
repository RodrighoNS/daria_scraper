"""
Main entry point for the Daria Outpost Reborn web scraper.
This script provides a focused approach to scrape Daria's
character information and alter ego images.
"""
import time
import logging
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup

# Import from our package
from daria_scraper import config

class DariaScraper:
    """Scraper class focused on extracting Daria's character info and alter ego images."""

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

    def scrape_daria_character_with_alter_egos(self):
        """
        Scrape Daria's character information and her alter ego images.
        This is a focused approach for the first iteration.
        """
        self.logger.info("Starting focused scrape of Daria's character and alter egos")

        # Step 1: Start with the characters page
        characters_url = "https://outpost-daria-reborn.info/characters.html"
        response = self.fetch_page(characters_url)
        if not response:
            self.logger.error("Failed to retrieve the characters page.")
            return None

        soup = self.parse_html(response.text)

        # Step 2: Find Daria's character page link
        daria_link = None
        for link in soup.select("a"):
            href = link.get('href')
            text = link.text.strip()

            if href and ("ch_daria.html" in href or text.lower() == "daria"):
                daria_link = href
                if not daria_link.startswith(('http://', 'https://')):
                    daria_link = urljoin(self.target['base_url'], daria_link)
                self.logger.info("Found Daria's character page: %s", daria_link)
                break

        if not daria_link:
            self.logger.error("Could not find Daria's character page link.")
            return None

        # Step 3: Scrape Daria's character page
        response = self.fetch_page(daria_link)
        if not response:
            self.logger.error("Failed to retrieve Daria's character page.")
            return None

        daria_soup = self.parse_html(response.text)

        # Extract basic character info
        daria_data = {
            "url": daria_link,
            "alter_egos_images": []
        }

        # Extract all the specific character information
        character_info_keys = [
            "Full Name:", "Current Age:", "Current Vocation:",
            "Season One Age:", "Season One Vocation:", "Parents:",
            "Siblings:", "First Appearance:", "Status at end of series:",
            "Daria on herself:"
        ]

        # Initialize all keys with empty values
        for key in character_info_keys:
            clean_key = key.replace(":", "").lower().replace(" ", "_")
            daria_data[clean_key] = ""

        # Improved extraction method for character details
        # First, look for strong/b tags that might contain our keys
        for bold in daria_soup.find_all(['strong', 'b']):
            bold_text = bold.get_text(strip=True)

            # Check if this bold text contains any of our keys
            for key in character_info_keys:
                if key.lower() in bold_text.lower():
                    # Found a key, now get the value
                    # It might be in the parent element after the bold tag
                    parent = bold.parent
                    if parent:
                        # Get the text of the parent and split by the bold text
                        parent_text = parent.get_text(strip=True)
                        if key in parent_text:
                            value = parent_text.split(key, 1)[1].strip()
                            clean_key = key.replace(":", "").lower().replace(" ", "_")
                            daria_data[clean_key] = value
                            self.logger.info("Found %s: %s", key, value)

        # If we still have empty values, try a more aggressive approach
        # Look for text containing our keys anywhere in the document
        for key in character_info_keys:
            clean_key = key.replace(":", "").lower().replace(" ", "_")
            if not daria_data[clean_key]:  # Only if we haven't found it yet
                for element in daria_soup.find_all(text=re.compile(re.escape(key), re.IGNORECASE)):
                    # Get the full text of the parent element
                    parent = element.parent
                    if parent:
                        parent_text = parent.get_text(strip=True)
                        # Split by the key to get the value
                        if key in parent_text:
                            value = parent_text.split(key, 1)[1].strip()
                            daria_data[clean_key] = value
                            self.logger.info("Found %s: %s", key, value)
                            break

        # Special handling for common patterns
        # Sometimes the information is in a specific format like "Key: Value"
        for p in daria_soup.find_all('p'):
            p_text = p.get_text(strip=True)
            for key in character_info_keys:
                if key in p_text and not daria_data[key.replace(":", "").lower().replace(" ", "_")]:
                    value = p_text.split(key, 1)[1].strip()
                    clean_key = key.replace(":", "").lower().replace(" ", "_")
                    daria_data[clean_key] = value
                    self.logger.info("Found %s: %s", key, value)

        # Get character description paragraphs
        daria_data["description"] = []
        for p in daria_soup.select("p"):
            text = p.get_text(strip=True)
            if text and len(text) > 50:  # Assuming descriptions are longer paragraphs
                # Skip paragraphs that contain our specific keys
                if not any(key in text for key in character_info_keys):
                    daria_data["description"].append(text)

        # Step 4: Find link to Daria's alter egos
        alter_egos_link = None
        alter_egos_fragment = None

        for link in daria_soup.select("a"):
            href = link.get('href')
            text = link.text.strip()

            if href and "art_alter-egos.html" in href:
                alter_egos_link = href
                # Extract the fragment identifier (#daria)
                if "#" in href:
                    alter_egos_fragment = href.split("#")[1]

                if not alter_egos_link.startswith(('http://', 'https://')):
                    alter_egos_link = urljoin(self.target['base_url'], alter_egos_link)

                self.logger.info("Found Daria's alter egos link: %s", alter_egos_link)
                break

        if not alter_egos_link:
            self.logger.error("Could not find Daria's alter egos link.")
            # We'll still return the character data we have
            return daria_data

        # Step 5: Scrape the alter egos page for Daria's section
        response = self.fetch_page(alter_egos_link)
        if not response:
            self.logger.error("Failed to retrieve the alter egos page.")
            return daria_data

        alter_egos_soup = self.parse_html(response.text)

        # Find Daria's section using the fragment identifier
        daria_section = None
        if alter_egos_fragment:
            # Try to find by id first
            daria_section = alter_egos_soup.find(id=alter_egos_fragment)

            # If not found by id, try to find by name attribute (for <a name="daria">)
            if not daria_section:
                daria_section = alter_egos_soup.find("a", {"name": alter_egos_fragment})

        # If we found Daria's section, extract images from it and following siblings
        # until we hit another section
        if daria_section:
            self.logger.info("Found Daria's alter egos section with fragment: %s", alter_egos_fragment)

            # Start from Daria's section and collect images until next section
            current = daria_section
            in_daria_section = True

            while current and in_daria_section:
                # Check if this is a new section header
                if current != daria_section and current.name in ['h1', 'h2', 'h3', 'h4'] and current.get_text(strip=True):
                    in_daria_section = False
                    break

                # Extract images from this element
                for img in current.find_all('img'):
                    src = img.get('src')
                    if src:
                        # Get parent link if image is within an <a> tag
                        parent_link = img.find_parent('a')
                        if parent_link and parent_link.get('href'):
                            href = parent_link.get('href')
                            if not href.startswith(('http://', 'https://')):
                                href = urljoin(self.target['base_url'], href)

                            # Only include the link key as requested
                            image_data = {
                                "link": href,
                                "width": img.get('width', ''),
                                "height": img.get('height', '')
                            }

                            daria_data["alter_egos_images"].append(image_data)
                        else:
                            # If no parent link, use the image source as the link
                            if not src.startswith(('http://', 'https://')):
                                src = urljoin(self.target['base_url'], src)

                            image_data = {
                                "link": src,
                                "width": img.get('width', ''),
                                "height": img.get('height', '')
                            }

                            daria_data["alter_egos_images"].append(image_data)

                # Move to next sibling
                current = current.next_sibling
        else:
            # If we couldn't find Daria's specific section, just look for any images
            # that might be related to Daria
            self.logger.warning("Could not find Daria's specific section with fragment: %s", alter_egos_fragment)
            self.logger.info("Searching for Daria-related images in the entire page")

            for img in alter_egos_soup.find_all('img'):
                src = img.get('src')

                # Only include images that seem related to Daria
                if src and 'daria' in src.lower():
                    # Get parent link if image is within an <a> tag
                    parent_link = img.find_parent('a')
                    if parent_link and parent_link.get('href'):
                        href = parent_link.get('href')
                        if not href.startswith(('http://', 'https://')):
                            href = urljoin(self.target['base_url'], href)

                        # Only include the link key as requested
                        image_data = {
                            "link": href,
                            "width": img.get('width', ''),
                            "height": img.get('height', '')
                        }

                        daria_data["alter_egos_images"].append(image_data)
                    else:
                        # If no parent link, use the image source as the link
                        if not src.startswith(('http://', 'https://')):
                            src = urljoin(self.target['base_url'], src)

                        image_data = {
                            "link": src,
                            "width": img.get('width', ''),
                            "height": img.get('height', '')
                        }

                        daria_data["alter_egos_images"].append(image_data)

        self.logger.info("Found %d alter ego images for Daria", len(daria_data["alter_egos_images"]))
        return daria_data

    def display_daria_json(self, daria_data):
        """Display Daria's character data in JSON format for debugging."""
        if not daria_data:
            print("No data found for Daria.")
            return

        # Convert to JSON and print
        json_data = json.dumps(daria_data, indent=2)
        print("\n" + "="*70)
        print("Daria Character Data with Alter Ego Images")
        print("="*70)
        print(json_data)
        print("="*70)

    def run(self):
        """Run the scraper with focus on Daria's character and alter ego images."""
        self.logger.info("Starting Daria web scraper with focus on Daria's character and alter egos")

        # Scrape Daria's character info and alter ego images
        daria_data = self.scrape_daria_character_with_alter_egos()

        if daria_data:
            # Display Daria's data in JSON format
            self.display_daria_json(daria_data)

            # Save the data
            output_file = self.save_data(
                daria_data,
                f"{config.OUTPUT_CONFIG['FILENAME_PREFIX']}_daria_character"
            )

            if output_file:
                self.logger.info("Daria's character data saved to %s", output_file)
        else:
            self.logger.error("Failed to scrape Daria's character information")

        self.logger.info("Scraping complete")
        return True

def main():
    """Main entry point for the scraper."""
    scraper = DariaScraper()
    scraper.run()

if __name__ == "__main__":
    main()
