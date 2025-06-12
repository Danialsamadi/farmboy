"""
Farm Boy service for login and schedule scraping.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def login(driver, email, password):
    """
    Log in to the Farm Boy employee portal.
    
    Args:
        driver: Selenium WebDriver instance
        email (str): Farm Boy login email
        password (str): Farm Boy login password
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        print("Navigating to login page...")
        driver.get('https://myfarmboy.ca/login')
        wait = WebDriverWait(driver, 10)

        print("Looking for email field...")
        email_field = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '#__layout > div > div > form > div > div:nth-child(1) > input'
        )))

        print("Looking for password field...")
        password_field = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '#__layout > div > div > form > div > div:nth-child(2) > input'
        )))

        email_field.clear()
        email_field.send_keys(email)
        password_field.clear()
        time.sleep(1)
        password_field.send_keys(password)
        time.sleep(1)

        print("Looking for Sign In button...")
        sign_in_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button.w-full.px-6.py-2.mt-4.bg-green-10.rounded-lg'
        )))

        print("Clicking Sign In button...")
        driver.execute_script("arguments[0].click();", sign_in_button)
        print("Waiting for login to complete...")
        time.sleep(5)

        if '/login' in driver.current_url:
            print("Login failed - still on login page")
            try:
                error_message = driver.find_element(By.CLASS_NAME, 'error-message')
                print(f"Error message: {error_message.text}")
            except:
                print("No error message found")
            return False

        print("Successfully logged in!")
        return True
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def scrape_schedule(driver):
    """
    Scrape the work schedule from the Farm Boy employee portal.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        tuple: (schedule_text, shift_data) or (None, None) if scraping fails
    """
    try:
        print("Navigating to schedule page...")
        driver.get('https://myfarmboy.ca/schedule')
        wait = WebDriverWait(driver, 10)

        print("Waiting for schedule content to load...")
        wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'div.rounded-md.p-3.my-3.bg-gray-50'
        )))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        schedule_cards = soup.find_all('div', class_='rounded-md p-3 my-3 bg-gray-50')
        print(f"Found {len(schedule_cards)} schedule cards")

        schedule_text = []
        shift_data = []

        for card in schedule_cards:
            try:
                day_element = card.find_previous('h3', class_='text-lg')
                day = day_element.get_text(strip=True) if day_element else "Day not found"

                time_div = card.find('div', class_='font-bold')
                time_text = time_div.get_text(strip=True) if time_div else "Time not found"

                status_div = card.find('div', class_='rounded-sm')
                status = status_div.get_text(strip=True) if status_div else "Active"

                role_div = card.find('div', string=lambda text: text and 'Role:' in text)
                role = role_div.find('span', class_='capitalize').get_text(strip=True) if role_div else "Role not found"

                department_div = card.find('div', string=lambda text: text and 'Department:' in text)
                department = department_div.find('span', class_='capitalize').get_text(strip=True) if department_div else "Department not found"

                duration_p = card.find('p', class_='text-xl font-bold')
                duration = duration_p.get_text(strip=True) if duration_p else "Duration not found"

                shift_info = (
                    f"Date: {day}\n"
                    f"Time: {time_text}\n"
                    f"Status: {status}\n"
                    f"Role: {role}\n"
                    f"Department: {department}\n"
                    f"Duration: {duration}\n"
                    f"{'-'*30}"
                )

                shift_data.append({
                    'date': day,
                    'time': time_text,
                    'status': status,
                    'role': role,
                    'department': department,
                    'duration': duration
                })

                schedule_text.append(shift_info)
                print(f"Processed shift for {day} - Status: {status}")
            except Exception as e:
                print(f"Error parsing card: {str(e)}")
                continue

        if not schedule_text:
            print("No schedule data found")
            return None, None

        return '\n\n'.join(schedule_text), shift_data
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return None, None 