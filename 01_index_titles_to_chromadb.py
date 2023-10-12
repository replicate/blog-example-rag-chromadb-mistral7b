import json

import replicate
import chromadb

from tqdm.auto import tqdm

# Initialize the chromadb directory, and client.
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_or_create_collection(name=f"hackernews-topstories-2023")

# Create an empty list which we will populate with jsonl entries.
hn_dataset = []

# Load the 13509-hn-topstories-2023.jsonl into a list of dictionaries
with open("13509-hn-topstories-2023.jsonl", "r") as f:
    for line in f:
        hn_dataset.append(json.loads(line))

# Generate embeddings, and index titles in batches of 250.
batch_size = 250

# Use tqdm to show a friendly progress bar.
for i in tqdm(range(0, len(hn_dataset), batch_size)):
    # set end position of batch
    i_end = min(i + batch_size, len(hn_dataset))

    # Get next batch of 250 lines
    batch = hn_dataset[i : i + batch_size]

    # When storing data in ChromaDB, we construct a list of titles, ids, and metadata.
    # NOTE: It is important that each of these lists is the same size, and that
    # each list index position corresponds with the others.
    batch_titles = [story["title"] for story in batch]
    batch_ids = [str(story["id"]) for story in batch]
    batch_metadata = [dict(score=story["score"], time=story["time"]) for story in batch]

    # Generate embeddings, 250 titles at a time.
    batch_embeddings = replicate.run(
        "nateraw/bge-large-en-v1.5:9cf9f015a9cb9c61d1a2610659cdac4a4ca222f2d3707a68517b18c198a9add1",
        input={"texts": json.dumps(batch_titles)},
    )

    # Upsert all of the embeddings, ids, metadata, and title strings into ChromaDB.
    collection.upsert(
        ids=batch_ids,
        metadatas=batch_metadata,
        documents=batch_titles,
        embeddings=batch_embeddings,
    )
