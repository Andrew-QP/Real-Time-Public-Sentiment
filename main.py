from twikit import Client, TooManyRequests
from dotenv import load_dotenv
import asyncio
import os
import time
from datetime import datetime
from random import randint
import re
from emoji import demojize

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
    tweets = await client.search_tweet("(Elon OR Musk) min_faves:10 lang:en -filter:links filter:replies", product='Latest', count=10)
    tweetCount = 0
    for tweet in tweets:
        tweetCount += 1
        #tweetData = [tweetCount, preprocessing_tweet(tweet.text), tweet.reply_count, tweet.view_count, tweet.favorite_count, tweet.retweet_count, tweet.created_at]
        #print(tweetData)
        print([tweetCount, tweet.text])
        print([tweetCount, preprocessing_tweet(tweet.text)])

def preprocessing_tweet(text):
    text = demojize(text); # Convert emoji to text
    text = re.sub(r'@\w+', '[MENTION]', text) # Remove @ to another user
    text = re.sub(r'#(\w+)', r'\1', text) # Remove # but keeps text
    text = text.strip() # Remove extra spaces
    return text


client.load_cookies('cookies.json')
# asyncio.run(twitterLogin())
asyncio.run(getTwitterPosts());