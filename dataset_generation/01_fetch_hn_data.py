from tqdm import tqdm
import asyncio
import aiohttp
import sqlite3
import random

# Number of retries
RETRIES = 5

# Base delay in seconds
DELAY = 1


async def fetch(session, url, progress):
    for i in range(RETRIES):
        try:
            async with session.get(url) as response:
                data = await response.json()
                progress.update(1)  # Update the progress bar
                return data
        except Exception as e:
            # Exponential backoff with jitter
            await asyncio.sleep(DELAY * 2**i + random.uniform(0.1, 0.3))
    print(f"Failed to fetch {url} after {RETRIES} retries")
    return None


async def fetch_stories(session, story_ids, progress, c):
    tasks = []
    for story_id in story_ids:
        # Check if the story already exists in the database
        c.execute("SELECT 1 FROM stories WHERE id = ?", (story_id,))
        if c.fetchone() is None:
            # If the story doesn't exist, fetch it
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            tasks.append(
                fetch(session, story_url, progress)
            )  # Pass the progress bar to the fetch function

    stories = await asyncio.gather(*tasks)
    return stories


# Create a new SQLite database and a table
conn = sqlite3.connect("./hn.db")
c = conn.cursor()

c.execute(
    """
    CREATE TABLE IF NOT EXISTS stories
    (id INT PRIMARY KEY NOT NULL,
    deleted BOOLEAN,
    type TEXT,
    by TEXT,
    time INT,
    text TEXT,
    dead BOOLEAN,
    parent INT,
    poll INT,
    kids TEXT,
    url TEXT,
    score INT,
    title TEXT,
    parts TEXT,
    descendants INT);
    """
)

conn.commit()

# Generate the list of story ids for the last year
story_ids = list(range(34209496, 37778496))

chunk_size = 500
progress = tqdm(total=len(story_ids))


async def main():
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(story_ids), chunk_size):
            chunk_ids = story_ids[i : i + chunk_size]

            # Fetch individual stories
            stories = await fetch_stories(session, chunk_ids, progress, c)

            # Insert the data into the database
            for story in stories:
                if story is not None:  # Check if the story is not None
                    c.execute(
                        """
                        INSERT OR IGNORE INTO stories (id, deleted, type, by, time, text, dead, parent, poll, kids, url, score, title, parts, descendants)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            story["id"],
                            story.get("deleted"),
                            story.get("type"),
                            story.get("by"),
                            story.get("time"),
                            story.get("text"),
                            story.get("dead"),
                            story.get("parent"),
                            story.get("poll"),
                            str(story.get("kids")),
                            story.get("url"),
                            story.get("score"),
                            story.get("title"),
                            str(story.get("parts")),
                            story.get("descendants"),
                        ),
                    )

            conn.commit()


# Run the main function
asyncio.run(main())
