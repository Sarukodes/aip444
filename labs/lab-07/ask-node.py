
import os
import sys
from pathlib import Path
from html import escape

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
CHAT_MODEL = os.getenv("CHAT_MODEL", "google/gemini-3.1-flash-lite-preview")

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
        candidate["rerank_score"] = item.get("relevance_score", 0)
        reranked.append(candidate)

    return reranked


def build_system_prompt(chunks):
    docs_xml = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        source = escape(str(metadata.get("source", "unknown")))
        breadcrumb = escape(str(metadata.get("breadcrumb", "unknown")))
        content = chunk["document"]

        docs_xml.append(
            f'<doc source="{source}" breadcrumb="{breadcrumb}">\n'
            f'{content}\n'
            f'</doc>'
        )

    context = "\n\n".join(docs_xml)

    return f"""
You are ask-node, an expert Node.js assistant that answers questions about Node.js.

Here is context from the official Node.js documentation:

<context>
{context}
</context>

Instructions:
1. Answer the user's question based ONLY on the provided context.
2. Do not use outside knowledge.
3. If the answer is not clearly available in the context, say exactly: "I don't have enough information to answer that."
4. Cite the source file names you used, such as fs.md, path.md, or crypto.md.
5. Be clear and practical. Include code examples only when the provided context supports them.
""".strip()


def generate_answer(question, chunks):
    system_prompt = build_system_prompt(chunks)

    response = openrouter.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    return response.choices[0].message.content


def main():
    if len(sys.argv) < 2:
        print('Usage: python ask-node.py "How do I read a file?"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    candidates = query_chroma(question, n_results=25)
    top_chunks = rerank(question, candidates, top_n=5)

    print("\nRetrieved sources:", file=sys.stderr)

    for chunk in top_chunks:
        metadata = chunk["metadata"]
        print(
            f"- {metadata.get('source')} | {metadata.get('breadcrumb')} "
            f"| Chroma rank {chunk['chroma_rank']} "
            f"| distance {chunk['distance']:.4f} "
            f"| rerank {chunk['rerank_score']:.4f}",
            file=sys.stderr,
        )

    print(file=sys.stderr)

    answer = generate_answer(question, top_chunks)
    print(answer)


if __name__ == "__main__":
    main()