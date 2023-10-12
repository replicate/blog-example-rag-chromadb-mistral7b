import sqlite3
import json

# Connect to the SQLite database
conn = sqlite3.connect("hn.db")
cursor = conn.cursor()

# Execute the query
query = """
    SELECT id, score, title, url, time
    FROM stories
    WHERE score > 100 AND type = 'story';
"""
cursor.execute(query)

# Fetch all results
results = cursor.fetchall()

# Close the database connection
conn.close()

# Open a file to write the data
with open("output.jsonl", "w") as f:
    for row in results:
        # Create a dictionary from the row data
        record = {
            "id": row[0],
            "score": row[1],
            "title": row[2],
            "url": row[3],
            "time": row[4],
        }
        # Write the dictionary to the file as a JSON-formatted string
        f.write(json.dumps(record) + "\n")
