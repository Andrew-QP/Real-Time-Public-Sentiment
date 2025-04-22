# import sqlite3

# # Connect to your SQLite database
# conn = sqlite3.connect('rtsProjectDB.db')
# cursor = conn.cursor()

# # Step 1: Get the ID of the last row
# cursor.execute("SELECT ROWID FROM simplePrediction ORDER BY ROWID DESC LIMIT 1")
# last_row = cursor.fetchone()

# # Step 2: Delete the row if it exists
# if last_row:
#     last_id = last_row[0]
#     cursor.execute("DELETE FROM simplePrediction WHERE ROWID = ?", (last_id,))
#     conn.commit()
#     print(f"Deleted row with ID {last_id}")
# else:
#     print("No rows to delete.")

# # Close connection
# conn.close()
# print(last_row)

# # Connect to your SQLite database
# conn = sqlite3.connect('rtsProjectDB.db')
# cursor = conn.cursor()

# # Step 1: Get the ID of the last row
# cursor.execute("SELECT ROWID FROM sentimentPrediction ORDER BY ROWID DESC LIMIT 1")
# last_row = cursor.fetchone()

# # Step 2: Delete the row if it exists
# if last_row:
#     last_id = last_row[0]
#     cursor.execute("DELETE FROM sentimentPrediction WHERE ROWID = ?", (last_id,))
#     conn.commit()
#     print(f"Deleted row with ID {last_id}")
# else:
#     print("No rows to delete.")

# # Close connection
# conn.close()
# print(last_row)

# from datetime import datetime, timedelta
# import models.sentimentModel.use_model as sentiModel
# import models.simpleModel.use_model as simpleModel
# import sqlite3
# def make_predictions():

#     # Predicting with simple model
#     simpleModels = simpleModel.list_available_models()
#     simplePrediction = simpleModel.predict_next_10_minutes(sorted(simpleModels, reverse=True)[0])
#     try:
#         with sqlite3.connect("rtsProjectDB.db") as local_conn:
#             local_cursor = local_conn.cursor()
#             # Get the latest (last inserted) time from stockPrice
#             local_cursor.execute('SELECT time FROM stockPrice ORDER BY rowid DESC LIMIT 1')
#             row = local_cursor.fetchone()

#             if row:
#                 last_time_str = row[0]
#                 dt_format = "%Y-%m-%d %I:%M %p"

#                 # Convert to datetime, add 10 minutes
#                 last_time = datetime.strptime(last_time_str, dt_format)
#                 next_time = last_time + timedelta(minutes=10)

#                 # Convert back to string in same format
#                 time_str = next_time.strftime(dt_format)

#             print(f'Simple model predicts {simplePrediction:.2f} at {time_str}')
#     except Exception as e:
#         print("ERROR1")

#     # Predicting with sentiment model
#     sentimentModels = sentiModel.list_available_models()
#     sentimentPrediction = sentiModel.predict_next_10_minutes(sorted(sentimentModels, reverse=True)[0])  
#     try:
#         with sqlite3.connect("rtsProjectDB.db") as local_conn:
#             local_cursor = local_conn.cursor()
#             # Get the latest (last inserted) time from tweets
#             local_cursor.execute('SELECT createdDate FROM tweets ORDER BY rowid DESC LIMIT 1')
#             row = local_cursor.fetchone()

#             if row:
#                 last_time_str = row[0]
#                 dt_format = "%Y-%m-%d %I:%M %p"

#                 # Convert to datetime, add 10 minutes
#                 last_time = datetime.strptime(last_time_str, dt_format)
#                 next_time = last_time + timedelta(minutes=10)

#                 # Convert back to string in same format
#                 time_str = next_time.strftime(dt_format)
#             print(f'Sentiment model predicts {sentimentPrediction:.2f} at {time_str}')
#     except Exception as e:
#         print("ERROR2")


# make_predictions()


import sqlite3

conn = sqlite3.connect('rtsProjectDB.db')
cursor = conn.cursor()


# # Step 1: Rename old tables
# cursor.execute('ALTER TABLE simplePrediction RENAME TO old_simplePrediction')
# cursor.execute('ALTER TABLE sentimentPrediction RENAME TO old_sentimentPrediction')

# # Step 2: Create new tables with time as PRIMARY KEY
# cursor.execute('''
#     CREATE TABLE simplePrediction (
#         time TEXT PRIMARY KEY,
#         prediction DECIMAL(10, 2)
#     )
# ''')

# cursor.execute('''
#     CREATE TABLE sentimentPrediction (
#         time TEXT PRIMARY KEY,
#         prediction DECIMAL(10, 2)
#     )
# ''')

# # Step 3: Copy data (only if time values are unique)
# cursor.execute('INSERT INTO simplePrediction SELECT * FROM old_simplePrediction')
# cursor.execute('INSERT INTO sentimentPrediction SELECT * FROM old_sentimentPrediction')

# # Step 4: (Optional) Drop old tables if everything looks good
cursor.execute('DROP TABLE old_simplePrediction')
cursor.execute('DROP TABLE old_sentimentPrediction')

conn.commit()

conn.close()
