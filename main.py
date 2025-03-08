import twitter
import asyncio
import sqlite3

# Create database for twitter data if it doesn't exist 
conn = sqlite3.connect("realTimeData.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        id INTEGER PRIMARY KEY,
        origText TEXT NOT NULL,
        cleanText TEXT NOT NULL,
        replyCount INTEGER NOT NULL,
        viewCount INTEGER NOT NULL,
        favoriteCount INTEGER NOT NULL,
        retweetCount INTEGER NOT NULL,
        createdDate TEXT NOT NULL,
        Positive Decimal(7, 5) NOT NULL,
        Hopeful Decimal(7, 5) NOT NULL, 
        Pride Decimal(7, 5) NOT NULL, 
        Approval Decimal(7, 5) NOT NULL, 
        Curiosity Decimal(7, 5) NOT NULL, 
        Fear Decimal(7, 5) NOT NULL, 
        Remorse Decimal(7, 5) NOT NULL, 
        Sadness Decimal(7, 5) NOT NULL, 
        Disapproval Decimal(7, 5) NOT NULL, 
        Neutral Decimal(7, 5) NOT NULL
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweet_id ON tweets (id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_date ON tweets (createdDate)')
conn.commit()

async def fetchTweetsPeriodically():
    while True:
        print("Getting Twitter posts...")
        await twitter.getTwitterPosts()
        print("Waiting 5 mins...")
        await asyncio.sleep(300)

async def main():
    await twitter.twitterLogin()
    asyncio.create_task(fetchTweetsPeriodically())
    while True:
        await asyncio.sleep(3600)

asyncio.run(main());