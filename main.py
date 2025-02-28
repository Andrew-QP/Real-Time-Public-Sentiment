from twikit import Client, TooManyRequests
from dotenv import load_dotenv
import asyncio
import os
import time
from datetime import datetime
from random import randint

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
    tweets = await client.search_tweet("Elon", product='Top')
    tweetCount = 0
    for tweet in tweets:
        tweetCount += 1
        tweetData = [tweetCount, tweet.user.name, tweet.text, tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.reply_count]
        print(tweetData)
        break;



client.load_cookies('cookies.json')
# asyncio.run(twitterLogin())
asyncio.run(getTwitterPosts());