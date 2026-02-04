import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time, random, re, os, json
import logging
from pymongo import MongoClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from selenium_stealth import stealth


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

PROXIES = [
    "37.48.118.90:13082",
    "83.149.70.159:13082"
]



def get_proxies():
    prx = random.choice(PROXIES)
    return {"http": f"http://{prx}", "https": f"http://{prx}"}


def sleep_random(min_sec=3, max_sec=6, for_reason=""):
    """Sleep for a random duration between min_sec and max_sec."""
    sleep_time = random.uniform(min_sec, max_sec)
    if for_reason:
        # Check if logger is passed or use print
        try:
            logging.info(f"Sleeping for {sleep_time:.2f} seconds for {for_reason}")
        except:
            print(f"Sleeping for {sleep_time:.2f} seconds for {for_reason}")
    else:
        try:
            logging.info(f"Sleeping for {sleep_time:.2f} seconds")
        except:
            print(f"Sleeping for {sleep_time:.2f} seconds")
    time.sleep(sleep_time)

def get_options():
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    prx = random.choice(PROXIES)
    options.add_argument(f"--proxy-server=http://{prx}")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-site-isolation-trials")
    return options

def fetch_page(url, retries=3, timeout=20):
    for _ in range(retries):
        try:
            res = requests.get(
                url,
                headers=HEADERS,
                timeout=timeout,
                proxies=get_proxies()
            )
            if res.status_code == 200:
                return res.text
        except requests.RequestException:
            pass
        time.sleep(1)
    return None


