# Daria Scraper

A web scraping tool built with Python and BeautifulSoup.<br>
Data extracted from https://outpost-daria-reborn.info, <br>
thanks to Kevin Bess (a.k.a. NeonHomer) for all his effort and dedication to the Daria community.

## Installation

This project uses Poetry for dependency management.

### Prerequisites

- Python 3.7 or higher
- Poetry ([installation guide](https://python-poetry.org/docs/#installation))

### Setup

1. Clone the repository:

```bash
git clone https://github.com/RodrighoNS/daria-scraper.git
cd daria-scraper
```

2. Install dependencies with Poetry:

```bash
poetry install
```

## Usage

### Basic Scraping

```bash
poetry run python -m daria_scraper.main
```

## Configuration Options

The scraper can be configured in `config.py`:

- `USER_AGENT`: Custom user agent for requests
- `REQUEST_DELAY`: Time between requests (in seconds)
- `TIMEOUT`: Request timeout
- `OUTPUT_FORMAT`: Data output format (csv/json)
- `DATA_DIR`: Directory for saved data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
