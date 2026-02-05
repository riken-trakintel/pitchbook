# Quick Start Guide - AT_TEST

## Installation

1. **Navigate to the at_test directory:**
```bash
cd /home/riken/pitchbook/at_test
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json` to set headless mode:
```json
{
    "headless": false
}
```

- `false` = visible browser (for debugging)
- `true` = headless mode (for production)

## Quick Examples

### 1. Run Full Scraper (Recommended for Production)

```python
python main.py
```

This will:
- Connect to MongoDB
- Fetch 5 companies per batch
- Run 50 batches
- Save data to database

### 2. Test with Single Company

```python
python examples.py
```

This runs a simple test to scrape one company.

### 3. Custom Configuration

Create a file `my_scraper.py`:

```python
from main import PitchBookScraper

# Custom configuration
scraper = PitchBookScraper(
    batch_size=10,     # Process 10 companies per batch
    max_runs=5         # Run 5 times
)

scraper.run()
```

Run it:
```bash
python my_scraper.py
```

## Common Use Cases

### Use Case 1: Scrape Specific Company

```python
from details import scrape_company
from logger import CustomLogger

logger = CustomLogger(log_folder="logs")
url = "https://pitchbook.com/profiles/company/233787-07"
data = scrape_company(url, logger)

print(f"Company: {data.get('company_name')}")
```

### Use Case 2: Search for Companies

```python
from main import PitchBookScraper

scraper = PitchBookScraper()
urls = scraper.get_companies_list("QNu Labs")

for url in urls:
    print(url)
```

### Use Case 3: Custom Driver Usage

```python
from driver import StartDriver

driver_manager = StartDriver(driver_type='undetected')
driver = driver_manager.get_driver()

driver.get("https://pitchbook.com")
print(driver.title)

driver_manager.CloseDriver()
```

## Monitoring

### Check Logs

```bash
# View all logs
tail -f logs/general.log

# View only errors
tail -f logs/error.log

# View only info
tail -f logs/info.log
```

### Check Saved Data

If database is unavailable, data is saved to:
```
json_data/scraped_*.json
```

## Troubleshooting

### Issue: "Driver not starting"

**Solution:** Check Chrome version
```bash
google-chrome --version
```

Update `driver/utils.py` if needed.

### Issue: "MongoDB connection failed"

**Solution:** Check connection string in `main.py` or pass custom URI:
```python
scraper = PitchBookScraper(
    mongo_uri="mongodb://user:pass@localhost:27017/"
)
```

### Issue: "Captcha detected"

**Solution:** The scraper has built-in retry logic. If it persists:
1. Increase sleep times in `details.py`
2. Use different proxies
3. Try non-headless mode

### Issue: "Module not found"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

## File Structure Quick Reference

```
at_test/
├── main.py              # Main scraper class (PitchBookScraper)
├── details.py           # Company detail scraper (ScrapeCompanyDetails)
├── driver/
│   ├── get_driver.py    # Driver manager (StartDriver)
│   └── utils.py         # Utilities
├── logger.py            # Logger class
├── config.json          # Configuration
├── examples.py          # Usage examples
└── README.md            # Full documentation
```

## Next Steps

1. **Read the README:** `cat README.md`
2. **Check examples:** `python examples.py`
3. **Review refactoring:** `cat REFACTORING_SUMMARY.md`
4. **Start scraping:** `python main.py`

## Support

For detailed documentation, see:
- `README.md` - Full documentation
- `REFACTORING_SUMMARY.md` - Changes from original code
- `examples.py` - 6 usage examples

## Tips

1. **Start with small batches** for testing:
   ```python
   scraper = PitchBookScraper(batch_size=1, max_runs=1)
   ```

2. **Use non-headless mode** for debugging:
   ```json
   {"headless": false}
   ```

3. **Check logs regularly** to monitor progress

4. **Save important data** to database for persistence

5. **Use examples.py** to learn the API

6. **Run scripts in parallel**: You can now run multiple scraping scripts at the same time. The framework automatically isolates their Chrome profiles and driver binaries.

Happy Scraping! 🚀
