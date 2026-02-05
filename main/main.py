"""
Main module for PitchBook scraping with class-based architecture.
Manages the scraping workflow including search, data collection, and storage.
"""

import time
import datetime
import random
import logging
import os
import json
from pymongo import MongoClient
from details import scrape_company, save_to_db, get_options, sleep_random, PROXIES, normalize_key
from logger import CustomLogger
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from driver.get_driver import StartDriver


class PitchBookScraper:
    """
    Main scraper class for PitchBook company data.
    Manages database connections, driver instances, and scraping workflow.
    """
    
    def __init__(self, mongo_uri=None, batch_size=5, max_runs=50):
        """
        Initialize the PitchBook scraper.
        
        Args:
            mongo_uri (str): MongoDB connection URI
            batch_size (int): Number of companies to process per batch
            max_runs (int): Maximum number of scraping runs
        """
        self.logger = CustomLogger(log_folder="logs")
        self.batch_size = batch_size
        self.max_runs = max_runs
        
        # Driver management
        self.driver_instance = None
        self.driver = None
        
        # Database setup
        self._setup_database(mongo_uri)
        
    def _setup_database(self, mongo_uri):
        """Setup MongoDB connections"""
        if mongo_uri is None:
            mongo_uri = (
                "mongodb://admin9:i38kjmx35@localhost:27017/"
                "?authSource=admin&authMechanism=SCRAM-SHA-256"
                "&readPreference=primary&tls=true"
                "&tlsAllowInvalidCertificates=true&directConnection=true"
            )
        
        try:
            self.masterclient = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.masterclient.admin.command('ping')
            
            # PitchBook database
            clientDB = self.masterclient.PITCHBOOK
            self.data_collection = clientDB['OrganizationDetails']
            
            # Source database
            masterdb = self.masterclient.STARTUPSCRAPERDATA
            self.org_collection = masterdb['OrganiztionDetails']
            self.stats_collection = masterdb['run_stats']
            
            self.logger.info("✓ Connected to MongoDB successfully")
        except Exception as e:
            self.logger.error(f"✗ Failed to connect to MongoDB: {e}")
            self.data_collection = None
            self.org_collection = None
            self.stats_collection = None
    
    def start_driver(self):
        """Initialize and start the WebDriver using StartDriver"""
        try:
            self.driver_instance = StartDriver(driver_type='undetected')
            self.driver = self.driver_instance.get_driver()
            
            if self.driver:
                # Apply stealth settings
                stealth(
                    self.driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True
                )
                self.logger.info("✓ Driver started successfully")
                return True
            else:
                self.logger.error("✗ Failed to start driver")
                return False
        except Exception as e:
            self.logger.error(f"✗ Error starting driver: {e}")
            return False
    
    def close_driver(self):
        """Close the current driver instance"""
        try:
            if self.driver_instance:
                self.driver_instance.CloseDriver()
                self.driver = None
                self.driver_instance = None
                self.logger.info("✓ Driver closed successfully")
        except Exception as e:
            self.logger.error(f"✗ Error closing driver: {e}")
    
    def read_company_names(self, number_of_records=10):
        """
        Read company names from database.
        
        Args:
            number_of_records (int): Number of records to fetch
            
        Returns:
            list: List of company documents
        """
        if self.org_collection is None:
            self.logger.warning("DB unavailable, returning sample keywords")
            return [{"organization_name": "QNu Labs"}]
            
        where_condition = {
            "corrupted_data": {"$ne": True},
            "financial": {"$exists": True, "$nin": [{}, None]}
        }
        
        try:
            pipeline = [
                {"$match": where_condition},
                {"$sample": {"size": number_of_records}}
            ]
            random_documents = list(self.org_collection.aggregate(pipeline))
            self.logger.info(f"✓ Retrieved {len(random_documents)} companies from database")
            return random_documents
        except Exception as e:
            self.logger.error(f"✗ Error reading from DB: {e}")
            return []
    
    def get_companies_list(self, search: str) -> list:
        """
        Search PitchBook for a company name and return profile URLs.
        
        Args:
            search (str): Company name to search
            
        Returns:
            list: List of company profile URLs
        """
        company_urls = []
        
        for attempt in range(20):
            try:
                # Start new driver for each attempt
                if not self.start_driver():
                    continue
                
                url = 'https://pitchbook.com/profiles/search?q=' + search
                self.logger.info(f"Searching PitchBook for: {search}")
                
                # Try to load the search page
                for retry in range(5):
                    self.driver.get(url)
                    self.driver.get(url)  # Double load for stability
                    sleep_random(8, 15, for_reason="waiting for search results")
                    
                    page_source = self.driver.page_source
                    if "Verify you are human" in page_source:
                        self.logger.warning("Captcha detected during search!")
                        continue
                    else:
                        break
                else:
                    # All retries failed
                    self.close_driver()
                    continue
                
                # Extract company links
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/profiles/company/']")
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            if href and '/profiles/company/' in href:
                                clean_url = href.split('?')[0].split('#')[0]
                                if clean_url not in company_urls:
                                    company_urls.append(clean_url)
                        except Exception as e:
                            self.logger.warning(f"Error extracting URL: {e}")
                            continue
                    
                    if not company_urls:
                        self.logger.warning(f"No profile links found for {search}")
                    else:
                        self.logger.info(f"✓ Found {len(company_urls)} matches for {search}")
                    return company_urls
                        
                except Exception as e:
                    self.logger.error(f"Error parsing search results: {e}")
                    
            except Exception as e:
                self.logger.error(f"Error in search: {e}")
            finally:
                self.close_driver()
        
        return company_urls
    
    def scrape_company_details(self, company_url: str) -> dict:
        """
        Scrape details for a single company.
        
        Args:
            company_url (str): Company profile URL
            
        Returns:
            dict: Scraped company data
        """
        try:
            self.logger.info(f"Scraping detailed info for: {company_url}")
            data = scrape_company(company_url, self.logger)
            return data
        except Exception as e:
            self.logger.error(f"Error scraping {company_url}: {e}")
            return {}
    
    def save_company_data(self, data: dict, search: str):
        """
        Save company data to database or file.
        
        Args:
            data (dict): Company data to save
            search (str): Search term used (for filename)
        """
        if not data:
            self.logger.warning("No data to save")
            return
        
        if self.data_collection is not None:
            save_to_db(data, self.data_collection, self.stats_collection, self.logger)
            self.logger.info(f"✓ Successfully saved {search} data to DB")
        else:
            # Save to local file if DB unavailable
            os.makedirs("json_data", exist_ok=True)
            filename = f"json_data/scraped_{normalize_key(search)}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"DB unavailable. Saved {search} data to: {filename}")
    
    def process_batch(self):
        """Process a batch of companies"""
        sleep_random(2, 5, for_reason="throttle between batches")
        
        keywords = self.read_company_names(number_of_records=self.batch_size)
        self.logger.info(f"Processing batch of {len(keywords)} companies")
        
        for key in keywords:
            search = str(key.get('organization_name', '')).strip()
            if not search:
                continue
            
            # Get company URLs from search
            companies_url = self.get_companies_list(search)
            if not companies_url:
                self.logger.warning(f"No URLs found for {search}")
                continue
            
            # Scrape each company
            for company_url in companies_url:
                try:
                    data = self.scrape_company_details(company_url)
                    
                    if data:
                        self.save_company_data(data, search)
                    else:
                        self.logger.warning(f"Failed to scrape data for {company_url}")
                    
                    sleep_random(10, 20, for_reason="throttle between company profiles")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {company_url}: {e}")
    
    def run(self):
        """Main execution loop"""
        for run in range(self.max_runs):
            try:
                self.logger.info(f"{'='*60}")
                self.logger.info(f"Starting run #{run + 1} of {self.max_runs}")
                self.logger.info(f"{'='*60}")
                
                self.process_batch()
                
                self.logger.info(f"Completed run #{run + 1}")
                
            except Exception as e:
                self.logger.error(f"Main loop error on run {run + 1}: {e}")
                time.sleep(30)
        
        self.logger.info("All runs completed!")


# Legacy function-based interface (for backward compatibility)
def read_company_name(numberofrecords=10):
    """Legacy function - use PitchBookScraper class instead"""
    scraper = PitchBookScraper()
    return scraper.read_company_names(numberofrecords)


def quit_driver(driver):
    """Quit driver and cleanup"""
    try:
        if driver:
            driver.quit()
            print("✓ Driver quit successfully")
    except Exception as e:
        print(f"✗ Quit failed: {e}")


def get_companies_list(search):
    """Legacy function - use PitchBookScraper class instead"""
    scraper = PitchBookScraper()
    return scraper.get_companies_list(search)


def collect_page_details():
    """Legacy function - use PitchBookScraper class instead"""
    scraper = PitchBookScraper(batch_size=5)
    scraper.process_batch()


# Main execution
if __name__ == "__main__":
    # Create and run scraper
    scraper = PitchBookScraper(
        batch_size=5,
        max_runs=50
    )
    
    scraper.run()
