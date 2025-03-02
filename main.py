from twikit import Client, TooManyRequests
from dotenv import load_dotenv
import asyncio
import os
import time
from datetime import datetime
from random import randint
import re
from emoji import demojize
import sqlite3

load_dotenv();

# Authenticate to X.com (Twitter)
client = Client(language='en-US')
async def twitterLogin():
    if client is None:
        print("Client initialization failed.")
        return
    await client.login(auth_info_1=os.getenv("twitterUsername"), auth_info_2=os.getenv("twitterEmail"), password=os.getenv("twitterPassword"))
    client.save_cookies('cookies.json')


# Get Tweets
async def getTwitterPosts():
    conn = sqlite3.connect("realTimeData.db")
    cursor = conn.cursor()
    tweets = await client.search_tweet("($TSLA) lang:en -filter:links", product='Latest', count=10)
    tweetCount = 0
    for tweet in tweets:
        tweetCount += 1
        tweetData = [
            tweet.id,
            tweet.text,
            preprocessingTweet(tweet.text), 
            tweet.reply_count, 
            tweet.view_count, 
            tweet.favorite_count, 
            tweet.retweet_count, 
            tweet.created_at
        ]
        cursor.execute('''
            INSERT INTO tweets (id, origText, cleanText, replyCount, viewCount, favoriteCount, retweetCount, createdDate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', tweetData)

        conn.commit()
        conn.close()

def preprocessingTweet(text):
    text = demojize(text); # Convert emoji to text
    text = re.sub(r'@\w+', '[MENTION]', text) # Remove @ to another user
    text = re.sub(r'#(\w+)', r'\1', text) # Remove # but keeps text
    text = re.sub("\n+", " ", text) # Remove \n
    text = text.strip() # Remove extra spaces
    return text


client.load_cookies('cookies.json')
#asyncio.run(twitterLogin())
asyncio.run(getTwitterPosts())

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
        createdDate TEXT NOT NULL
    )
''')
conn.commit()