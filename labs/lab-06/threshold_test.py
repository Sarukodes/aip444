import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def dot_product(vec_a, vec_b):
    return sum(a * b for a, b in zip(vec_a, vec_b))


def embed_query(query):
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
            "input": query,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Embedding failed: {response.status_code} {response.text}")

    data = response.json()
    return data["data"][0]["embedding"]


def load_database():
    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    with open("vectors.tsv", "r", encoding="utf-8") as f:
        vector_lines = f.read().strip().split("\n")

    products_with_vectors = []

    for product, line in zip(products, vector_lines):
        vector = [float(x) for x in line.split("\t")]
        products_with_vectors.append({
            **product,
            "embedding": vector,
        })

    return products_with_vectors


def print_top_matches(query, products):
    print(f"\nQuery: {query}")

    query_vector = embed_query(query)

    scored_products = []
    for product in products:
        score = dot_product(query_vector, product["embedding"])
        scored_products.append({
            "title": product["title"],
            "category": product["category"],
            "score": score,
        })

    scored_products.sort(key=lambda item: item["score"], reverse=True)

    print("Top 3 matches:")
    for index, item in enumerate(scored_products[:3], start=1):
        print(
            f"{index}. {item['title']} "
            f"({item['category']}) - Score: {item['score']:.4f}"
        )


def main():
    products = load_database()

    print_top_matches("Nice smelling scent", products)
    print_top_matches("A textbook on quantum physics", products)


if __name__ == "__main__":
    main()