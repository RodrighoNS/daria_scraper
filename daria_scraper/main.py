"""
Main entry point for the Daria Outpost Reborn web scraper.
This script provides a structured approach to scrape content from the site.
"""

# import os
import sys
import time
import logging
import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin#, urlparse
import requests
from bs4 import BeautifulSoup

# Import from our package
from daria_scraper import config

class DariaScraper:
    """Main scraper class for the Daria Outpost Reborn website."""

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

    def extract_site_structure(self, soup):
        """Extract the site's navigation structure."""
        nav_links = []
        nav_selector = self.target["selectors"]["navigation"]

        for link in soup.select(nav_selector):
            href = link.get('href')
            if href:
                # Handle relative URLs
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(self.target['base_url'], href)

                nav_links.append({
                    "text": link.text.strip(),
                    "url": href
                })

        self.logger.info("Found %d navigation links", len(nav_links))
        return nav_links

    def extract_page_content(self, soup, url):
        """Extract content from a page."""
        page_data = {
            "url": url,
            "title": soup.title.text.strip() if soup.title else "No title",
            "headings": [],
            "links": [],
            "content_snippets": []
        }

        # Extract headings
        for heading in soup.select(self.target["selectors"]["titles"]):
            page_data["headings"].append({
                "level": heading.name,
                "text": heading.text.strip()
            })

        # Extract links (excluding navigation links)
        for link in soup.select(self.target["selectors"]["links"]):
            # Skip if the link is likely navigation
            if link.parent.name == 'nav' or 'menu' in link.parent.get('class', []):
                continue

            href = link.get('href')
            if href and not href.startswith('#'):
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(self.target['base_url'], href)

                page_data["links"].append({
                    "text": link.text.strip(),
                    "url": href
                })

        # Extract content snippets
        for p in soup.select(self.target["selectors"]["content"]):
            text = p.text.strip()
            if text:  # Only add non-empty paragraphs
                page_data["content_snippets"].append(text)

        return page_data

    def extract_episode_info(self, soup):
        """Extract episode information if present on the page."""
        episodes = []
        for episode in soup.select(self.target["selectors"]["episodes"]):
            # This is a placeholder - adjust according to actual site structure
            episode_data = {
                "title": episode.find('h3').text.strip() if episode.find('h3') else "Unknown",
                "description": episode.find('p').text.strip() if episode.find('p') else ""
            }
            episodes.append(episode_data)

        if episodes:
            self.logger.info("Found %d episodes", len(episodes))

        return episodes

    def save_data(self, data, filename_prefix):
        """Save scraped data to file in the specified format."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_format = config.OUTPUT_CONFIG["FORMAT"].lower()
        filename = f"{filename_prefix}_{timestamp}.{output_format}"
        filepath = self.data_dir / filename

        self.logger.info("Saving data to %s", filepath)

        if output_format == 'csv':
            self._save_as_csv(data, filepath)
        elif output_format == 'json':
            self._save_as_json(data, filepath)
        else:
            self.logger.error("Unsupported output format: %s", output_format)
            return None

        return filepath

    def _save_as_csv(self, data, filepath):
        """Save data as CSV file."""
        # For this example, we'll save the links
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if 'links' in data and data['links']:
                fieldnames = ['text', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for link in data['links']:
                    writer.writerow(link)
            elif 'nav_links' in data and data['nav_links']:
                fieldnames = ['text', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for link in data['nav_links']:
                    writer.writerow(link)

    def _save_as_json(self, data, filepath):
        """Save data as JSON file."""
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2)

    def display_summary(self, data):
        """Display a summary of the scraped data."""
        print("\n" + "="*60)
        print(f"Scraping Summary for {self.target['name']}")
        print("="*60)

        if 'page_content' in data:
            page = data['page_content']
            print(f"Page Title: {page['title']}")
            print(f"URL: {page['url']}")
            print(f"Found {len(page['headings'])} headings")
            print(f"Found {len(page['links'])} content links")
            print(f"Extracted {len(page['content_snippets'])} content snippets")

        if 'nav_links' in data:
            print(f"\nSite Navigation: {len(data['nav_links'])} links")
            for i, link in enumerate(data['nav_links'][:5], 1):
                print(f"  {i}. {link['text']} ({link['url']})")
            if len(data['nav_links']) > 5:
                print(f"  ...and {len(data['nav_links']) - 5} more")

        if 'episodes' in data and data['episodes']:
            print(f"\nEpisodes: {len(data['episodes'])} found")
            for i, episode in enumerate(data['episodes'][:3], 1):
                print(f"  {i}. {episode['title']}")
            if len(data['episodes']) > 3:
                print(f"  ...and {len(data['episodes']) - 3} more")

        print("="*60)

    def run(self):
        """Run the scraper to extract information from the Daria site."""
        self.logger.info("Starting Daria web scraper")

        # Fetch the home page
        response = self.fetch_page(self.target['url'])
        if not response:
            self.logger.error("Failed to retrieve the home page. Exiting.")
            return False

        # Parse the home page
        soup = self.parse_html(response.text)

        # Extract data
        result = {}

        # Extract navigation structure
        result['nav_links'] = self.extract_site_structure(soup)

        # Extract main page content
        result['page_content'] = self.extract_page_content(soup, self.target['url'])

        # Extract episode info if present
        episodes = self.extract_episode_info(soup)
        if episodes:
            result['episodes'] = episodes

        # Save the results
        output_file = self.save_data(
            result,
            f"{config.OUTPUT_CONFIG['FILENAME_PREFIX']}_{self.target['name'].lower().replace(' ', '_')}"
        )

        if output_file:
            self.logger.info("Data saved to %s", output_file)

        # Display summary
        self.display_summary(result)

        self.logger.info("Scraping complete")
        return True

def main():
    """Main function to run the Daria scraper."""
    scraper = DariaScraper()
    success = scraper.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
