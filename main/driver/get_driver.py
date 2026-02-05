import json
import random
import os
import time
import requests
from .utils import get_chrome_version
from tqdm import tqdm

# Selenium imports
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException,
    ElementNotInteractableException,
    WebDriverException, 
    StaleElementReferenceException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
import shutil
import uuid

class StartDriver:
    """
    Selenium WebDriver manager class with support for both normal and undetected Chrome drivers.
    Provides utilities for element interaction, file downloads, and cookie management.
    """
    
    def __init__(self, driver_type='normal', instance_id=None):
        """
        Initialize the driver manager.
        
        Args:
            driver_type (str): Type of driver - 'normal' or 'undetected'
            instance_id (str, optional): Unique ID for this instance. If None, a random one will be generated.
        """
        self.driver_type = driver_type
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        
        # Define paths
        self.base_dir = os.getcwd()
        self.download_path = os.path.join(self.base_dir, 'downloads', self.instance_id)
        self.cookies_path = os.path.join(self.base_dir, 'cookies')
        self.temp_dir = os.path.join(self.base_dir, 'temp_drivers', self.instance_id)
        self.profile_dir = os.path.join(self.base_dir, 'profiles', self.instance_id)

        # Create directories
        # os.makedirs(self.download_path, exist_ok=True)
        # os.makedirs(self.cookies_path, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.profile_dir, exist_ok=True)
        
        self.driver = None
        self.options = None
        
        # Load config
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
            self.headless = config.get("headless", False)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}, using default headless=False")
            self.headless = False
    
    def driver_arguments(self):
        """Configure common Chrome driver arguments"""
        self.options.add_argument('--lang=en')  
        self.options.add_argument("--enable-webgl-draft-extensions")
        self.options.add_argument('--mute-audio')
        self.options.add_argument("--ignore-gpu-blocklist")
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--enable-javascript")
        self.options.add_argument("--enable-popup-blocking")
        
        # Instance isolation: unique profile directory
        self.options.add_argument(f'--user-data-dir={self.profile_dir}')
        
        if self.driver_type == 'normal':
            self.options.add_argument("--disable-blink-features=AutomationControlled") 
            self.options.add_argument("--incognito")
            self.options.add_argument('--start-maximized')
            # Exclude the collection of enable-automation switches 
            # self.options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
            # Turn-off userAutomationExtension 
            # self.options.add_experimental_option("useAutomationExtension", False) 
        # uc handles these natively, adding them manually can cause issues        
        prefs = {
            "credentials_enable_service": True,
            'profile.default_content_setting_values.automatic_downloads': 1,
            "download.default_directory": f"{self.download_path}",
            'download.prompt_for_download': False, 
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            "profile.password_manager_enabled": True
        }
        self.options.add_experimental_option("prefs", prefs)
        
    def get_driver(self):
        """
        Get a configured Chrome WebDriver instance.
        
        Returns:
            WebDriver: Configured Chrome WebDriver instance
        """
        if not self.headless:
            self.get_local_driver()
            return self.driver
        else:
            return self._get_headless_driver()
    
    def _get_headless_driver(self):
        """Get a headless Chrome driver"""
        user_agents = [
            f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(108,126)}.0.0.0 Safari/537.36',
            f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(108,126)}.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        ]

        for _ in range(30):
            try:
                if self.driver_type == 'normal':
                    from selenium import webdriver
                    user_agent = random.choice(user_agents)
                    self.options = webdriver.ChromeOptions()
                    self.options.add_argument(f'user-agent={user_agent}')
                    self.options.add_argument(f'--headless=new')
                    self.driver_arguments()
                    self.options.add_argument(f"download.default_directory={self.download_path}")

                    self.driver = webdriver.Chrome(options=self.options)
                    params = {
                        "behavior": "allow",
                        "downloadPath": self.download_path
                    }
                    self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                    return self.driver
                else:
                    import undetected_chromedriver as uc
                    user_agent = random.choice(user_agents)
                    self.options = uc.ChromeOptions()
                    self.options.add_argument(f'user-agent={user_agent}')
                    self.driver_arguments()
                    
                    # Ensure a unique driver executable for this instance to avoid race conditions
                    driver_executable_path = os.path.join(self.temp_dir, 'chromedriver')
                    
                    self.driver = uc.Chrome(
                        options=self.options, 
                        use_subprocess=True, 
                        headless=True, 
                        version_main=get_chrome_version()
                    )
                    params = {
                        "behavior": "allow",
                        "downloadPath": self.download_path
                    }
                    self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                    return self.driver
            except Exception as e:
                print(f"Error creating headless driver: {e}")
                continue
        
        return self.driver
        
    def get_local_driver(self):
        """
        Start a local (non-headless) WebDriver.
        
        Returns:
            WebDriver: Configured Chrome WebDriver instance
        """
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        ]
        
        for _ in range(30):
            try:
                if self.driver_type == 'normal':
                    from selenium import webdriver
                    user_agent = random.choice(user_agents)
                    self.options = webdriver.ChromeOptions()
                    self.options.add_argument(f'user-agent={user_agent}')
                    self.driver_arguments()
                    self.options.add_argument("--incognito")
                    self.options.add_argument(f"download.default_directory={self.download_path}")
                    
                    self.driver = webdriver.Chrome(options=self.options)
                    params = {
                        "behavior": "allow",
                        "downloadPath": self.download_path
                    }
                    self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                    return self.driver
                else:
                    import undetected_chromedriver as uc
                    user_agent = random.choice(user_agents)
                    self.options = uc.ChromeOptions()
                    self.options.add_argument(f'user-agent={user_agent}')
                    self.driver_arguments()

                    self.driver = uc.Chrome(use_subprocess=True, options=self.options, version_main=get_chrome_version())
                    params = {
                        "behavior": "allow",
                        "downloadPath": self.download_path
                    }
                    self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                    return self.driver
            except Exception as e:
                print(f"Error creating local driver: {e}")
                continue
        
        return self.driver
    
    def find_element(self, element, locator, locator_type=By.XPATH,
            page=None, timeout=10,
            condition_func=EC.presence_of_element_located,
            condition_other_args=tuple()):
        """
        Find an element with optional wait.
        
        Args:
            element (str): Element description for logging
            locator (str): Locator value
            locator_type (By): Selenium By type
            page (str): Page name for logging
            timeout (int): Wait timeout in seconds
            condition_func: Expected condition function
            condition_other_args: Additional arguments for condition
            
        Returns:
            WebElement or None
        """
        try:
            if timeout > 0:
                wait_obj = WebDriverWait(self.driver, timeout)
                ele = wait_obj.until(EC.presence_of_element_located((locator_type, locator)))
            else:
                print(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver.find_element(by=locator_type, value=locator)
            
            if page:
                print(f'Found the element "{element}" in the page "{page}"')
            else:
                print(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                print(f'Cannot find the element "{element}" in the page "{page}"')
            else:
                print(f'Cannot find the element: {element}')
            return None
                
    def click_element(self, element, locator, locator_type=By.XPATH, timeout=10):
        """
        Find and click an element.
        
        Args:
            element (str): Element description
            locator (str): Locator value
            locator_type (By): Selenium By type
            timeout (int): Wait timeout
            
        Returns:
            WebElement or None
        """
        ele = self.find_element(element, locator, locator_type, timeout=timeout)
        
        if ele:
            self.driver.execute_script('arguments[0].scrollIntoViewIfNeeded();', ele)
            self.ensure_click(ele)
            print(f'Clicked the element: {element}')
            return ele
        return None

    def input_text(self, text, element, locator, locator_type=By.XPATH,
            timeout=10, hide_keyboard=True):
        """
        Find an element and input text.
        
        Args:
            text (str): Text to input
            element (str): Element description
            locator (str): Locator value
            locator_type (By): Selenium By type
            timeout (int): Wait timeout
            hide_keyboard (bool): Whether to hide keyboard after input
            
        Returns:
            WebElement or None
        """
        ele = self.find_element(element, locator, locator_type=locator_type, timeout=timeout)
        
        if ele:
            for i in range(3):
                try: 
                    ele.send_keys(text)
                    print(f'Inputed "{text}" for the element: {element}')
                    return ele    
                except ElementNotInteractableException:
                    pass
        return None
    
    def scroll_down(self, px):
        """Scroll down by specified pixels"""
        self.driver.execute_script(f"window.scrollTo(0, {px})")
    
    def ensure_click(self, element: WebElement, timeout=3):
        """
        Ensure element is clicked, using JavaScript if normal click fails.
        
        Args:
            element (WebElement): Element to click
            timeout (int): Wait timeout
        """
        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(element))
            element.click()
        except WebDriverException:
            self.driver.execute_script("arguments[0].click();", element)
        
    def new_tab(self):
        """Open a new browser tab"""
        self.driver.find_element(By.XPATH, '/html/body').send_keys(Keys.CONTROL + 't')

    def random_sleep(self, a=3, b=7, reason=""):
        """
        Sleep for a random duration.
        
        Args:
            a (int): Minimum seconds
            b (int): Maximum seconds
            reason (str): Reason for sleeping (for logging)
        """
        random_time = random.randint(a, b)
        if reason:
            print(f'Time sleep randomly: {random_time} for {reason}')
        else:
            print(f'Time sleep randomly: {random_time}')
        time.sleep(random_time)

    def getvalue_byscript(self, script='', reason=''):
        """
        Execute JavaScript and return value.
        
        Args:
            script (str): JavaScript to execute
            reason (str): Reason for execution (for logging)
            
        Returns:
            Any: Value returned by JavaScript
        """
        if reason:
            print(f'Script execute for: {reason}')
        else:
            print(f'execute_script: {script}')
        value = self.driver.execute_script(f'return {script}')  
        return value
        
    def CloseDriver(self):
        """Close and quit the driver and cleanup instance files"""
        if isinstance(self.driver, WebDriver):
            try:
                self.driver.quit()
                print('Driver is closed!')
            except Exception as e:
                print(f"Error quitting driver: {e}")
        
        # Cleanup instance directories
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            if os.path.exists(self.profile_dir):
                shutil.rmtree(self.profile_dir, ignore_errors=True)
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
    def load_cookies(self, website: str, redirect_url: str='', refresh=True):
        """
        Load cookies from file.
        
        Args:
            website (str): Website identifier
            redirect_url (str): URL to redirect after loading cookies
            refresh (bool): Whether to refresh page after loading
        """
        try:
            path = os.path.join(self.cookies_path, f'{website}_cookietest.json')
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    cookies = json.load(f)
                for item in cookies:
                    self.driver.add_cookie(item)
            if redirect_url:
                self.driver.get(redirect_url)
            else:
                if refresh:
                    self.driver.refresh()
            self.random_sleep()                
        except Exception as e:
            print(f'The cookies could not be loaded: {e}')
            
    def create_or_check_path(self, folder_name, sub_folder_=None, main=False):
        """
        Create or verify a directory path.
        
        Args:
            folder_name (str): Folder name
            sub_folder_ (str): Optional subfolder name
            main (bool): Whether to use current directory as base
            
        Returns:
            str: Full path to directory
        """
        folder_name = folder_name if not os.path.isdir(folder_name) else os.path.basename(folder_name)
        base_path = os.path.join(os.getcwd(), 'downloads') if not main else os.getcwd()
        folder = os.path.join(base_path, folder_name)
        try:
            if sub_folder_:
                folder = os.path.join(folder, sub_folder_)
        except Exception as e: 
            print("Error:", e)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def get_cookies(self, website: str):
        """
        Save current cookies to file.
        
        Args:
            website (str): Website identifier
            
        Returns:
            list: List of cookie dictionaries
        """
        path = os.path.join(self.cookies_path, f'{website}_cookietest.json')
        cookies = self.driver.get_cookies()
        with open(path, 'w', newline='') as outputdata:
            if website == "Fivek_teen":
                cookies[0]['expiry'] += 172800
            json.dump(cookies, outputdata)
        return cookies
    
    def wait_for_file_download(self, files=[], timeout=60, download_dir="downloads"):
        """
        Wait for a file download to complete.
        
        Args:
            files (list): List of existing files to ignore
            timeout (int): Maximum wait time in seconds
            download_dir (str): Download directory path
            
        Returns:
            str or False: Downloaded filename or False if timeout
        """
        print('Waiting for download to start...')
        
        start_time = time.time()
        
        if not os.path.exists(download_dir):
            raise FileNotFoundError(f"Download directory '{download_dir}' does not exist.")

        crdownload_file = None

        # Wait for a .crdownload file to appear
        for i in range(timeout):
            time.sleep(1)
            
            for crd in os.listdir(download_dir):
                if crd.endswith('.crdownload'):
                    crdownload_file = crd
                    print(f"Download started: {crdownload_file}")
                    break

            if crdownload_file:
                break
        else:
            # Check for finished file
            for f in os.listdir(download_dir):
                if os.path.isfile(os.path.join(download_dir, f)):
                    if f.endswith(".mp4") and f not in files:
                        return f

        if not crdownload_file:
            print("No download started within the timeout period.")
            return None

        print("Download is in progress. Checking until download completes...")

        # Wait for download to complete
        while True:
            if not os.path.exists(os.path.join(download_dir, crdownload_file)):
                completed_file = crdownload_file.replace('.crdownload', '')
                print(f"Download complete: {completed_file}")
                return completed_file
            
            time.sleep(1)

            if time.time() - start_time > timeout:
                print("Download did not complete within the timeout period.")
                return False
    
    def sanitize_title(self, title: str):
        """
        Sanitize a title for use as filename.
        
        Args:
            title (str): Title to sanitize
            
        Returns:
            str: Sanitized title
        """
        formatted_title = ''.join(c.lower() if c.isalnum() else '_' for c in title)
        formatted_title = '_'.join(filter(None, formatted_title.split('_')))
        return formatted_title
    
    def download_video_from_request(self, url, filename, headers=None):
        """
        Download a video from URL with progress bar.
        
        Args:
            url (str): Video URL
            filename (str): Output filename
            headers (dict): Optional HTTP headers
        """
        if not url:
            return
        
        if headers:
            response = requests.get(url, headers=headers, stream=True)
        else: 
            response = requests.get(url, stream=True)
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filename, 'wb') as f, tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
                
    def copy_files_in_media_folder(self, src_file, folder="videos"):
        """
        Copy files to media folder.
        
        Args:
            src_file (str): Source file path
            folder (str): Target folder ('videos' or 'image')
            
        Returns:
            str or False: Relative path to copied file or False
        """
        new_src_file = ''
        current_src_file = ''
        if os.path.exists(src_file):
            if os.getcwd() in src_file:
                current_src_file = src_file.split(os.getcwd())[-1]
            
            if "downloads" in current_src_file:
                current_src_file = current_src_file.split('downloads')[-1]
            
            if current_src_file.startswith('/'):
                current_src_file = current_src_file[1:]
            
            if folder == "videos":
                new_src_file = os.path.join(os.getcwd(), "media", folder, current_src_file)
            else:
                new_src_file = os.path.join(os.getcwd(), "media", "image", current_src_file)
                
            parent_dir = os.path.dirname(new_src_file)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            shutil.move(src_file, new_src_file)
            return os.path.join("videos", current_src_file) if folder == "videos" else os.path.join("image", current_src_file)

        return False
