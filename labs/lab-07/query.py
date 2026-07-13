
import os
import sys
from pathlib import Path

import chromadb
import requests
from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]

load_dotenv(BASE_DIR / ".env")
load_dotenv(REPO_ROOT / ".env", override=False)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")
RERANK_MODEL = os.getenv("RERANK_MODEL", "cohere/rerank-v3.5")

if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY")

openrouter = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

chroma_client = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))


def embed_query(query):
    response = openrouter.embeddings.create(
        model=EMBED_MODEL,
        input=[query],
    )
    return response.data[0].embedding


def query_chroma(question, n_results=25):
    collection = chroma_client.get_collection(name="node-docs")
    query_embedding = embed_query(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    candidates = []

    for i, doc_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][i]

        candidates.append({
            "id": doc_id,
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": distance,
            "similarity": 1 - distance,
            "chroma_rank": i + 1,
        })

    return candidates


def rerank(question, candidates, top_n=5):
    documents = [candidate["document"] for candidate in candidates]

    response = requests.post(
        "https://openrouter.ai/api/v1/rerank",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": RERANK_MODEL,
            "query": question,
            "documents": documents,
            "top_n": top_n,
        },
        timeout=60,
    )

    response.raise_for_status()
    data = response.json()

    reranked = []

    for item in data.get("results", []):
        index = item["index"]
        candidate = dict(candidates[index])
        candidate["rerank_score"] = item.get("relevance_score")
        reranked.append(candidate)

    return reranked


def main():
    if len(sys.argv) < 2:
        print('Usage: python query.py "How do I read a file?"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    candidates = query_chroma(question, n_results=25)
    reranked = rerank(question, candidates, top_n=5)

    print(f"\nQuestion: {question}")
    print("\nTop reranked results:\n")

    for result in reranked:
        metadata = result["metadata"]

        print("=" * 80)
        print(f"Chroma rank: {result['chroma_rank']}")
        print(f"Source: {metadata.get('source')}")
        print(f"Breadcrumb: {metadata.get('breadcrumb')}")
        print(f"Chroma distance: {result['distance']:.4f}")
        print(f"Chroma similarity: {result['similarity']:.4f}")
        print(f"Rerank score: {result['rerank_score']:.4f}")
        print("-" * 80)
        print(result["document"][:800].strip())
        print()


if __name__ == "__main__":
    main()