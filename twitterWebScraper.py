# %%
import goEmotions
import re
from emoji import demojize
import time
import pickle
import random
import os
from datetime import datetime, timedelta, timezone
import yfinance as yf
import requests
import pytz
from dotenv import load_dotenv
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv();

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/15.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36"
]

# %%
def setupDriver():
    # Set up Brave options
    options = Options()
    options.binary_location = os.getenv("bravePath")  # Update with your Brave installation path

    # Choose a random User-Agent from the list
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Helps evade bot detection

    # Define the user data directory where cookies will be stored
    user_data_dir = os.path.join(os.getcwd(), "cookies")  # Create a 'cookies' directory in the current working directory
    options.add_argument(f"user-data-dir={user_data_dir}")  # Use this directory for storing cookies

    # Create a WebDriver instance using the Brave browser
    driver = webdriver.Chrome(options=options)
    return driver

# %%
# Function to check if the account menu exists, indicating a successful login
def checkAccountLoggedIn(driver):
    if driver.current_url == "https://x.com/home":
        print("Check Account Logged in = true")
        return True
    print("Check Account Logged in = false")
    return False

# %%
# Function to perform login (if needed) and handle cookies
def login():
    driver = setupDriver()

    # Try to load cookies from previous session if they exist
    try:
        driver.get("https://x.com")  # Navigate to the homepage or login page to check if we have cookies
        time.sleep(10)  # Wait for the page to load
        
        # Check if the account menu is available, meaning we're already logged in
        if checkAccountLoggedIn(driver):
            print("Logged in using cookies.")
            return driver  # Return the driver with cookies applied
        else:
            print("Cookies did not work. Logging in manually...")
            raise Exception("Cookies invalid or expired, logging in manually.")  # Force manual login

    except Exception as e:
        print(f"Error: {e}")
        print("Logging in manually...")
        driver.get("https://x.com/i/flow/login")
        time.sleep(10)  # Wait for login page to load

        # Manually log in (provide your credentials here)
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys(os.getenv("twitterEmail"))
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        time.sleep(6)

        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(os.getenv("twitterPassword"))
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        time.sleep(7)

        print("Successfully Logged in")
        return driver  # Return the logged-in driver

# %%
def preprocessingTweet(text):
    text = demojize(text); # Convert emoji to text
    text = re.sub(r'@elonmusk', 'Elon Musk', text) # Replace @elonmusk to "Elon Musk"
    text = re.sub(r'@\w+', '[MENTION]', text) # Remove @ to another user
    text = re.sub("\n+", " ", text) # Remove \n
    text = text.strip() # Remove extra spaces
    return text

# %%
def convertToCentral(utc_time_str):
    # Define the UTC timezone
    utc_zone = pytz.utc
    # Define the Central timezone (CST/CDT)
    central_zone = pytz.timezone('US/Central')

    # Parse the input UTC time string into a datetime object
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M")
    utc_time = utc_zone.localize(utc_time)  # Localize to UTC

    # Convert to Central Time
    central_time = utc_time.astimezone(central_zone)

    # Return the Central time in string format
    return central_time.strftime('%Y-%m-%d %I:%M %p')  # 12-hour format

# %%
def humanLikeScroll(driver, duration=30, randDirection = True):

    start_time = time.time()
    actions = ActionChains(driver)

    while time.time() - start_time < duration:
        total_scroll = random.randint(1000, 1500)  # Total distance for one scroll
        steps = random.randint(50, 100)  # Break into small steps
        mid_point = steps//2
        if (randDirection): # if enabled, gives ability to scroll up
            scroll_direction = 1 if random.random() < 0.90 else -1  # 90% chance to scroll down
        else: # if disabled, can only scroll down
            scroll_direction = 1

        for i in range(steps):
        # Acceleration: Slow at start, fast in middle, slow at end
            if i < mid_point:
                step_size = int((i / mid_point) * total_scroll / steps) + 5  # Increasing step size
            else:
                step_size = int(((steps - i) / mid_point) * total_scroll / steps) + 5  # Decreasing step size

            actions.scroll_by_amount(0, step_size * scroll_direction).perform()
            time.sleep(random.uniform(0, 0.02))  # Smooth small delays

        # Random pauses between scrolls
        time.sleep(random.uniform(1, 5))  

        if random.random() < 0.3:  # 30% chance to hover (50% to click)
            try:
                tweets = driver.find_elements("xpath", "//article[@data-testid='tweet']")

                visible_tweets = []
                for t in tweets:  # Loop through each tweet
                    if t.is_displayed():  # Check if the tweet is visible
                        visible_tweets.append(t)  # If yes, add it to the list
                
                if visible_tweets:  # Ensure there are visible tweets
                    tweet = random.choice(visible_tweets)
                    actions.move_to_element(tweet).perform()
                    
                    # Extract tweet text
                    tweet_text = tweet.text.strip()
                    #print(f"Hovering over tweet: {tweet_text[:200]}")  # Print first 200 chars for readability
                    
                    time.sleep(random.uniform(1, 3))  # Pause while hovering

                    # 50% chance to click the tweet
                    if random.random() < 0.5:
                        tweet_link = tweet.find_element("xpath", ".//time/..")  # Gets parent anchor <a> tag
                        tweet_link.click()  # Click the tweet to open it
                        time.sleep(random.uniform(5, 8)) # Keep tweet open for a random duration
                        driver.back() # Go back to the previous page
                        time.sleep(random.uniform(2, 5)) # Wait a bit after going back
            except:
                pass  # If no tweets found, just continue scrolling
    print("Finished human-like scrolling.")


