"""
HTML parser for processing web page content.
"""

import re
from bs4 import BeautifulSoup

class HtmlParser:
    """Parser for HTML content with utility methods for common operations."""

    def __init__(self, parser='html.parser'):
        """
        Initialize the HTML parser.

        Args:
            parser: BeautifulSoup parser to use (default: 'html.parser')
        """
        self.parser_type = parser

    def parse(self, html_content):
        """
        Parse HTML content using BeautifulSoup.

        Args:
            html_content: Raw HTML content as string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, self.parser_type)

    def find_element_by_text(self, soup, text, tag=None, partial=True):
        """
        Find an element by its text content.

        Args:
            soup: BeautifulSoup object to search in
            text: Text to search for
            tag: Specific tag to search (optional)
            partial: Whether to match partial text

        Returns:
            Matching element or None if not found
        """
        elements = soup.find_all(tag) if tag else soup.find_all()

        for element in elements:
            if not element.string:
                continue

            element_text = element.string.strip()

            if (partial and text.lower() in element_text.lower()) or \
               (not partial and text.lower() == element_text.lower()):
                return element

        return None

    def find_element_by_regex(self, soup, pattern, tag=None):
        """
        Find an element by regex pattern in its text.

        Args:
            soup: BeautifulSoup object to search in
            pattern: Regex pattern to match
            tag: Specific tag to search (optional)

        Returns:
            Matching element or None if not found
        """
        regex = re.compile(pattern)
        return soup.find(tag, text=regex) if tag else soup.find(text=regex)

    def extract_table_data(self, table):
        """
        Extract data from an HTML table.

        Args:
            table: BeautifulSoup table element

        Returns:
            List of dictionaries with table data
        """
        if not table:
            return []

        # Extract headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

        # Extract rows
        rows = []
        data_rows = table.find_all('tr')[1:] if headers else table.find_all('tr')

        for row in data_rows:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]

            if headers:
                # Create dictionary mapping headers to cell values
                row_data = {headers[i]: cells[i] for i in range(min(len(headers), len(cells)))}
            else:
                # If no headers, just use list of cell values
                row_data = cells

            rows.append(row_data)

        return rows

    def extract_image_data(self, img):
        """
        Extract data from an image element.

        Args:
            img: BeautifulSoup img element

        Returns:
            Dictionary with image data
        """
        if not img:
            return {}

        data = {
            'src': img.get('src', ''),
            'alt': img.get('alt', ''),
            'width': img.get('width', ''),
            'height': img.get('height', '')
        }

        # Check if image is inside a link
        parent_link = img.find_parent('a')
        if parent_link:
            data['link'] = parent_link.get('href', '')

        return data

    def get_section_by_id_or_anchor(self, soup, section_id):
        """
        Get a section by ID or anchor name.

        Args:
            soup: BeautifulSoup object to search in
            section_id: ID or anchor name to find

        Returns:
            Section element or None if not found
        """
        # Try to find by id
        section = soup.find(id=section_id)

        # If not found, try to find by anchor name
        if not section:
            section = soup.find('a', {'name': section_id})

        return section
