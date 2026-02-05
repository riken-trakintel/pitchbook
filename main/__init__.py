"""
AT_TEST - PitchBook Scraping Framework

A refactored, class-based web scraping framework for PitchBook company data.

Main Classes:
    - PitchBookScraper: Main orchestrator for scraping workflow
    - ScrapeCompanyDetails: Handles individual company scraping
    - StartDriver: Manages Selenium WebDriver instances
    - CustomLogger: Logging functionality

Example:
    >>> from main import PitchBookScraper
    >>> scraper = PitchBookScraper(batch_size=5, max_runs=10)
    >>> scraper.run()
"""

__version__ = "1.0.0"
__author__ = "Riken"

from .main import PitchBookScraper
from .details import ScrapeCompanyDetails, scrape_company, save_to_db
from .driver import StartDriver
from .logger import CustomLogger

__all__ = [
    'PitchBookScraper',
    'ScrapeCompanyDetails',
    'scrape_company',
    'save_to_db',
    'StartDriver',
    'CustomLogger'
]