# %%
def getStockData():
    # Define the timezone (Eastern Time)
    tz = pytz.timezone('America/New_York')

    # Get the current time in ET
    now = datetime.now(tz)

    # Adjust the time window to be the **previous** 10-minute window
    start_minute = (now.minute // 10) * 10 - 10  # Shift back by 10 minutes
    if start_minute < 0:
        start_minute += 60  # Handle cases where minute becomes negative
        now = now - timedelta(hours=1)

    start_time = now.replace(minute=start_minute, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=10)  # Now correctly ends at the current 10-minute mark

    # Convert to UTC for filtering
    start_time_utc = start_time.astimezone(pytz.utc)
    end_time_utc = end_time.astimezone(pytz.utc)

    # Convert to date format for Yahoo Finance API
    start_date = start_time.strftime("%Y-%m-%d")
    end_date = (start_time + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        stock = yf.Ticker("TSLA")
        hist = stock.history(interval="1m", start=start_date, end=end_date)

        # Ensure hist.index is timezone-aware
        if hist.index.tzinfo is None:
            hist.index = hist.index.tz_localize('UTC')

        # Print available timestamps
        # print("\nAll timestamps in data:")
        # print(hist.index)

        # Filter based on UTC timestamps
        hist_filtered = hist[(hist.index >= start_time_utc) & (hist.index <= end_time_utc)]

        # Debug output
        # print(f"\nLocal Start Time (ET): {start_time}")
        # print(f"Local End Time (ET): {end_time}")
        # print(f"UTC Start Time: {start_time_utc}")
        # print(f"UTC End Time: {end_time_utc}")

        if hist_filtered.empty:
            print("No data returned for the 10-minute window. Market might be closed.")
            return None

        # Convert to list of dictionaries and include timestamps
        result = [
            {
                "Datetime": idx.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M"), # In UTC
                "Open": row["Open"],
                "High": row["High"],
                "Low": row["Low"],
                "Close": row["Close"],
                "Volume": row["Volume"]
            }
            for idx, row in hist_filtered.iterrows()
        ]

        # Print result with timestamps
        # print("\nFiltered Data:")
        # for entry in result:
        #     print(entry)

        return result
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None


# %%
def extractTweets(driver):
    timeNow = datetime.now(timezone.utc) # Get current UTC time
    timeNow = datetime.now(timezone.utc).replace(microsecond=0) # Remove miliseconds
    tweetsFound = 0 # Count how many unique tweets added to the database
    tweets = []
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()
    
    try:
        # Extract tweet containers (articles with data-testid="tweet")
        tweetElements = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
        # print(f"Elements found {len(tweetElements)}")
        
        for tweet in tweetElements:
            try:
                # Get tweet ID
                tweet_link = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]").get_attribute("href")
                matchID = re.search(r'/status/(\d+)', tweet_link)
                tweet_id = matchID.group(1) # Get digit portion

                # Check if tweet is already in the database
                cursor.execute('SELECT 1 FROM tweets WHERE id = ?', (tweet_id,))
                existing_tweet = cursor.fetchone()
                if existing_tweet: # Skip if a duplicate is found
                    print(f"Duplicate tweet found. Skipping the rest...")
                    break

                # Get tweet creation date (timestamp)
                created_date = tweet.find_element(By.XPATH, ".//time").get_attribute("datetime")
                created_date_DTObject = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                created_date_DTObject = created_date_DTObject.replace(tzinfo=timezone.utc)
                #print(f"{timeNow} - {created_date_DTObject}")
                if timeNow - created_date_DTObject > timedelta(minutes=10): #Skip tweets older than 10 minutes
                    break

                # Get the div with tweetText (multiple spans/imgs with tweet content)
                tweetTextElement = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                
                # Get tweet text (including emoji)
                tweet_text = ""
                # Iterate over all child elements (spans and img) in the tweetText div
                tweet_children = tweetTextElement.find_elements(By.XPATH, ".//span | .//img")
                for child in tweet_children:
                    if child.tag_name == 'span':
                        tweet_text += child.text # If it's a span, get the text
                    elif child.tag_name == 'img':
                        tweet_text += child.get_attribute("alt") # If img, get emoji in the alt attribute
                
                # Get tweet metadata (reply count, retweet count, like count, view count)
                reply_count = tweet.find_element(By.XPATH, ".//button[@data-testid='reply']//span").text
                retweet_count = tweet.find_element(By.XPATH, ".//button[@data-testid='retweet']//span").text
                like_count = tweet.find_element(By.XPATH, ".//button[@data-testid='like']//span").text
                try: # If no views, there won't be a span
                    view_count = tweet.find_element(By.XPATH, ".//a[contains(@aria-label, 'views')]//span").text
                except:
                    view_count = 0
                # Default to 0 if no text is found for any of the counts
                reply_count = reply_count if reply_count else "0"
                retweet_count = retweet_count if retweet_count else "0"
                like_count = like_count if like_count else "0"
       
                # Store tweet data in a dictionary
                tweetData = [
                    tweet_id,
                    tweet_text,
                    preprocessingTweet(tweet_text),
                    reply_count,
                    view_count,
                    like_count,
                    retweet_count,
                    created_date
                ]

                tweets.append(tweetData)
                tweetsFound += 1

                # if (tweetsFound > 4):
                #     break
                
            except Exception as e:
                print(f"Error extracting data from tweet: {e}")
        
    except Exception as e:
        print(f"Error while extracting tweets: {e}")
    
    conn.close()
    print(f"extractTweets found {tweetsFound} tweets")
    tweets.reverse() # From oldest to neweset
    return tweets


# %%
def combineTweetStock(driver):
    conn = sqlite3.connect("rtsProjectDB.db")
    cursor = conn.cursor()
    tweets = extractTweets(driver)
    stockData = getStockData()

    # Convert stock timestamps to minute format
    print("Adding to stock map & stockPrice")
    stock_map = {}
    stocksAdded = 0
    stockToInsert = []
    for stockEntry in stockData:
        # Convert stock timestamp
        stock_time = stockEntry['Datetime']
        stock_map[stock_time] = [
            stockEntry['Open'],
            stockEntry['High'],
            stockEntry['Low'],
            stockEntry['Close'],
            stockEntry['Volume'],
        ]
        # Store stock data separately for graphing
        centralTime = convertToCentral(stockEntry['Datetime'])
        stockToInsert.append((centralTime, stockEntry['Open'], stockEntry['High'], stockEntry['Low'], stockEntry['Close'], stockEntry['Volume']))
        stocksAdded += 1
    cursor.executemany('INSERT OR IGNORE INTO stockPrice (time, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?)', stockToInsert)
    conn.commit()


    # Process tweets
    print("Processing Tweets")
    tweetsAdded = 0
    for tweet in tweets:
        # Add sentiment scores
        sentimentScores = goEmotions.getTextSentiment(tweet[2])
        for category in sentimentScores:
            tweet.append(sentimentScores[category])

        # Match tweet to stock data using time
        tweet_time = tweet[7].strip()  # Strip any extra spaces
        # Remove the '.000Z' and convert to datetime
        tweet_time = datetime.strptime(tweet_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        # Format the datetime object to the desired format
        tweet_time = tweet_time.strftime("%Y-%m-%d %H:%M")

        # Add stock data to tweet
        stockInfo = stock_map.get(tweet_time, [])  # Match creation date/time to stock date/time
        if stockInfo: # If not empty...
            tweet.extend(stockInfo)
        
        # Add to database
        tweet[7] = convertToCentral(tweet_time)
        try:
            cursor.execute('''
                INSERT INTO tweets (id, origText, cleanText, replyCount, viewCount, likeCount, retweetCount, createdDate,
                                    Positive, Hopeful, Pride, Approval, Curiosity, Fear, Remorse, Sadness, Disapproval, Neutral,
                                    open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', tweet)
            conn.commit()
            tweetsAdded += 1
        except Exception as e:
            print(f"Error inserting tweet into database: {e}") # Most likely 3 pm missing stock information

    
    conn.close()
    print(f'{stocksAdded} stocks added and {tweetsAdded} tweets added!')
    return f'{stocksAdded} stocks added and {tweetsAdded} tweets added!'

# %%
def tempLogin():
    driver = setupDriver()
    #driver.get("https://x.com/i/flow/login")

    driver.get("https://x.com")  # Navigate to the homepage or login page to check if we have cookies
    time.sleep(5)  # Wait for the page to load
        
    # Check if the account menu is available, meaning we're already logged in
    if checkAccountLoggedIn(driver):
        print("Logged in using cookies.")
        return driver  # Return the driver with cookies applied
