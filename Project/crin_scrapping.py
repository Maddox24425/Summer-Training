import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import json
import re
from typing import Optional, List, Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrinacleAdvancedScraper:
    """
    Advanced scraper for Crinacle's IEM rankings with multiple fallback methods.
    """
    
    def __init__(self, url: str = "https://crinacle.com/rankings/iems/"):
        self.url = url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def try_selenium_scraping(self) -> Optional[List[List[str]]]:
        """
        Try scraping with Selenium WebDriver for JavaScript-rendered content.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print("🤖 Trying Selenium WebDriver...")
            
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            # Initialize driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                print("🌐 Loading page with JavaScript...")
                driver.get(self.url)
                
                # Wait for table to load
                wait = WebDriverWait(driver, 20)
                
                # Try different selectors for the table
                table_selectors = [
                    'table',
                    'tbody',
                    '.tablepress',
                    '[id*="tablepress"]',
                    '.dataTable',
                    '[class*="table"]',
                    'tr'  # Just look for any table rows
                ]
                
                table_element = None
                for selector in table_selectors:
                    try:
                        table_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        print(f"✅ Found table using selector: {selector}")
                        break
                    except:
                        continue
                
                if not table_element:
                    print("❌ No table found with Selenium")
                    return None
                
                # Get page source after JavaScript execution
                html_content = driver.page_source
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all table rows
                rows = soup.find_all('tr')
                if not rows:
                    print("❌ No table rows found")
                    return None
                
                extracted_data = []
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_data = []
                        for cell in cells:
                            text = cell.get_text(separator=' ', strip=True)
                            text = ' '.join(text.split())  # Clean whitespace
                            row_data.append(text)
                        if row_data and any(cell.strip() for cell in row_data):
                            extracted_data.append(row_data)
                
                print(f"✅ Selenium extracted {len(extracted_data)} rows")
                return extracted_data
                
            finally:
                driver.quit()
                
        except ImportError:
            print("⚠️ Selenium not installed. Install with: pip install selenium")
            print("⚠️ Also need ChromeDriver: https://chromedriver.chromium.org/")
            return None
        except Exception as e:
            print(f"❌ Selenium scraping failed: {e}")
            return None

    def try_direct_parsing(self) -> Optional[List[List[str]]]:
        """
        Try parsing the page content directly looking for data patterns.
        """
        try:
            print("🔍 Trying direct content parsing...")
            
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            
            # Look for JSON data or structured content
            content = response.text
            
            # Method 1: Look for inline JSON data
            json_patterns = [
                r'var\s+tableData\s*=\s*(\[.*?\]);',
                r'data:\s*(\[.*?\])',
                r'tablepress_\w+\s*=\s*(\{.*?\});'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    try:
                        data = json.loads(matches[0])
                        print(f"✅ Found JSON data with {len(data)} items")
                        return self.convert_json_to_rows(data)
                    except:
                        continue
            
            # Method 2: Look for structured text content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and look for table-like patterns
            text = soup.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look for lines that contain typical IEM data patterns
            data_lines = []
            for line in lines:
                # Look for lines with grade patterns (S-, A+, etc.) and prices
                if re.search(r'[SA][+-]?\s*\|.*?\$?\d+', line) or \
                   re.search(r'[A-F][+-]?\s*\|.*?\d{2,4}', line):
                    data_lines.append(line)
            
            if data_lines:
                print(f"✅ Found {len(data_lines)} potential data lines")
                extracted_rows = []
                for line in data_lines[:10]:  # Limit for testing
                    # Split by common delimiters
                    parts = re.split(r'\s*\|\s*', line)
                    if len(parts) >= 4:
                        extracted_rows.append(parts)
                
                if extracted_rows:
                    return extracted_rows
            
            return None
            
        except Exception as e:
            print(f"❌ Direct parsing failed: {e}")
            return None

    def try_alternative_endpoints(self) -> Optional[List[List[str]]]:
        """
        Try alternative endpoints that might serve the data.
        """
        alternative_urls = [
            "https://crinacle.com/wp-admin/admin-ajax.php",
            "https://crinacle.com/rankings/iems/data/",
            "https://crinacle.com/api/rankings/iems/",
        ]
        
        for alt_url in alternative_urls:
            try:
                print(f"🔄 Trying alternative endpoint: {alt_url}")
                response = self.session.get(alt_url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list) and data:
                            print(f"✅ Found JSON data at {alt_url}")
                            return self.convert_json_to_rows(data)
                    except:
                        pass
            except:
                continue
        
        return None

    def convert_json_to_rows(self, data) -> List[List[str]]:
        """Convert JSON data to rows format."""
        if not data:
            return []
        
        rows = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    row = list(item.values())
                    rows.append([str(val) for val in row])
                elif isinstance(item, list):
                    rows.append([str(val) for val in item])
        
        return rows

    def create_sample_data(self) -> List[List[str]]:
        """
        Create sample data based on what we know about the structure.
        """
        print("📋 Creating sample data from known structure...")
        
        sample_data = [
            ['Rank', 'Value', 'Name', 'Price', 'Signature', 'Notes', 'Tone Grade', 'Tech Grade', 'Drivers'],
            ['S-', '★', 'Elysian Annihilator (2021)', '3700', 'U-shaped', '', 'S-', 'S', '2EST 4BA 1DD'],
            ['S-', '★★', 'ThieAudio Monarch Mk2', '1000', 'Neutral with bass boost', '', 'S+', 'A+', '2EST 6BA 1DD'],
            ['A+', '★★★', 'Moondrop Variations', '520', 'U-shaped', 'Sub-bass-focused signature with Moondrop\'s clean tuning', 'S', 'A', '2EST 2BA 1DD'],
            ['A+', '★', 'Hidition NT6', '1050', 'Neutral', 'If Etymotic made a multi-BA IEM, this would be the closest', 'S-', 'A+', '6BA'],
            ['A+', '★★', 'Sennheiser IE600', '700', 'U-shaped', 'Well-tuned mids, powerful yet controlled sub-bass', 'A+', 'A+', 'DD'],
        ]
        
        return sample_data

    def save_to_csv(self, data: List[List[str]], filename: str = 'crinacle_iem_rankings.csv') -> bool:
        """Save data to CSV file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
            filepath = os.path.join(script_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
            
            print(f"✅ Successfully saved {len(data)} rows to: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            return False

    def scrape(self, output_filename: str = 'crinacle_iem_rankings.csv') -> bool:
        """
        Main scraping method that tries multiple approaches.
        """
        print("🎧 Advanced Crinacle IEM Rankings Scraper")
        print(f"🌐 URL: {self.url}")
        print("=" * 60)
        
        # Method 1: Try Selenium (handles JavaScript)
        data = self.try_selenium_scraping()
        if data:
            return self.save_to_csv(data, output_filename)
        
        print("\n" + "-" * 40)
        
        # Method 2: Try direct parsing
        data = self.try_direct_parsing()
        if data:
            return self.save_to_csv(data, output_filename)
        
        print("\n" + "-" * 40)
        
        # Method 3: Try alternative endpoints
        data = self.try_alternative_endpoints()
        if data:
            return self.save_to_csv(data, output_filename)
        
        print("\n" + "-" * 40)
        
        # Method 4: Create sample data for testing
        print("⚠️ All scraping methods failed. Creating sample data for testing...")
        data = self.create_sample_data()
        success = self.save_to_csv(data, f"sample_{output_filename}")
        
        if success:
            print("\n🎯 Next steps to get the full data:")
            print("1. Install Selenium: pip install selenium")
            print("2. Download ChromeDriver: https://chromedriver.chromium.org/")
            print("3. Or manually copy table data from browser and save as CSV")
            print("4. The website might be using advanced anti-scraping measures")
            
        return success


def main():
    """Main function."""
    current_dir = os.getcwd()
    print(f"📁 Working directory: {current_dir}\n")
    
    scraper = CrinacleAdvancedScraper()
    scraper.scrape()


if __name__ == "__main__":
    main()