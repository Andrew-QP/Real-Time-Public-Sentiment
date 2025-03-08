import goEmotions
from twikit import Client, TooManyRequests
from dotenv import load_dotenv
import asyncio
import os
from random import randint
import re
from emoji import demojize
import sqlite3

load_dotenv();

client = Client(language='en-US')

# Authenticate to X.com (Twitter)
async def twitterLogin():
    try:
        client.load_cookies('cookies.json')
        print("Succesfully Logged in with Cookies")
    except:
        await client.login(auth_info_1=os.getenv("twitterUsername"), auth_info_2=os.getenv("twitterEmail"), password=os.getenv("twitterPassword"))
        client.save_cookies('cookies.json')
        print("Successfully Logged in using User Details")


# Get Tweets
async def getTwitterPosts():
    conn = sqlite3.connect("realTimeData.db")
    cursor = conn.cursor()
    tweets = await client.search_tweet("($TSLA) lang:en -filter:links", product='Latest', count=10)
    tweetCount = 0
    for tweet in tweets:
        # Check if tweet is already in the database
        cursor.execute('SELECT COUNT(*) FROM tweets WHERE id = ?', (tweet.id,))
        existing_tweet_count = cursor.fetchone()[0]
        
        if existing_tweet_count > 0: # Skip tweet if its already in the database
            print(f"Tweet {tweet.id} already exists. Skipping...")
            continue 

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
        sentimentScores = goEmotions.getTextSentiment(tweet.text)
        for category in sentimentScores:
            tweetData.append(sentimentScores[category])

        cursor.execute('''
            INSERT INTO tweets (id, origText, cleanText, replyCount, viewCount, favoriteCount, retweetCount, createdDate,
                       Positive, Hopeful, Pride, Approval, Curiosity, Fear, Remorse, Sadness, Disapproval, Neutral)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tweetData)
        conn.commit()
        tweetCount += 1
    conn.close()
    print(f"{tweetCount} tweets added to the database")

def preprocessingTweet(text):
    text = demojize(text); # Convert emoji to text
    text = re.sub(r'@\w+', '[MENTION]', text) # Remove @ to another user
    text = re.sub(r'#(\w+)', r'\1', text) # Remove # but keeps text
    text = re.sub("\n+", " ", text) # Remove \n
    text = text.strip() # Remove extra spaces
    return text