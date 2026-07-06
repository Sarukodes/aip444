import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from utils import serialize_product


# Load .env from the main aip444 folder
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def fetch_products():
    url = "https://dummyjson.com/products?limit=200"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch products: {response.status_code} {response.text}")

    data = response.json()
    return data["products"]


def create_embeddings(texts):
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
            "input": texts,
        },
    )

    if response.status_code != 200:
        raise Exception(f"Embedding failed: {response.status_code} {response.text}")

    data = response.json()
    return [item["embedding"] for item in data["data"]]


def clean_tsv_value(value):
    return str(value).replace("\t", " ").replace("\n", " ").strip()


def main():
    print("Fetching products...")
    products = fetch_products()
    print(f"Fetched {len(products)} products.")

    print("Saving products.json...")
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2)

    print("Serializing products...")
    serialized_products = [serialize_product(product) for product in products]

    print("Creating embeddings...")
    embeddings = create_embeddings(serialized_products)
    print(f"Created {len(embeddings)} embeddings.")

    print("Saving vectors.tsv...")
    with open("vectors.tsv", "w", encoding="utf-8") as f:
        lines = ["\t".join(str(num) for num in vector) for vector in embeddings]
        f.write("\n".join(lines))

    print("Saving metadata.tsv...")
    with open("metadata.tsv", "w", encoding="utf-8") as f:
        f.write("Title\tCategory\n")

        for product in products:
            title = clean_tsv_value(product.get("title", ""))
            category = clean_tsv_value(product.get("category", ""))
            f.write(f"{title}\t{category}\n")

    print("Done! Created products.json, vectors.tsv, and metadata.tsv.")


if __name__ == "__main__":
    main()