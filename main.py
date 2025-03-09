import twitterScraper
import config
import asyncio
import sqlite3

# Create database for twitter data if it doesn't exist 
conn = sqlite3.connect("realTimeData.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        id DECIMAL(25, 0) PRIMARY KEY,
        origText TEXT NOT NULL,
        cleanText TEXT NOT NULL,
        replyCount INTEGER NOT NULL DEFAULT 0,
        viewCount INTEGER NOT NULL DEFAULT 0,
        favoriteCount INTEGER NOT NULL DEFAULT 0,
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
        Neutral REAL NOT NULL
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweet_id ON tweets (id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_date ON tweets (createdDate)')
conn.commit()

async def fetchTweetsPeriodically():
    while True:
        if (config.twitterRateLimitReached):
            print("Rate limit reached. Waiting 15 mins...")
            await asyncio.sleep(900)
            config.twitterRateLimitReached = False
        else:
            print("Getting Twitter posts...")
            await twitterScraper.getTwitterPosts()
            print("Waiting 7 mins...")
            await asyncio.sleep(420)

async def main():
    await twitterScraper.twitterLogin()
    asyncio.create_task(fetchTweetsPeriodically())
    while True:
        await asyncio.sleep(3600)

asyncio.run(main());