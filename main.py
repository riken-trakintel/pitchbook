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

logger = CustomLogger(log_folder="logs")

masterclient = MongoClient("mongodb://admin9:i38kjmx35@localhost:27017/?authSource=admin&authMechanism=SCRAM-SHA-256&readPreference=primary&tls=true&tlsAllowInvalidCertificates=true&directConnection=true", serverSelectionTimeoutMS=5000)
masterclient.admin.command('ping')
clientDB = masterclient.PITCHBOOK
data_collection = clientDB['OrganizationDetails']

masterdb = masterclient.STARTUPSCRAPERDATA
org_collection = masterdb['OrganiztionDetails']
stats_collection = masterdb['run_stats']
logger.info("Connected to MongoDB successfully.")

def read_company_name(numberofrecords=10):
    if org_collection is None:
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

def quit(driver):
    """Quit driver and cleanup"""
    try:
        if driver:
            driver.quit()
            logger.info("✓ Driver quit successfully")
    except Exception as e:
        logger.error(f"✗ Quit failed: {e}")
        
def get_companies_list(search):
    """
    Search PitchBook for a company name and return a list of profile URLs.
    """
    driver = None
    company_urls = []
    
    for _ in range(20):
        try:
            url = 'https://pitchbook.com/profiles/search?q=' + search
            driver = uc.Chrome(options=get_options(), version_main=143)
            stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
            
            logger.info(f"Searching PitchBook for: {search} (Title: {driver.title})")
            
            for __ in range(5):
                driver.get(url)
                driver.get(url)
                sleep_random(8, 15, for_reason="waiting for search results")
                page_source = driver.page_source
                if "Verify you are human" in page_source:
                    logger.warning("Captcha detected during search!")
                    continue
                else:
                    break
                
            try:
                links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/profiles/company/']")
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if href and '/profiles/company/' in href:
                            clean_url = href.split('?')[0].split('#')[0]
                            if clean_url not in company_urls:
                                company_urls.append(clean_url)
                    except:
                        quit(driver)
                        continue
                
                if not company_urls:
                    logger.warning(f"No profile links found on search page for {search}. Saving page for debug.")
                else:
                    logger.info(f"Found {len(company_urls)} potential matches for {search}")
                
                if company_urls :
                    return company_urls
                else:
                    quit(driver)
                    return []
            except Exception as e:
                logger.error(f"Error parsing search results: {e}")
                quit(driver)
                continue
        except Exception as e:
            logger.error(f"Error in search: {e}")
            quit(driver)
        finally:
            quit(driver)

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
            try:
                logger.info(f"Scraping detailed info for: {company_url}")
                data = scrape_company(company_url, logger)
                
                if data:
                    if data_collection is not None:
                        save_to_db(data, data_collection, stats_collection, logger)
                        logger.info(f"Successfully saved {search} data to DB")
                    else:
                        filename = f"json_data/scraped_{normalize_key(search)}.json"
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                        logger.info(f"DB unavailable. Saved {search} data to local file: {filename}")
                else:
                    logger.warning(f"Failed to scrape data for {company_url}")
                
                sleep_random(10, 20, for_reason="throttle between company profiles")
            except Exception as e:
                logger.error(f"Error scraping {company_url}: {e}")

if __name__ == "__main__":
    for run in range(50):
        try:
            logger.info(f"Starting run #{run + 1}")
            collect_page_details()
        except Exception as e:
            logger.error(f"Main loop error on run {run}: {e}")
            time.sleep(30)
