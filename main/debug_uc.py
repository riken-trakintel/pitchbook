import undetected_chromedriver as uc
import sys

print("Starting uc.Chrome()...")
try:
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    prefs = {
        "credentials_enable_service": True,
        'profile.default_content_setting_values.automatic_downloads': 1,
        "profile.password_manager_enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(options=options, headless=True, version_main=143, use_subprocess=True)
    print("✓ Success! Session ID:", driver.session_id)
    driver.get("https://www.google.com")
    print("✓ Page title:", driver.title)
    driver.quit()
    print("✓ Closed.")
except Exception as e:
    print("✗ Failed:", e)
    import traceback
    traceback.print_exc()
