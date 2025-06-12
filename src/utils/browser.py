"""
Browser utilities for Selenium WebDriver setup and management.
"""

from selenium import webdriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.safari.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import time

def setup_driver():
    """
    Set up and configure the Safari WebDriver.
    
    Returns:
        WebDriver: Configured Safari WebDriver instance
    """
    try:
        safari_options = Options()
        safari_options.set_capability('platformName', 'mac')
        safari_options.set_capability('browserName', 'safari')
        service = Service()
        driver = webdriver.Safari(service=service, options=safari_options)
        return driver
    except Exception as e:
        print(f"Error setting up Safari driver: {str(e)}")
        print("\nPlease make sure you have:")
        print("1. Safari installed")
        print("2. Remote Automation enabled in Safari > Develop menu")
        print("3. Required Python packages installed (pip install -r requirements.txt)")
        sys.exit(1) 