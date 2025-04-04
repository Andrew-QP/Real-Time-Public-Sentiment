import twitterWebScraper as tws
import sqlite3
import time
import random
import logging
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Create database for twitter data if it doesn't exist 
conn = sqlite3.connect("rtsProjectDB.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        id DECIMAL(25, 0) PRIMARY KEY,
        origText TEXT NOT NULL,
        cleanText TEXT NOT NULL,
        replyCount INTEGER NOT NULL DEFAULT 0,
        viewCount INTEGER NOT NULL DEFAULT 0,
        likeCount INTEGER NOT NULL DEFAULT 0,
        retweetCount INTEGER NOT NULL DEFAULT 0,
        createdDate TEXT NOT NULL,
               
        Positive REAL NOT NULL,
        Hopeful REAL NOT NULL, 
        Pride REAL NOT NULL, 
        Approval REAL NOT NULL, 
        Curiosity REAL NOT NULL, 
        Fear REAL NOT NULL, 
        Remorse REAL NOT NULL, 
        Sadness REAL NOT NULL, 
        Disapproval REAL NOT NULL, 
        Neutral REAL NOT NULL,
               
        open DECIMAL(10, 2) NOT NULL, 
        high DECIMAL(10, 2) NOT NULL, 
        low DECIMAL(10, 2) NOT NULL, 
        close DECIMAL(10, 2) NOT NULL, 
        volume INTEGER NOT NULL
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweet_id ON tweets (id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_date ON tweets (createdDate)')
conn.commit()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stockPrice (
        time TEXT PRIMARY KEY,
        open DECIMAL(10, 2) NOT NULL,
        high DECIMAL(10, 2) NOT NULL,
        low DECIMAL(10, 2) NOT NULL,
        close DECIMAL(10, 2) NOT NULL,
        volume INTEGER NOT NULL
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_prices_time ON stockPrice(time)')
conn.commit()

# Custom time converter for Central Time
def central_time_converter(*args):
    return datetime.now(pytz.timezone("US/Central")).timetuple()
logging.basicConfig(
    filename='collector.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %I:%M:%S %p'
)
logging.Formatter.converter = central_time_converter

# Task functions
def collectData():
    try:
        logging.info("Starting data collection...")
        driver.refresh()
        sleep_duration = random.uniform(60, 120)  # Random time between 1 and 2 minutes
        logging.info(f"Sleeping for {sleep_duration:.2f} seconds before scrolling")
        time.sleep(sleep_duration)
        tws.humanLikeScroll(driver, 5)
        logOutput = tws.combineTweetStock(driver)
        if logOutput:
            logging.info(logOutput)
        logging.info("Data collection completed successfully.")
    except Exception as e:
        logging.error(f"collectData failed: {e}")

def make_predictions():
    logging.info("Making predictions...")

def update_graphs():
    logging.info("Updating graphs...")


# Task completion listener
def task_listener(event):
    if event.job_id == 'collect_data':
        if event.exception is None: 
            logging.info("collect_data detected by completion listener.")
        else:
            logging.error(f"collect_data encountered an error in listener: {event.exception}")
        time.sleep(5)
        # make_predictions()
        # update_graphs()
        logging.info("Task listener finished.\n--------------")



# Initialize BackgroundScheduler
scheduler = BackgroundScheduler()

# Add jobs to scheduler (set specific times for tweet and finance data collection)
scheduler.add_job(collectData, 'cron', minute='0, 10, 20, 30, 40, 50', id='collect_data')

# Add listener for task completion
scheduler.add_listener(task_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Start the scheduler
print("Starting...")
driver = tws.login()
driver.get("https://x.com/search?q=%24TSLA%20lang%3Aen%20-filter%3Alinks&f=live&src=typed_query")
scheduler.start()







# To keep the program running
try:
    while True:
        time.sleep(1)  # Keeps the program running, allowing scheduler to run in background
except (KeyboardInterrupt, SystemExit):
    # Shut down the scheduler gracefully when exiting
    logging.info("Shutting down...")
    driver.quit()
    scheduler.shutdown()