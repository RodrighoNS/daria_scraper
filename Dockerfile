FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-dev

# Copy project files
COPY daria_scraper/ ./daria_scraper/

# Run the script
CMD ["python", "-m", "daria_scraper.main"]
