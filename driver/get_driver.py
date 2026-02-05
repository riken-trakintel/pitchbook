import json, random, os, time, requests
from .utils import get_chrome_version
from tqdm import tqdm
import shutil

# selenium imports
from selenium.common.exceptions import NoSuchElementException, TimeoutException,ElementNotInteractableException,NoSuchElementException,WebDriverException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver


with open("config.json", "r") as file:
    config = json.load(file)

headless = config.get("headless")

class StartDriver():
    def __init__(self, driver_type='normal'):
        self.driver_type = driver_type
        self.download_path = os.path.join(os.getcwd(), 'downloads')
        self.cookies_path = os.path.join(os.getcwd(), 'cookies')
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.cookies_path, exist_ok=True)
        self.driver = None
        self.options = None
    
    def driver_arguments(self):
        self.options.add_argument('--lang=en')  
        self.options.add_argument("--enable-webgl-draft-extensions")
        self.options.add_argument('--mute-audio')
        self.options.add_argument("--ignore-gpu-blocklist")
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--disable-blink-features=AutomationControlled") 
 
        # Exclude the collection of enable-automation switches 
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        
        # Turn-off userAutomationExtension 
        self.options.add_experimental_option("useAutomationExtension", False) 
        
        prefs = {
            "credentials_enable_service": True,
            'profile.default_content_setting_values.automatic_downloads': 1,
            "download.default_directory" : f"{self.download_path}",
            'download.prompt_for_download': False, 
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True ,
            "profile.password_manager_enabled": True
        }
        
        self.options.add_experimental_option("prefs", prefs)
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--start-maximized')    
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_argument("--enable-javascript")
        self.options.add_argument("--enable-popup-blocking")
        self.options.add_argument("--incognito")
        
    def get_driver(self):
        if not headless:
            self.get_local_driver()
            return self.driver
        else:
            for _ in range(30):
                user_agents = [
                    # Add your list of user agents here
                    f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(108,126)}.0.0.0 Safari/537.36',
                    f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(108,126)}.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                ]

                if self.driver_type == 'normal':
                    from selenium import webdriver
                    for _ in range(30):
                        user_agent = random.choice(user_agents)
                        self.options = webdriver.ChromeOptions()
                        self.options.add_argument(f'user-agent={user_agent}')
                        self.options.add_argument(f'--headless=new')
                        self.driver_arguments()
                        self.options.add_argument(f"download.default_directory={os.path.join(os.getcwd(), 'downloads')}")

                        try:
                            self.driver = webdriver.Chrome(options=self.options)
                            params = {
                                "behavior": "allow",
                                "downloadPath": os.path.join(os.getcwd(), 'downloads')
                            }
                            self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                            break
                        except Exception as e:
                            print(e)
                else:
                    import undetected_chromedriver as uc
                    user_agent = random.choice(user_agents)
                    self.options = uc.ChromeOptions()
                    self.options.add_argument(f'user-agent={user_agent}')
                    self.options.add_argument(f"download.default_directory={os.path.join(os.getcwd(), 'downloads')}")
                    try:
                        self.driver = uc.Chrome( options=self.options, use_subprocess=False, headless=True, version_main=get_chrome_version())
                        params = {
                            "behavior": "allow",
                            "downloadPath": os.path.join(os.getcwd(), 'downloads')
                        }
                        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                        break
                    except Exception as e:


                            print(e)
        
            return self.driver
        
        
    def get_local_driver(self):
        """### Start webdriver and return state of it.
            #### if not self.driver_type then it's by default go with undetected chromedriver,
            #### else use normal selenium driver with extra argument."""
        # import seleniumwire.undetected_chromedriver as uc
        user_agents = [
            # Add your list of user agents here
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        ]
        # self.driver_type = 'normal'
        if self.driver_type == 'normal':
            from selenium import webdriver
            for _ in range(30):
                user_agent = random.choice(user_agents)
                self.options = webdriver.ChromeOptions()
                self.options.add_argument(f'user-agent={user_agent}')
                self.driver_arguments()
                self.options.add_argument("--incognito")

                self.options.add_argument(f"download.default_directory={os.path.join(os.getcwd(),'downloads')}")
                try:
                    self.driver = webdriver.Chrome(options=self.options)
                    params = {
                        "behavior": "allow",
                        "downloadPath": os.path.join(os.getcwd(), 'downloads')
                    }
                    self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                    break
                except Exception as e:
                    
                    print(e)
        else:
            import undetected_chromedriver as uc
            for _ in range(30):
                user_agent = random.choice(user_agents)
                self.options = uc.ChromeOptions()
                self.options.add_argument(f'user-agent={user_agent}')
                self.options.add_argument("--incognito")
                self.options.add_argument(f"download.default_directory={os.path.join(os.getcwd(),'downloads')}")

                try:
                    self.driver = uc.Chrome(use_subprocess=False)
                    params = {
                        "behavior": "allow",
                        "downloadPath": os.path.join(os.getcwd(),'downloads')
                    }
                    self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
                    break
                except Exception as e:
                    print(e)
        
        return self.driver
    
    
    def find_element(self, element, locator, locator_type=By.XPATH,
            page=None, timeout=10,
            condition_func=EC.presence_of_element_located,
            condition_other_args=tuple()):
        """Find an element, then return it or None.
        If timeout is less than or requal zero, then just find.
        If it is more than zero, then wait for the element present.
        """
        try:
            if timeout > 0:
                wait_obj = WebDriverWait(self.driver, timeout)
                ele = wait_obj.until(EC.presence_of_element_located((locator_type, locator)))
                # ele = wait_obj.until( condition_func((locator_type, locator),*condition_other_args))
            else:
                print(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver.find_element(by=locator_type,
                        value=locator)
            if page:
                print(
                    f'Found the element "{element}" in the page "{page}"')
            else:
                print(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                print(f'Cannot find the element "{element}"'
                        f' in the page "{page}"')
            else:
                print(f'Cannot find the element: {element}')
                
    def click_element(self, element, locator, locator_type=By.XPATH,
            timeout=10):
        """Find an element, then click and return it, or return None"""
        ele = self.find_element(element, locator, locator_type, timeout=timeout)
        
        if ele:
            self.driver.execute_script('arguments[0].scrollIntoViewIfNeeded();',ele)
            self.ensure_click(ele)
            print(f'Clicked the element: {element}')
            return ele

    def input_text(self, text, element, locator, locator_type=By.XPATH,
            timeout=10, hide_keyboard=True):
        """Find an element, then input text and return it, or return None"""
        
        ele = self.find_element(element, locator, locator_type=locator_type,
                timeout=timeout)
        
        if ele:
            for i in range(3):
                try: 
                    ele.send_keys(text)
                    print(f'Inputed "{text}" for the element: {element}')
                    return ele    
                except ElementNotInteractableException :...
    
    def ScrollDown(self,px):
        self.driver.execute_script(f"window.scrollTo(0, {px})")
    
    def ensure_click(self, element: WebElement, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(element))
            element.click()
        except WebDriverException:
            self.driver.execute_script("arguments[0].click();", element)
        
    def new_tab(self):
        self.driver.find_element(By.XPATH,'/html/body').send_keys(Keys.CONTROL+'t')

    def random_sleep(self,a=3,b=7,reson = ""):
        random_time = random.randint(a,b)
        print('time sleep randomly :',random_time) if not reson else print('time sleep randomly :',random_time,f' for {reson}')
        time.sleep(random_time)

    def getvalue_byscript(self,script = '',reason=''):
        """made for return value from ele or return ele"""
        if reason :print(f'Script execute for : {reason}')
        else:
            print(f'execute_script : {script}')
        value = self.driver.execute_script(f'return {script}')  
        return value
        
    def CloseDriver(self):
        if isinstance(self.driver, WebDriver):
            self.driver.quit()
        print('Driver is closed !')
        
        
    def load_cookies(self,website :str, redirect_url:str='', refreash=True):
        try:
            path = os.path.join(self.cookies_path,f'{website}_cookietest.json')
            if os.path.isfile(path):
                with open(path,'rb') as f:cookies = json.load(f)
                for item in cookies: self.driver.add_cookie(item)
            if redirect_url:self.driver.get(redirect_url)
            else:
                if refreash :
                    self.driver.refresh()
            self.random_sleep()                
        except : 
            print('The coockies could not be loaded')
            
            
    def create_or_check_path(self,folder_name, sub_folder_=None,main=False):
        folder_name = folder_name if not os.path.isdir(folder_name) else os.path.basename(folder_name)
        base_path = os.path.join(os.getcwd(), 'downloads') if not main else os.getcwd()
        folder = os.path.join(base_path, folder_name)
        try :
            if sub_folder_: folder = os.path.join(folder, sub_folder_)
        except Exception as e: 
            print("Error :",e)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    
    def get_cookies(self,website :str):
        path = os.path.join(self.cookies_path,f'{website}_cookietest.json')
        cookies = self.driver.get_cookies()
        with open(path, 'w', newline='') as outputdata:
            if website == "Fivek_teen" :
                cookies[0]['expiry'] +=172800

            json.dump(cookies, outputdata)
        return cookies
    
    def wait_for_file_download(self,files = [], timeout=60,download_dir="downloads"):
        """
        Waits for a file download to complete in the specified directory (non-recursively),
        accounting for downloads that start late within the timeout period.
        
        Parameters:
            timeout (int): Maximum time to wait for the download to complete (in seconds).
            download_dir (str): Directory to monitor for the download.
        
        Returns:
            str: The name of the completed downloaded file (without `.crdownload` extension).
            None: If no download completes within the timeout.
        """
        print('Waiting for download to start...')
        
        start_time = time.time()
        
        # Ensure the directory exists
        if not os.path.exists(download_dir):
            raise FileNotFoundError(f"Download directory '{download_dir}' does not exist.")

        crdownload_file = None

        # Wait for a .crdownload file to appear in the download directory
        for i in range(timeout):
            time.sleep(1)
            
            # List files in the top level of the directory
            for crd in os.listdir(download_dir):
                if crd.endswith('.crdownload'):
                    crdownload_file = crd
                    print(f"Download started: {crdownload_file}")
                    break

            if crdownload_file:
                break
        else:
            # If no download starts within the timeout, check for a finished file
            for f in os.listdir(download_dir):
                if os.path.isfile(os.path.join(download_dir, f)):
                    if f.endswith(".mp4") and f not in files:
                        return f

        if not crdownload_file:
            print("No download started within the timeout period.")
            return None

        print("Download is in progress. Checking until download completes...")

        # Wait for the .crdownload file to disappear, indicating the download is complete
        completed_file = None
        while True:
            if crdownload_file :
                print("Download is in progress. Checking until download completes... While loop")
                
                while True :
                    if not os.path.exists(os.path.join(download_dir, crdownload_file)):
                        completed_file = crdownload_file.replace('.crdownload', '')
                        print(f"Download complete: {completed_file}")
                        return completed_file
            
            if not os.path.exists(os.path.join(download_dir, crdownload_file)):
                # Download is complete
                completed_file = crdownload_file.replace('.crdownload', '')
                print(f"Download complete: {completed_file}")
                return completed_file
            
            # If the file is still in progress, wait for a short period before checking again
            time.sleep(1)

            # Break if timeout exceeds (check for maximum timeout)
            if time.time() - start_time > timeout:
                print("Download did not complete within the timeout period.")
                return False
    
    def sanitize_title(self,title : str): 
        formatted_title = ''.join(c.lower() if c.isalnum() else '_' for c in title)
        formatted_title = '_'.join(filter(None, formatted_title.split('_')))
        return formatted_title
    
    
    def download_video_from_request(self, url, filename, headers = None):
        if not url : return
        
        if headers:
            response = requests.get(url, headers=headers ,stream=True)
        else: 
            response = requests.get(url, stream=True)
        
        # Total size in bytes, may be None if content-length header is not set
        total_size = int(response.headers.get('content-length', 0))
        
        # Open a local file for writing the binary stream
        with open(filename, 'wb') as f, tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
                
    
    def copy_files_in_media_folder(self,src_file,folder="videos"):
        new_src_file = ''
        current_src_file = ''
        if os.path.exists(src_file):
            if os.getcwd() in src_file:
                current_src_file = src_file.split(os.getcwd())[-1]
            
            if "downloads" in current_src_file:
                current_src_file = current_src_file.split('downloads')[-1]
            
            if current_src_file.startswith('/'):
                current_src_file = current_src_file[1:]
            
            if folder == "videos" :
                new_src_file = os.path.join(os.getcwd(), "media", folder, current_src_file)
            else :
                new_src_file = os.path.join(os.getcwd(), "media", "image", current_src_file)
                
            parent_dir = os.path.dirname(new_src_file)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            shutil.move(src_file, new_src_file)
            return os.path.join("videos", current_src_file) if folder=="videos" else os.path.join("image", current_src_file)

        return False