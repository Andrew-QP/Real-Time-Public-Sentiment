import asyncio
import sqlite3

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
        Neutral REAL NOT NULL
    )
''')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_tweet_id ON tweets (id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_date ON tweets (createdDate)')
conn.commit()