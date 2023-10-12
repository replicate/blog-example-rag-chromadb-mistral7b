import json
import sys

import chromadb
import replicate

from chromadb import Documents


# Use bge-large-en-v1.5 on Replicate to generate embeddings.
def generate_embeddings(texts: Documents):
    return replicate.run(
        "nateraw/bge-large-en-v1.5:9cf9f015a9cb9c61d1a2610659cdac4a4ca222f2d3707a68517b18c198a9add1",
        input={"texts": json.dumps(texts)},
    )


# Instantiate the chromadb client, with embedding function
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_or_create_collection(
    name=f"hackernews-topstories-2023", embedding_function=generate_embeddings
)

# Accept a user prompt from the first command line argument.
user_prompt = sys.argv[1]

# Query ChromaDB for the 10 most similar titles to the user prompt.
results = collection.query(
    query_texts=[user_prompt],
    n_results=20,
)

# Concatenate the results into a single string, which we will shove into the prompt.
successful_titles = "\n".join(results["documents"][0])

# LLM Prompt template.
# NOTE: The [INST] and [/INST] tags are required for mistral-7b-instruct to leverage instruction fine-tuning.
PROMPT_TEMPLATE = f"""[INST]
You are an expert in all things HackerNews. Your goal is to help me write the most click worthy HackerNews title that will get the most upvotes. You will be given a USER_PROMPT, and a series of SUCCESSFUL_TITLES. You will respond with 5 suggestions for better hackernews titles.

All of your suggestions should be structured in the same format and tone as the previously successful SUCCESSFUL_TITLES. Make sure you do not include specific versions from the SUCCESSFUL_TITLES in your suggestions.

USER_PROMPT: {user_prompt}

SUCCESSFUL_TITLES: {successful_titles}

SUGGESTIONS:

[/INST]
"""


# Prompt the mistral-7b-instruct LLM
mistral_response = replicate.run(
    "a16z-infra/mistral-7b-instruct-v0.1:83b6a56e7c828e667f21fd596c338fd4f0039b46bcfa18d973e8e70e455fda70",
    input={
        "prompt": PROMPT_TEMPLATE,
        "temperature": 0.75,
        "max_new_tokens": 2048,
    },
)

# Concatenate the response into a single string.
suggestions = "".join([str(s) for s in mistral_response])

# Print the suggestions.
print(suggestions)

print("====")

print("PROMPT_TEMPLATE", PROMPT_TEMPLATE)
