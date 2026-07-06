import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def serialize_product(product: dict) -> str:
    title = product.get("title", "")
    category = product.get("category", "")
    description = product.get("description", "")
    tags = product.get("tags", [])
    brand = product.get("brand", "")

    tags_text = ", ".join(tags) if isinstance(tags, list) else str(tags)

    return (
        f"Title: {title} | "
        f"Category: {category} | "
        f"Description: {description} | "
        f"Tags: {tags_text} | "
        f"Brand: {brand}"
    )


def embed_text(input_text: str | list[str]) -> list[float] | list[list[float]]:
    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY not found. Check your .env file.")

    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/text-embedding-3-small",
            "input": input_text,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Embedding failed: {response.status_code} {response.text}")

    data = response.json()
    embeddings = [item["embedding"] for item in data["data"]]

    if isinstance(input_text, str):
        return embeddings[0]

    return embeddings


def dot_product(vec_a: list[float], vec_b: list[float]) -> float:
    return sum(a * b for a, b in zip(vec_a, vec_b))


def load_database() -> list[dict[str, Any]]:
    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    with open("vectors.tsv", "r", encoding="utf-8") as f:
        lines = f.read().strip().split("\n")

    products_with_embeddings = []

    for product, line in zip(products, lines):
        vector = [float(x) for x in line.split("\t")]
        products_with_embeddings.append({
            **product,
            "embedding": vector,
        })

    return products_with_embeddings


def rerank_results(
    query: str,
    candidates: list[dict],
    top_n: int = 5
) -> list[dict]:
    documents = [serialize_product(product) for product in candidates]

    response = requests.post(
        "https://openrouter.ai/api/v1/rerank",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "cohere/rerank-v3.5",
            "query": query,
            "documents": documents,
            "top_n": top_n,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Reranking failed: {response.status_code} {response.text}")

    data = response.json()

    return [
        {
            **candidates[result["index"]],
            "rerank_score": result["relevance_score"],
        }
        for result in data["results"]
    ]


def search_products(
    query: str,
    products: list[dict],
    min_score: float = 0.30
) -> list[dict]:
    query_vector = embed_text(query)

    scored_products = []

    for product in products:
        vector_score = dot_product(query_vector, product["embedding"])

        if vector_score >= min_score:
            scored_products.append({
                **product,
                "vector_score": vector_score,
            })

    scored_products.sort(key=lambda item: item["vector_score"], reverse=True)

    candidates = scored_products[:20]

    if not candidates:
        return []

    return rerank_results(query, candidates, top_n=5)