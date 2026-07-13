# indexer.py
import os
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from chunker import chunk_markdown

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]

load_dotenv(BASE_DIR / ".env")
load_dotenv(REPO_ROOT / ".env", override=False)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")

if not OPENROUTER_API_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY")

openrouter = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

chroma_client = chromadb.PersistentClient(path=str(BASE_DIR / "chroma_db"))


def embed_texts(texts, batch_size=32):
    all_embeddings = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        for attempt in range(5):
            try:
                response = openrouter.embeddings.create(
                    model=EMBED_MODEL,
                    input=batch,
                )

                sorted_items = sorted(response.data, key=lambda item: item.index)
                all_embeddings.extend([item.embedding for item in sorted_items])
                print(f"Embedded {start + len(batch)} / {len(texts)} chunks")
                break

            except Exception as error:
                wait = 2 ** attempt
                print(f"Embedding error: {error}")
                print(f"Retrying in {wait} seconds...")
                time.sleep(wait)
        else:
            raise RuntimeError("Failed to embed batch after multiple retries")

    return all_embeddings


def main():
    collection = chroma_client.get_or_create_collection(
        name="node-docs",
        metadata={"hnsw:space": "cosine"},
    )

    docs_dir = BASE_DIR / "docs"
    files = sorted(docs_dir.glob("*.md"))

    if not files:
        raise RuntimeError("No Markdown files found in docs folder")

    total_chunks = 0

    for filepath in files:
        filename = filepath.name
        print(f"\nProcessing {filename}...")

        text = filepath.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, filename)

        if not chunks:
            print(f"No chunks created for {filename}")
            continue

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        embeddings = embed_texts(documents)

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        total_chunks += len(chunks)
        print(f"Stored {len(chunks)} chunks from {filename}")

    print("\nIndexing complete!")
    print(f"Total chunks stored: {total_chunks}")


if __name__ == "__main__":
    main()
