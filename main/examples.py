"""
Example usage of the at_test scraping framework.
Demonstrates different ways to use the classes.
"""

from main import PitchBookScraper
from details import ScrapeCompanyDetails, scrape_company
from driver import StartDriver
from logger import CustomLogger


def example_1_full_scraper():
    """Example 1: Run the full scraper with custom settings"""
    print("\n" + "="*60)
    print("Example 1: Full Scraper")
    print("="*60)
    
    scraper = PitchBookScraper(
        batch_size=2,
        max_runs=1
    )
    
    scraper.run()


def example_2_single_company():
    """Example 2: Scrape a single company"""
    print("\n" + "="*60)
    print("Example 2: Single Company Scrape")
    print("="*60)
    
    logger = CustomLogger(log_folder="logs")
    url = "https://pitchbook.com/profiles/company/233787-07"
    
    # Method 1: Using the convenience function
    data = scrape_company(url, logger)
    
    if data:
        print(f"✓ Successfully scraped: {data.get('company_name', 'Unknown')}")
        print(f"  Overview items: {len(data.get('overview', {}))}")
        print(f"  Investors: {len(data.get('investors', []))}")
    else:
        print("✗ Failed to scrape company")


def example_3_custom_scraper():
    """Example 3: Use ScrapeCompanyDetails class directly"""
    print("\n" + "="*60)
    print("Example 3: Custom Scraper Class")
    print("="*60)
    
    logger = CustomLogger(log_folder="logs")
    url = "https://pitchbook.com/profiles/company/233787-07"
    
    # Create scraper instance
    scraper = ScrapeCompanyDetails(url, logger, driver_type='undetected')
    
    # Scrape the data
    data = scraper.scrape()
    
    if data:
        print(f"✓ Company: {data.get('company_name', 'Unknown')}")
        print(f"  URL: {data.get('source_url', 'N/A')}")
        print(f"  Scraped at: {data.get('scraped_at', 'N/A')}")


def example_4_driver_only():
    """Example 4: Use StartDriver class directly"""
    print("\n" + "="*60)
    print("Example 4: Direct Driver Usage")
    print("="*60)
    
    # Create driver manager
    driver_manager = StartDriver(driver_type='undetected')
    driver = driver_manager.get_driver()
    
    if driver:
        print("✓ Driver started successfully")
        
        # Navigate to a page
        print("DEBUG: Navigating to https://pitchbook.com ...")
        driver.get("https://pitchbook.com")
        print(f"  Page title: {driver.title}")
        print("DEBUG: Navigation successful")
        
        # Use driver manager utilities
        driver_manager.random_sleep(2, 4, reason="demonstration")
        
        # Clean up
        driver_manager.CloseDriver()
        print("✓ Driver closed")
    else:
        print("✗ Failed to start driver")


def example_5_search_only():
    """Example 5: Search for companies without scraping details"""
    print("\n" + "="*60)
    print("Example 5: Search Only")
    print("="*60)
    
    scraper = PitchBookScraper()
    
    # Search for a company
    search_term = "QNu Labs"
    urls = scraper.get_companies_list(search_term)
    
    if urls:
        print(f"✓ Found {len(urls)} results for '{search_term}':")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
    else:
        print(f"✗ No results found for '{search_term}'")


def example_6_batch_processing():
    """Example 6: Process a single batch"""
    print("\n" + "="*60)
    print("Example 6: Single Batch Processing")
    print("="*60)
    
    scraper = PitchBookScraper(batch_size=3)
    
    # Process just one batch
    scraper.process_batch()
    print("✓ Batch processing complete")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AT_TEST Framework Examples")
    print("="*60)
    print("\nChoose an example to run:")
    print("1. Full scraper (batch processing)")
    print("2. Single company scrape")
    print("3. Custom scraper class")
    print("4. Direct driver usage")
    print("5. Search only (no scraping)")
    print("6. Single batch processing")
    print("\nUncomment the example you want to run in the code.")
    print("="*60)
    
    # Uncomment the example you want to run:
    
    # For testing, run example 4 (direct driver)
    example_4_driver_only()
