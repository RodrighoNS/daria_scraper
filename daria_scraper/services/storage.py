"""
Storage service for saving scraped data to files.
"""

import json
import csv
from datetime import datetime
from pathlib import Path

class Storage:
    """Service for storing scraped data to files."""

    def __init__(self, config, logger):
        """
        Initialize the storage service.

        Args:
            config: Configuration object with output settings
            logger: Logger instance for recording activity
        """
        self.config = config
        self.logger = logger
        self.data_dir = Path(config.OUTPUT_CONFIG["DATA_DIR"])
        self.data_dir.mkdir(exist_ok=True)

    def save_json(self, data, filename_prefix):
        """
        Save data as a JSON file with timestamp.

        Args:
            data: Data to save (must be JSON serializable)
            filename_prefix: Prefix for the filename

        Returns:
            Path to the saved file on success, None on failure
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = self.data_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info("Data saved to %s", filepath)
            return filepath
        except (IOError, TypeError, ValueError) as e:
            self.logger.error("Error saving data: %s", e)
            return None

    def save_csv(self, data, filename_prefix, fieldnames=None):
        """
        Save data as a CSV file with timestamp.

        Args:
            data: List of dictionaries to save
            filename_prefix: Prefix for the filename
            fieldnames: List of field names for CSV header (optional)

        Returns:
            Path to the saved file on success, None on failure
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = self.data_dir / filename

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not fieldnames and data:
                    # Use keys from first item if fieldnames not provided
                    fieldnames = data[0].keys()

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            self.logger.info("Data saved to %s", filepath)
            return filepath
        except (IOError, TypeError, ValueError, csv.Error) as e:
            self.logger.error("Error saving CSV data: %s", e)
            return None
