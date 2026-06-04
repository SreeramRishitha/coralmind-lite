from sentence_transformers import SentenceTransformer
import numpy as np

# Load a small fast model
model = SentenceTransformer('all-MiniLM-L6-v2')

# These are your CoralMind query types
queries = [
    "who are the top contributors",
    "show merged pull requests", 
    "any bugs open",
    "show incidents",
    "what is being worked on",
]

# User questions to test
user_questions = [
    "who built this repo",
    "what was recently shipped",
    "are there any errors",
    "production outages",
    "current active work",
]

print("Generating embeddings...\n")
query_embeddings = model.encode(queries)
user_embeddings = model.encode(user_questions)

print("Matching user questions to query types:\n")
for i, user_q in enumerate(user_questions):
    similarities = np.dot(user_embeddings[i], query_embeddings.T)
    best_match = queries[np.argmax(similarities)]
    score = np.max(similarities)
    print(f"'{user_q}'")
    print(f"  → matches: '{best_match}' (score: {score:.2f})\n")