import json
import time
from pathlib import Path

import requests


# =========================================================
# CONFIGURATION
# =========================================================

BASE_URL = "https://world.openfoodfacts.org/api/v2"

USER_AGENT = (
    "FMCG-Supply-Chain-Analytics/1.0 "
    "(educational-project)"
)

OUTPUT_DIR = Path(
    "data/raw/openfoodfacts"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# Number of products to retrieve
TARGET_PRODUCTS = 500

# Products per API request
PAGE_SIZE = 100

# Delay between requests
REQUEST_DELAY = 1.0


# =========================================================
# HEADERS
# =========================================================

HEADERS = {
    "User-Agent": USER_AGENT
}


# =========================================================
# SEARCH PRODUCTS
# =========================================================

def fetch_products(
    page=1,
    page_size=100
):
    """
    Fetch a page of products from Open Food Facts.
    """

    url = (
        f"{BASE_URL}/search"
    )

    params = {
        "page": page,
        "page_size": page_size,

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
        ),

        "json": 1
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# SAVE PRODUCT
# =========================================================

def save_product(
    product
):

    barcode = str(
        product.get("code", "")
    ).strip()

    if not barcode:
        return False

    output_file = (
        OUTPUT_DIR
        / f"{barcode}.json"
    )

    # Don't overwrite existing products
    if output_file.exists():
        return False

    data = {
        "product": product
    }

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

    return True


# =========================================================
# DOWNLOAD CATALOG
# =========================================================

def download_catalog(
    target_products=TARGET_PRODUCTS
):

    print(
        "\nDownloading Open Food Facts "
        "product catalog..."
    )

    print(
        f"Target products: "
        f"{target_products:,}"
    )

    saved_products = 0
    page = 1

    while saved_products < target_products:

        print(
            f"\nRequesting page {page}..."
        )

        try:

            data = fetch_products(
                page=page,
                page_size=PAGE_SIZE
            )

        except requests.RequestException as e:

            print(
                f"API request failed: {e}"
            )

            break

        products = data.get(
            "products",
            []
        )

        if not products:

            print(
                "No more products returned."
            )

            break

        page_saved = 0

        for product in products:

            if saved_products >= target_products:
                break

            saved = save_product(
                product
            )

            if saved:

                saved_products += 1
                page_saved += 1

        print(
            f"Products returned : "
            f"{len(products):,}"
        )

        print(
            f"New products saved: "
            f"{page_saved:,}"
        )

        print(
            f"Total saved       : "
            f"{saved_products:,}"
        )

        page += 1

        time.sleep(
            REQUEST_DELAY
        )

    print(
        "\nOpen Food Facts ingestion complete."
    )

    print(
        f"Total products saved: "
        f"{saved_products:,}"
    )

    return saved_products


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 60
    )

    print(
        "OPEN FOOD FACTS INGESTION"
    )

    print(
        "=" * 60
    )

    download_catalog()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()