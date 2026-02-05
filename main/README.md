# AT_TEST - PitchBook Scraper

A refactored, class-based web scraping framework for PitchBook company data.

## Project Structure

```
at_test/
├── driver/
│   ├── __init__.py          # Driver package initialization
│   ├── get_driver.py        # StartDriver class for Selenium management
│   └── utils.py             # Utility functions (Chrome version detection)
├── config.json              # Configuration file (headless mode, etc.)
├── logger.py                # CustomLogger class for logging
├── details.py               # ScrapeCompanyDetails class for data extraction
├── main.py                  # PitchBookScraper class - main orchestrator
└── README.md                # This file
```

## Key Features

### 1. **Class-Based Architecture**
All major components are now organized as classes:

- **`StartDriver`** (`driver/get_driver.py`): Manages Selenium WebDriver instances
  - Supports both normal and undetected Chrome drivers
  - Handles driver configuration, cookies, downloads
  - Provides utility methods for element interaction

- **`ScrapeCompanyDetails`** (`details.py`): Handles company detail scraping
  - Uses `StartDriver` for driver management
  - Extracts data from PitchBook pages
  - Handles captcha detection and retries

- **`PitchBookScraper`** (`main.py`): Main orchestrator class
  - Manages the entire scraping workflow
  - Handles database connections
  - Coordinates search and data collection

### 2. **Improved Driver Management**

The `StartDriver` class provides:
- Automatic driver initialization with retry logic
- Support for headless and non-headless modes
- Proxy configuration
- Cookie management
- File download handling
- Element interaction utilities

### 3. **Better Error Handling**

- Comprehensive try-catch blocks
- Detailed logging at each step
- Automatic retries for failed operations
- Graceful degradation (saves to file if DB unavailable)

### 4. **Modular Design**

Each module has a clear responsibility:
- `driver/` - WebDriver management
- `details.py` - Data extraction logic
- `main.py` - Workflow orchestration
- `logger.py` - Logging functionality

## Usage

### Basic Usage

```python
from main import PitchBookScraper

# Create scraper instance
scraper = PitchBookScraper(
    batch_size=5,      # Companies per batch
    max_runs=50        # Number of runs
)

# Run the scraper
scraper.run()
```

### Custom MongoDB Connection

```python
scraper = PitchBookScraper(
    mongo_uri="mongodb://user:pass@localhost:27017/",
    batch_size=10,
    max_runs=100
)
scraper.run()
```

### Scrape Single Company

```python
from details import scrape_company
from logger import CustomLogger

logger = CustomLogger(log_folder="logs")
url = "https://pitchbook.com/profiles/company/233787-07"
data = scrape_company(url, logger)
```

### Use StartDriver Directly

```python
from driver import StartDriver

# Create driver instance
driver_manager = StartDriver(driver_type='undetected')
driver = driver_manager.get_driver()

# Use driver
driver.get("https://example.com")

# Clean up
driver_manager.CloseDriver()
```

## Configuration

Edit `config.json` to change settings:

```json
{
    "headless": false
}
```

- `headless`: Set to `true` for headless mode, `false` for visible browser

## Database Schema

### Source Collection: `STARTUPSCRAPERDATA.OrganiztionDetails`
Used to read company names for searching.

### Target Collection: `PITCHBOOK.OrganizationDetails`
Stores scraped company data with fields:
- `company_name`
- `source_url`
- `scraped_at`
- `overview`
- `general_info`
- `valuation_funding`
- `cap_table`
- `competitors`
- `investors`
- `patents`
- `faqs`
- `related_research`

## Logging

Logs are stored in the `logs/` directory:
- `info.log` - Information messages
- `error.log` - Error messages
- `warning.log` - Warning messages
- `general.log` - All messages

Logs older than 7 days are automatically cleaned up.

## Key Improvements Over Original Code

1. **Class-Based Design**: Better organization and reusability
2. **Centralized Driver Management**: `StartDriver` class handles all driver operations
3. **Better Separation of Concerns**: Each class has a single responsibility
4. **Improved Error Handling**: More robust error handling and logging
5. **Easier Testing**: Classes can be easily mocked and tested
6. **Better Documentation**: Comprehensive docstrings and comments
7. **Configuration Management**: Centralized config file
8. **Retry Logic**: Built-in retry mechanisms for failed operations

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- `selenium` - Web automation
- `undetected-chromedriver` - Bypass detection
- `selenium-stealth` - Additional stealth features
- `beautifulsoup4` - HTML parsing
- `pymongo` - MongoDB driver
- `requests` - HTTP requests
- `pytz` - Timezone handling

## Running the Scraper

```bash
# Navigate to the at_test directory
cd /home/riken/pitchbook/at_test

# Run the scraper
python main.py
```

## Notes

- The scraper includes anti-detection measures (stealth, random delays)
- Proxy support is built-in (configure in `details.py`)
- Captcha detection and retry logic is implemented
- Data is saved to MongoDB or local JSON files as fallback
