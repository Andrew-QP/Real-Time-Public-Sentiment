import twitterWebScraper as tws
from models.simpleModel.use_model import list_available_models,predict_next_10_minutes
import sqlite3
import time
import random
import logging
import pytz
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.triggers.cron import CronTrigger

stop_program = False

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

        anger REAL DEFAULT 0,
        anticipation REAL DEFAULT 0,
        disgust REAL DEFAULT 0,
        fear REAL DEFAULT 0,
        joy REAL DEFAULT 0,
        love REAL DEFAULT 0,
        optimism REAL DEFAULT 0,
        pessimism REAL DEFAULT 0,
        sadness REAL DEFAULT 0,
        surprise REAL DEFAULT 0,
        trust REAL DEFAULT 0,

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
# Table for stock prices
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
# Table for flags
cursor.execute('''
    CREATE TABLE IF NOT EXISTS flags (
        id INTEGER PRIMARY KEY,
        update_graph INTEGER DEFAULT 0
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_flags_id ON flags(id)')
conn.commit()
# Initialize the flags table with a default value if it doesn't exist
cursor.execute('SELECT COUNT(*) FROM flags')
count = cursor.fetchone()[0]
if count == 0:
    cursor.execute('INSERT INTO flags (id, update_graph) VALUES (1, 0)')
    conn.commit()

# Create predictions table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        time TEXT NOT NULL,
        stockPred DECIMAL(10, 2),
        stockSentimentPred DECIMAL(10, 2)
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_time ON predictions (time)')
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
        sleep_duration = random.uniform(60, 90)  # Random time between 1 and 1.5 minutes
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
    models = list_available_models()
    prediction = predict_next_10_minutes(sorted(models, reverse=True)[0])
    
    # Get the latest (last inserted) time from stockPrice
    cursor.execute('SELECT time FROM stockPrice ORDER BY rowid DESC LIMIT 1')
    row = cursor.fetchone()

    if row:
        last_time_str = row[0]
        dt_format = "%Y-%m-%d %I:%M %p"

        # Convert to datetime, add 10 minutes
        last_time = datetime.strptime(last_time_str, dt_format)
        next_time = last_time + timedelta(minutes=10)

        # Convert back to string in same format
        time_str = next_time.strftime(dt_format)

    logging.info(f'Stock data only predicts {prediction:.2f} at {time_str}')
    cursor.execute('''
    INSERT INTO predictions (time, stockPred, stockSentimentPred)
    VALUES (?, ?, ?)
''', (time_str, prediction, None)) # Need to add stockSentimentPred
    conn.commit()

# Task completion listener
def task_listener(event):
    if event.job_id == 'collect_data':
        if event.exception is None: 
            logging.info("collect_data detected by completion listener.")
        else:
            logging.error(f"collect_data encountered an error in listener: {event.exception}")
        time.sleep(5)
        make_predictions()

        try:
            with sqlite3.connect("rtsProjectDB.db") as local_conn:
                local_cursor = local_conn.cursor()
                local_cursor.execute("UPDATE flags SET update_graph = 1 WHERE id = 1")
                local_conn.commit()
                print("Set update flag to 1")
        except Exception as e:
            logging.error(f"Error updating flags in task_listener: {e}")


        logging.info("Task listener finished.\n--------------")

def stockMarketClose():
    global stop_program
    current_time = datetime.now(pytz.timezone("US/Central"))
    if current_time.hour == 15 and current_time.minute >= 8:
        stop_program = True

# Initialize BackgroundScheduler
scheduler = BackgroundScheduler()

# Add jobs to scheduler (set specific times for tweet and finance data collection)
scheduler.add_job(collectData, 'cron', minute='1, 11, 21, 31, 41, 51', id='collect_data')
scheduler.add_job(stockMarketClose, CronTrigger(minute="*", hour="15"), id='stockMarketClose')

# Add listener for task completion
scheduler.add_listener(task_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Start the scheduler
print("Starting...")
driver = tws.login()
if not driver:
    logging.error("Driver initialization failed. Exiting...")
    sys.exit(1)
driver.get("https://x.com/search?q=%24TSLA%20lang%3Aen%20-filter%3Alinks&f=live&src=typed_query")
scheduler.start()




try:
    while not stop_program:
            time.sleep(1)  # Keeps the program running, allowing scheduler to run in background
except (KeyboardInterrupt, SystemExit):
    logging.info("Received exit signal. Shutting down...")

finally:
    logging.info("Cleaning up: closing driver and shutting down scheduler.")
    try:
        driver.quit()
    except Exception as e:
        logging.error(f"Error quitting driver: {e}")
    try:
        if scheduler.running:
            scheduler.shutdown()
    except Exception as e:
        logging.error(f"Error shutting down scheduler: {e}")
