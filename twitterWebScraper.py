import time
import pickle
import random
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

load_dotenv();

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36"
]


def setupDriver():
    # Set up Brave options
    options = Options()
    options.binary_location = "/usr/bin/brave-browser"  # Update with your Brave installation path
    # Choose a random User-Agent from the list
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Helps evade bot detection
    # options.add_argument("--incognito")  # Avoids stored cache issues


    # Create a WebDriver instance using the Brave browser (ensure ChromeDriver is in PATH)
    driver = webdriver.Chrome(options=options)
    return driver

# Function to check if the account menu exists, indicating a successful login
def checkAccountMenu(driver):
    try:
        driver.find_element(By.XPATH, "//div[@aria-label='Account menu']")
        return True
    except NoSuchElementException:
        return False


# Function to save cookies to a file
def saveCookies(driver):
    with open("twitter_cookies.pkl", "wb") as cookies_file:
        pickle.dump(driver.get_cookies(), cookies_file)
    print("Cookies saved.")


# Function to perform login (if needed) and handle cookies
def login():
    driver = setupDriver()
    driver.get("https://x.com/i/flow/login")

    # Try to load cookies from file
    try:
        with open("twitter_cookies.pkl", "rb") as cookies_file:
            cookies = pickle.load(cookies_file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
        driver.refresh()  # Refresh to apply cookies and be logged in
        time.sleep(5)  # Wait for the page to load after refreshing

        # Check if we're logged in by looking for a specific element (like the profile button)
        if checkAccountMenu(driver):
            print("Logged in using cookies.")
            return driver  # Return the driver with cookies applied
        else:
            print("Cookies did not work. Logging in manually...")
            raise Exception("Cookies invalid or expired, logging in manually.")  # Force manual login

    except Exception as e:
        print(f"Error: {e}")
        print("Logging in manually...")
        driver.get("https://x.com/i/flow/login")
        time.sleep(5)  # Wait for login page to load

        # Manually log in (provide your credentials here)
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys(os.getenv("twitterEmail"))
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        time.sleep(6)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(os.getenv("twitterPassword"))
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        time.sleep(7)

        # After logging in, save the cookies
        saveCookies(driver)
        print("Successfully Logged in")
        return driver  # Return the logged-in driver


login()