def normalize_key(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

def clean_text(el):
    return el.get_text(" ", strip=True) if el else None



def extract_pitchbook_overview(soup):
    overview = {}
    items = soup.select('[data-pp-overview-item]')
    for item in items:
        label_elem = item.select_one('.dont-break.text-small')
        value_elem = item.select_one('.pp-overview-item__title')
        if label_elem and value_elem:
            key = normalize_key(label_elem.text)
            overview[key] = value_elem.text.strip()
    return overview

def extract_pitchbook_general_info(soup):
    info = {}
    gen_info_sec = soup.select_one('.general-info')
    if not gen_info_sec:
        return info
    
    desc_elem = gen_info_sec.select_one('.pp-description_text')
    if desc_elem:
        info['description'] = clean_text(desc_elem)
        
    contact_items = gen_info_sec.select('.pp-contact-info_item')
    for item in contact_items:
        label_elem = item.select_one('h5, .font-weight-bold')
        if label_elem:
            label = label_elem.text.strip()
            value_elem = item.select_one('a, .font-weight-regular')
            if value_elem:
                info[normalize_key(label)] = value_elem.get('title') or value_elem.text.strip()
    
    office_elem = gen_info_sec.select_one('.pp-contact-info_corporate-office')
    if office_elem:
        address_lines = [li.text.strip() for li in office_elem.select('ul li')]
        info['corporate_office'] = ", ".join(address_lines)
        
    socials = {}
    for social in gen_info_sec.select('.info-item__social div a'):
        platform = social.get('aria-label', '').replace(' link', '').lower()
        if platform:
            socials[platform] = social.get('href')
    if socials:
        info['social_links'] = socials
        
    return info

def extract_pitchbook_table(section_soup):
    if not section_soup:
        return []
    table = section_soup.find('table')
    if not table:
        return []
    
    headers = [normalize_key(th.text) for th in table.find_all('th')]
    rows = []
    for tr in table.find('tbody').find_all('tr'):
        cells = tr.find_all('td')
        if len(cells) == len(headers):
            row_data = {}
            for i, cell in enumerate(cells):
                if cell.select_one('.data-table__gray-box'):
                    row_data[headers[i]] = "[Locked/Blurred]"
                else:
                    row_data[headers[i]] = cell.get('title') or cell.text.strip()
            rows.append(row_data)
    return rows

def extract_pitchbook_faqs(soup):
    faqs = []
    faq_items = soup.select('.pp-faqs-table li')
    for item in faq_items:
        q = item.select_one('h3')
        a = item.select_one('p')
        if q and a:
            faqs.append({
                'question': q.text.strip(),
                'answer': a.text.strip()
            })
    return faqs

def extract_pitchbook_data(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    company_name = soup.select_one('.pp-search-wrap__title')
    company_name = company_name.text.strip() if company_name else "Unknown"
    
    data = {
        'company_name': company_name,
        'source_url': url,
        'scraped_at': datetime.now().isoformat(),
        'overview': extract_pitchbook_overview(soup),
        'general_info': extract_pitchbook_general_info(soup),
        'valuation_funding': extract_pitchbook_table(soup.select_one('#funding')),
        'cap_table': extract_pitchbook_table(soup.select_one('#captable')),
        'competitors': extract_pitchbook_table(soup.select_one('#competitors')),
        'investors': extract_pitchbook_table(soup.select_one('#investors')),
        'patents': extract_pitchbook_table(soup.select_one('#patents')),
        'faqs': extract_pitchbook_faqs(soup)
    }
    
    # Try to extract research items
    research = []
    research_items = soup.select('#research .pp-related-research__item')
    for item in research_items:
        title = item.select_one('.pp-related-research__item-title')
        date = item.select_one('.pp-related-research__item-release')
        link = item.get('href')
        if title:
            research.append({
                'title': title.text.strip(),
                'date': date.text.strip() if date else None,
                'url': "https://pitchbook.com" + link if link else None
            })
    data['related_research'] = research
    
    return data

def extract_company_data(html_content, url):
    if 'pp-overview' in html_content or 'pitchbook' in html_content.lower():
        return extract_pitchbook_data(html_content, url)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    return extract_pitchbook_data(html_content, url)

def save_to_db(data, collection, stats_collection, logger, unique_field="source_url"):
    """
    Insert or update company data in MongoDB.

    Args:
        data (dict): Scraped company data
        collection (pymongo.collection.Collection): MongoDB collection
        unique_field (str): Field used to identify uniqueness (default: source_url)
        logger: CustomLogger instance
    """
    if not data or unique_field not in data:
        if logger:
            logger.error("Invalid data or missing unique field")
        else:
            print("Invalid data or missing unique field")
        return

    data["updated_at"] = datetime.utcnow()

    query = {unique_field: data[unique_field]}

    update = {
        "$set": data,
        "$setOnInsert": {
            "created_at": datetime.utcnow()
        }
    }
    try:
        result = collection.update_one(
            query,
            update,
            upsert=True
        )

        if result.matched_count:
            if logger:
                logger.info(f"Updated existing document: {data[unique_field]}")
            else:
                print(f"Updated existing document: {data[unique_field]}")
        elif result.upserted_id:
            if stats_collection is not None:
                stats_collection.update_one(
                    {"_id": "update_run_stats"},
                    {"$inc": {"added_count": 1}}
                )
            if logger:
                logger.info(f"Inserted new document: {data[unique_field]}")
            else:
                print(f"Inserted new document: {data[unique_field]}")
    except Exception as e:
        if logger:
            logger.error(f"Error saving to DB: {e}")
        else:
            print(f"Error saving to DB: {e}")
        
class ScrapeCompanyDetails:
    def __init__(self, url, logger=None):
        self.url = url
        if not logger:
            from logger import CustomLogger
            logger = CustomLogger(log_folder="logs")
            
        self.logger = logger
        self.company_resource = None
        self.driver = None
        self.wait = ''
        self.get_driver_url()

    def find_element(self, locator: tuple[By, str], timeout: int = 10):
        """Find element with explicit wait"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator))
            return element
        except TimeoutException:
            self.logger.error(f"✗ Element not found: {locator}")
            return None
        except Exception as e:
            self.logger.error(f"✗ Error finding element {locator}: {e}")
            return None
    
    def find_elements(self, locator: tuple[By, str], timeout: int = 10) -> list:
        """Find multiple elements with explicit wait"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            elements = wait.until(EC.presence_of_all_elements_located(locator))
            return elements
        except TimeoutException:
            self.logger.warning(f"⚠ No elements found: {locator}")
            return []
        except Exception as e:
            self.logger.error(f"✗ Error finding elements {locator}: {e}")
            return []
    
    def wait_for_element(self, locator: tuple[By, str], timeout: int = 10, condition="presence"):
        """Wait for element with different conditions"""
        conditions = {
            "presence": EC.presence_of_element_located,
            "visible": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable
        }
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(conditions.get(condition, EC.presence_of_element_located)(locator))
            return element
        except TimeoutException:
            self.logger.error(f"✗ Element {condition} timeout: {locator}")
            return None
    
    def is_element_present(self, locator: tuple[By, str], timeout: int = 5) -> bool:
        """Check if element exists without raising exception"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def quit(self):
        """Quit driver and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("✓ Driver quit successfully")
        except Exception as e:
            self.logger.error(f"✗ Quit failed: {e}")
        
    def get_driver_url(self):
        for _ in range(20):
            self.driver = uc.Chrome(options=get_options(), version_main=143)
            self.wait = WebDriverWait(self.driver,  10)
            stealth(self.driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True )
            if not self.driver :
                continue
                
            for __ in range(5):
                self.driver.get(self.url)
                sleep_random(for_reason="driver get captcha")
                if "Verify you are human by completing the action below" in self.driver.find_element(By.TAG_NAME, 'body').text:
                    self.logger.warning("Captcha detected, retrying...")
                    sleep_random(5,10)
                    continue
                else :
                    break
            else :  
                self.quit()
                continue
            self.company_resource = self.driver.page_source
            return self.company_resource
        else :
            self.logger.error("Failed to bypass captcha after multiple attempts.")
        return None

    def get_company_resource(self):
        
        return self.company_resource

    def extract_company_data(self):
        page_source = self.driver.page_source 
        return extract_company_data(self.company_resource, self.url)

    def scrape(self):
        if self.logger:
            self.logger.info(f"Scraping company details: {self.url}")
        data = self.extract_company_data()
        self.quit()
        return data

def scrape_company(url, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)
        if not hasattr(logger, 'handlers') or not logger.handlers:
            logging.basicConfig(level=logging.INFO)
    
    data = {}
    for _ in range(3):
        scraper = ScrapeCompanyDetails(url, logger)
        data = scraper.scrape()
        if data['company_name'] == "Unknown":
            logger.info(f"could not sucessfully scraped data for {url}")
            continue
        else:
            break
        
    if data:
        if hasattr(logger, 'info'):
            logger.info(f"Successfully scraped data for {url}")
            return data
            
    else:
        if hasattr(logger, 'error'):
            logger.error(f"Failed to scrape data for {url}")
            return {}
    

if __name__ == "__main__":
    from pymongo import MongoClient
    from logger import CustomLogger
    logger = CustomLogger(log_folder="logs")
    masterclient = MongoClient("mongodb://admin9:i38kjmx35@localhost:27017/?authSource=admin&authMechanism=SCRAM-SHA-256&readPreference=primary&tls=true&tlsAllowInvalidCertificates=true&directConnection=true", serverSelectionTimeoutMS=5000)
    masterclient.admin.command('ping')
    clientDB = masterclient.PITCHBOOK
    data_collection = clientDB['OrganizationDetails']

    masterdb = masterclient.STARTUPSCRAPERDATA
    org_collection = masterdb['OrganiztionDetails']
    stats_collection = masterdb['run_stats']
    logger.info("Connected to MongoDB successfully.")
    sample_url = "https://pitchbook.com/profiles/company/279690-49"
    sample_url = "https://pitchbook.com/profiles/company/925292-08"
    sample_url = "https://pitchbook.com/profiles/company/41082-40"
    sample_url = "https://pitchbook.com/profiles/company/233787-07"
    data = scrape_company(sample_url)
    search = sample_url.split("/")[-1]
    if data:
        if data_collection is not None:
            save_to_db(data, data_collection, stats_collection, logger)
            logger.info(f"Successfully saved {search} data to DB")
        else:
            filename = f"scraped_{normalize_key(search)}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info(f"DB unavailable. Saved {search} data to local file: {filename}")
    else:
        logger.warning(f"Failed to scrape data for {sample_url}")
