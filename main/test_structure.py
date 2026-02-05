"""
Test script to validate the at_test code structure without running browser.
This tests imports, class initialization, and method availability.
"""

import sys
import os

print("="*60)
print("AT_TEST Structure Validation")
print("="*60)

# Test 1: Import all modules
print("\n[Test 1] Testing imports...")
try:
    from main import PitchBookScraper
    from details import ScrapeCompanyDetails, scrape_company, save_to_db, normalize_key
    from driver import StartDriver
    from logger import CustomLogger
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check class initialization
print("\n[Test 2] Testing class initialization...")
try:
    logger = CustomLogger(log_folder="test_logs")
    print("✓ CustomLogger initialized")
    
    # Note: Not initializing driver as it requires Chrome
    print("✓ StartDriver class available (not initialized to avoid Chrome dependency)")
    
    # Initialize scraper without running
    scraper = PitchBookScraper(batch_size=1, max_runs=1)
    print("✓ PitchBookScraper initialized")
    
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Check method availability
print("\n[Test 3] Testing method availability...")
try:
    # Check PitchBookScraper methods
    assert hasattr(scraper, 'start_driver'), "Missing start_driver method"
    assert hasattr(scraper, 'close_driver'), "Missing close_driver method"
    assert hasattr(scraper, 'read_company_names'), "Missing read_company_names method"
    assert hasattr(scraper, 'get_companies_list'), "Missing get_companies_list method"
    assert hasattr(scraper, 'scrape_company_details'), "Missing scrape_company_details method"
    assert hasattr(scraper, 'save_company_data'), "Missing save_company_data method"
    assert hasattr(scraper, 'process_batch'), "Missing process_batch method"
    assert hasattr(scraper, 'run'), "Missing run method"
    print("✓ PitchBookScraper has all required methods")
    
    # Check StartDriver methods
    driver_class = StartDriver
    assert hasattr(driver_class, 'get_driver'), "Missing get_driver method"
    assert hasattr(driver_class, 'find_element'), "Missing find_element method"
    assert hasattr(driver_class, 'click_element'), "Missing click_element method"
    assert hasattr(driver_class, 'CloseDriver'), "Missing CloseDriver method"
    print("✓ StartDriver has all required methods")
    
    # Check Logger methods
    assert hasattr(logger, 'info'), "Missing info method"
    assert hasattr(logger, 'error'), "Missing error method"
    assert hasattr(logger, 'warning'), "Missing warning method"
    print("✓ CustomLogger has all required methods")
    
except AssertionError as e:
    print(f"✗ Method check failed: {e}")
    sys.exit(1)

# Test 4: Test utility functions
print("\n[Test 4] Testing utility functions...")
try:
    # Test normalize_key
    assert normalize_key("Test Company Name") == "test_company_name"
    assert normalize_key("ABC-123") == "abc_123"
    print("✓ normalize_key works correctly")
    
except Exception as e:
    print(f"✗ Utility function test failed: {e}")
    sys.exit(1)

# Test 5: Test configuration
print("\n[Test 5] Testing configuration...")
try:
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    assert 'headless' in config, "Missing headless config"
    print(f"✓ Configuration loaded: headless={config['headless']}")
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    sys.exit(1)

# Test 6: Test logger functionality
print("\n[Test 6] Testing logger functionality...")
try:
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    
    # Check if log files were created
    assert os.path.exists("test_logs/info.log"), "Info log not created"
    assert os.path.exists("test_logs/error.log"), "Error log not created"
    assert os.path.exists("test_logs/warning.log"), "Warning log not created"
    assert os.path.exists("test_logs/general.log"), "General log not created"
    print("✓ Logger creates all log files correctly")
    
except Exception as e:
    print(f"✗ Logger test failed: {e}")
    sys.exit(1)

# Test 7: Test class attributes
print("\n[Test 7] Testing class attributes...")
try:
    assert scraper.batch_size == 1, "Batch size not set correctly"
    assert scraper.max_runs == 1, "Max runs not set correctly"
    assert scraper.logger is not None, "Logger not initialized"
    print("✓ PitchBookScraper attributes set correctly")
    
except Exception as e:
    print(f"✗ Attribute test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*60)
print("VALIDATION SUMMARY")
print("="*60)
print("✓ All 7 tests passed!")
print("\nCode structure is valid and ready to use.")
print("\nNote: Actual web scraping requires:")
print("  1. Chrome browser installed")
print("  2. MongoDB connection (optional)")
print("  3. Valid proxy configuration (optional)")
print("\nTo run actual scraping, use:")
print("  python3 main.py")
print("="*60)

# Cleanup test logs
import shutil
if os.path.exists("test_logs"):
    shutil.rmtree("test_logs")
    print("\n✓ Test logs cleaned up")
