import json
import time
from pathlib import Path

import requests


BASE_URL = "https://world.openfoodfacts.org/api/v3"

USER_AGENT = "FMCG-Supply-Chain-Analytics/1.0"


def fetch_product(barcode: str) -> dict:
    """
    Fetch a single product from Open Food Facts API v3.
    """

    url = f"{BASE_URL}/product/{barcode}.json"

    params = {
        "fields": (
            "code,"
            "product_name,"
            "brands,"
            "categories,"
            "categories_tags,"
            "countries,"
            "quantity,"
            "packaging,"
            "ingredients_text,"
            "nutriscore_data,"
            "nutriments"
        )
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_raw_product(data: dict, barcode: str) -> Path:
    """
    Save raw API response as JSON.
    """

    output_dir = Path("data/raw/openfoodfacts")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{barcode}.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    return output_file


def main():

    # Initial API connectivity test product
    barcode = "3017620422003"

    print("Fetching Open Food Facts product...")
    print(f"Barcode: {barcode}")

    data = fetch_product(barcode)

    output_file = save_raw_product(data, barcode)

    print("\nAPI request successful.")
    print(f"Saved raw response to: {output_file}")

    product = data.get("product", {})

    print("\nProduct information:")
    print(f"Name     : {product.get('product_name')}")
    print(f"Brand    : {product.get('brands')}")
    print(f"Category : {product.get('categories')}")
    print(f"Quantity : {product.get('quantity')}")


if __name__ == "__main__":
    main()