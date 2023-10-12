import json

import chromadb
import replicate

from chromadb import Documents


# This function will be used to convert the query string to embeddings, so we can
# perform a similarity search against the embedding space.
#
# This is configured to use the bge-large-en-v1.5 embeddings model
def generate_embeddings(texts: Documents):
    return replicate.run(
        "nateraw/bge-large-en-v1.5:9cf9f015a9cb9c61d1a2610659cdac4a4ca222f2d3707a68517b18c198a9add1",
        input={"texts": json.dumps(texts)},
    )


# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./chromadb")

# Note the `embedding_function` keyword argument. When supplied like this,
# ChromaDB will seamlessly convert a query string to embedding vectors, which get
# used for similarity search.
collection = client.get_or_create_collection(
    name=f"hackernews-topstories-2023", embedding_function=generate_embeddings
)

# We will be searching for results that are similar to this string
query_string = "how to create a sqlite extension"

# Perform the ChromaDB query.
results = collection.query(
    query_texts=[query_string],
    n_results=10,
)

# Create a string from all of the results
results = "\n".join(results["documents"][0])

# Print the results
print(results)
