from utils import load_database, search_products


def display_results(results):
    if not results:
        print("\nI'm sorry, we don't have anything like that in stock.\n")
        return

    print(f"\nFound {len(results)} matches:")

    for index, product in enumerate(results, start=1):
        title = product.get("title", "Unknown product")
        price = product.get("price", "N/A")
        rerank_score = product.get("rerank_score", 0)
        vector_score = product.get("vector_score", 0)

        print(
            f"{index}. [Rerank: {rerank_score:.4f} | "
            f"Vector: {vector_score:.4f}] "
            f"{title} - ${price}"
        )

    print()


def main():
    print("Loading product database...")
    products = load_database()
    print(f"Loaded {len(products)} products.")
    print("Type 'quit' to exit.\n")

    while True:
        query = input("What are you looking for? ")

        if query.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        results = search_products(query, products)
        display_results(results)


if __name__ == "__main__":
    main()