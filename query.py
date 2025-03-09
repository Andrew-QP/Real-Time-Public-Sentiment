import sqlite3

conn = sqlite3.connect("realTimeData.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM tweets WHERE id = '1898453107765612662'")
results = cursor.fetchall()

for row in results:
    print(row)

conn.close()