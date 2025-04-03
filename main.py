#import twitterWebScraper as tws
import asyncio
import sqlite3
import time
import threading
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

# # Task functions
# def collect_tweet_data():
#     print("Collecting tweet data...")

# def collect_finance_data():
#     print("Collecting finance data...")

# def make_predictions():
#     print("Making predictions...")

# def update_graphs():
#     print("Updating graphs...")

# # Global flags to track task completion
# tweet_data_collected = False
# finance_data_collected = False
# lock = threading.Lock()

# # Task completion listener
# def task_listener(event):
#     global tweet_data_collected, finance_data_collected

#     # Listen for completion of tasks
#     with lock:
#         if event.job_id == 'collect_tweets' and event.exception is None:
#             tweet_data_collected = True
#             print("Tweet data collection completed.")

#         elif event.job_id == 'collect_finance' and event.exception is None:
#             finance_data_collected = True
#             print("Finance data collection completed.")

#         # Trigger predictions only if both data collection tasks are completed
#         print(f"{tweet_data_collected} | {finance_data_collected}")
        
#         # Trigger predictions and graph updates only once after both are done
#         if tweet_data_collected and finance_data_collected:
#             # Ensure tasks are triggered only once
#             print("Both data collections completed. Running predictions and updating graphs.")
            
#             time.sleep(5)
#             make_predictions()
#             update_graphs()
#             print("--------------")
            
#             # Reset the flags after triggering the tasks
#             tweet_data_collected = False
#             finance_data_collected = False


# # Initialize BackgroundScheduler
# scheduler = BackgroundScheduler()

# # Add jobs to scheduler (set specific times for tweet and finance data collection)
# scheduler.add_job(collect_tweet_data, 'cron', minute='2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58', id='collect_tweets')
# scheduler.add_job(collect_finance_data, 'cron', minute='2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58', id='collect_finance')

# # Add listener for task completion
# scheduler.add_listener(task_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# # Start the scheduler
# # driver = tws.login()
# # driver.get("https://x.com/search?q=%24TSLA%20lang%3Aen%20-filter%3Alinks&f=live&src=typed_query")
# print("Starting...")
# scheduler.start()







# # To keep the program running
# try:
#     while True:
#         time.sleep(1)  # Keeps the program running, allowing scheduler to run in background
# except (KeyboardInterrupt, SystemExit):
#     # Shut down the scheduler gracefully when exiting
#     scheduler.shutdown()







# driver = login()
# driver.get("https://x.com/search?q=%24TSLA%20lang%3Aen%20-filter%3Alinks&f=live&src=typed_query")

# extractTweets(driver)

# humanLikeScroll(driver, 15)

# driver.quit()