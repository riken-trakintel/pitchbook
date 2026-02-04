# Import necessary modules
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

# Initialize Logger
logger = CustomLogger(log_folder="logs")

# Database connections
try:
    masterclient = MongoClient("mongodb://admin9:i38kjmx35@localhost:27017/?authSource=admin&authMechanism=SCRAM-SHA-256&readPreference=primary&tls=true&tlsAllowInvalidCertificates=true&directConnection=true", serverSelectionTimeoutMS=5000)
    # Check connection
    masterclient.admin.command('ping')
    clientDB = masterclient.PITCHBOOK
    data_collection = clientDB['OrganizationDetails']

    masterdb = masterclient.STARTUPSCRAPERDATA
    org_collection = masterdb['OrganiztionDetails']
    stats_collection = masterdb['run_stats']
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    # Fallback or exit? For now, we'll try to continue but functions will likely fail
    org_collection = None
    data_collection = None
    stats_collection = None
print(f"DEBUG: data_collection is {data_collection}")

def read_company_name(numberofrecords=10):
    if org_collection is None:
        # Fallback to some sample data or empty list if DB is down
        logger.warning("DB unavailable, returning sample keywords.")
        return [{"organization_name": "QNu Labs"}]
        
    where_condition = {
        "corrupted_data": {"$ne": True},
        "financial": {"$exists": True, "$nin": [{}, None]}
    }
    try:
        pipeline = [{"$match": where_condition}, {"$sample": {"size": numberofrecords}}]
        random_documents = list(org_collection.aggregate(pipeline))
        return random_documents
    except Exception as e:
        logger.error(f"Error reading from DB: {e}")
        return []

def get_companies_list(search):
    """
    Search PitchBook for a company name and return a list of profile URLs.
    """
    driver = None
    try:
        url = 'https://pitchbook.com/profiles/search?q=' + search
        driver = uc.Chrome(options=get_options(), version_main=143)
        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
        
        logger.info(f"Searching PitchBook for: {search} (Title: {driver.title})")
        driver.get(url)
        sleep_random(8, 15, for_reason="waiting for search results")
        
        page_source = driver.page_source
        if "Verify you are human" in page_source or "captcha" in page_source.lower():
            logger.warning("Captcha detected during search!")
            # Save for debugging
            with open("search_captcha.html", "w", encoding="utf-8") as f: f.write(page_source)
            return []
            
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/profiles/company/']")
            company_urls = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/profiles/company/' in href:
                        # Normalize and deduplicate
                        clean_url = href.split('?')[0].split('#')[0]
                        if clean_url not in company_urls:
                            company_urls.append(clean_url)
                except:
                    continue
            
            if not company_urls:
                logger.warning(f"No profile links found on search page for {search}. Saving page for debug.")
                with open(f"search_debug_{normalize_key(search)}.html", "w", encoding="utf-8") as f: f.write(page_source)
            else:
                logger.info(f"Found {len(company_urls)} potential matches for {search}")
                
            return company_urls
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return []
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def collect_page_details():
    """
    Collect search results for keywords and scrape each company.
    """
    sleep_random(2, 5, for_reason="throttle between batches")
    
    keywords = read_company_name(numberofrecords=5)
    logger.info(f"Processing batch of {len(keywords)} companies")
    
    for key in keywords:
        search = str(key.get('organization_name', '')).strip()
        if not search:
            continue
            
        companies_url = get_companies_list(search)
        
        for company_url in companies_url:
            logger.info(f"Scraping detailed info for: {company_url}")
            
            data = scrape_company(company_url, logger)
            
            if data:
                # Save to database using save_to_db from z.py
                if data_collection:
                    save_to_db(data, data_collection, stats_collection, logger)
                    logger.info(f"Successfully saved {search} data to DB")
                else:
                    # Local fallback
                    filename = f"scraped_{normalize_key(search)}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    logger.info(f"DB unavailable. Saved {search} data to local file: {filename}")
            else:
                logger.warning(f"Failed to scrape data for {company_url}")
            
            # Sleep between individual company scrapes to be polite
            sleep_random(10, 20, for_reason="throttle between company profiles")

if __name__ == "__main__":
    # Main execution loop
    for run in range(50):
        try:
            logger.info(f"Starting run #{run + 1}")
            collect_page_details()
        except Exception as e:
            logger.error(f"Main loop error on run {run}: {e}")
            time.sleep(30) # Wait before retry on crash
