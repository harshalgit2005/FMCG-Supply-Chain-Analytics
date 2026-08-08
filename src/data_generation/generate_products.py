import json
import random
import re
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw/openfoodfacts")
OUTPUT_DIR = Path("data/processed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# FMCG business mappings
# ---------------------------------------------------------

CATEGORY_MAPPING = {
    "beverages": "Food & Beverages",
    "snacks": "Packaged Foods",
    "biscuits": "Packaged Foods",
    "cookies": "Packaged Foods",
    "chocolates": "Packaged Foods",
    "cereals": "Packaged Foods",
    "breakfast cereals": "Packaged Foods",
    "sauces": "Packaged Foods",
    "pasta": "Packaged Foods",

    "shampoo": "Personal Care",
    "hair care": "Personal Care",
    "skin care": "Personal Care",
    "soap": "Personal Care",
    "toothpaste": "Personal Care",
    "deodorants": "Personal Care",

    "detergents": "Household Care",
    "cleaning products": "Household Care",
    "dishwashing": "Household Care",
}


DEFAULT_CATEGORIES = [
    "Packaged Foods",
    "Food & Beverages",
    "Personal Care",
    "Household Care",
]


SUBCATEGORIES = {
    "Food & Beverages": [
        "Soft Drinks",
        "Juices",
        "Water",
        "Tea",
        "Coffee",
    ],
    "Packaged Foods": [
        "Biscuits",
        "Snacks",
        "Breakfast Cereals",
        "Chocolate",
        "Pasta",
        "Sauces",
    ],
    "Personal Care": [
        "Shampoo",
        "Soap",
        "Toothpaste",
        "Skin Care",
        "Deodorant",
    ],
    "Household Care": [
        "Detergent",
        "Dishwashing",
        "Surface Cleaner",
        "Laundry Care",
    ],
}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def normalize_text(value):
    if not value:
        return None

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    return value


def determine_category(raw_category):
    """
    Map Open Food Facts category information
    into our FMCG business categories.
    """

    if not raw_category:
        return random.choice(DEFAULT_CATEGORIES)

    category_text = raw_category.lower()

    for keyword, category in CATEGORY_MAPPING.items():

        if keyword in category_text:
            return category

    return random.choice(DEFAULT_CATEGORIES)


def generate_product_attributes(category):

    subcategory = random.choice(
        SUBCATEGORIES[category]
    )

    if category == "Food & Beverages":
        shelf_life = random.randint(90, 540)

    elif category == "Packaged Foods":
        shelf_life = random.randint(120, 720)

    elif category == "Personal Care":
        shelf_life = random.randint(365, 1095)

    else:
        shelf_life = random.randint(365, 1095)

    unit_cost = round(
        random.uniform(20, 400),
        2
    )

    selling_price = round(
        unit_cost * random.uniform(1.15, 1.60),
        2
    )

    return (
        subcategory,
        shelf_life,
        unit_cost,
        selling_price,
    )


# ---------------------------------------------------------
# Main extraction
# ---------------------------------------------------------

def extract_products():

    records = []

    json_files = list(
        RAW_DIR.glob("*.json")
    )

    print(
        f"Found {len(json_files)} "
        f"Open Food Facts files."
    )

    for file in json_files:

        try:

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            product = data.get(
                "product",
                {}
            )

            barcode = (
                product.get("code")
                or file.stem
            )

            product_name = normalize_text(
                product.get(
                    "product_name"
                )
            )

            if not product_name:
                continue

            brands = normalize_text(
                product.get("brands")
            )

            categories = normalize_text(
                product.get("categories")
            )

            quantity = normalize_text(
                product.get("quantity")
            )

            countries = normalize_text(
                product.get("countries")
            )

            packaging = normalize_text(
                product.get("packaging")
            )

            category = determine_category(
                categories
            )

            (
                subcategory,
                shelf_life,
                unit_cost,
                selling_price,
            ) = generate_product_attributes(
                category
            )

            records.append(
                {
                    "product_id": f"P{barcode}",
                    "barcode": barcode,
                    "product_name": product_name,
                    "brand": brands or "Unknown",
                    "category": category,
                    "subcategory": subcategory,
                    "unit_size": quantity or "Unknown",
                    "unit_of_measure": "unit",
                    "countries": countries or "Unknown",
                    "packaging": packaging or "Unknown",
                    "shelf_life_days": shelf_life,
                    "unit_cost": unit_cost,
                    "selling_price": selling_price,
                }
            )

        except Exception as e:

            print(
                f"Error processing {file}: {e}"
            )

    return pd.DataFrame(records)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_products(df):

    print("\nRunning product validation...")

    # Remove duplicate barcodes
    df = df.drop_duplicates(
        subset=["barcode"]
    )

    # Remove missing names
    df = df[
        df["product_name"].notna()
    ]

    # Ensure valid prices
    df = df[
        (df["unit_cost"] > 0)
        &
        (df["selling_price"] > 0)
    ]

    # Ensure selling price > cost
    df = df[
        df["selling_price"]
        >
        df["unit_cost"]
    ]

    df = df.reset_index(
        drop=True
    )

    print(
        f"Valid products: {len(df):,}"
    )

    return df


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_products(df):

    output_file = (
        OUTPUT_DIR /
        "dim_product.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nSaved product master to:"
        f"\n{output_file}"
    )


def main():

    print("=" * 60)
    print("FMCG PRODUCT MASTER GENERATION")
    print("=" * 60)

    df = extract_products()

    if df.empty:

        print(
            "\nNo products found."
        )

        print(
            "Run the Open Food Facts "
            "ingestion script first."
        )

        return

    df = validate_products(df)

    save_products(df)

    print("\nCategory distribution:")
    print(
        df["category"]
        .value_counts()
    )

    print("\nSample products:")
    print(
        df[
            [
                "product_id",
                "product_name",
                "brand",
                "category",
                "subcategory",
                "unit_cost",
                "selling_price",
            ]
        ].head(10)
    )


if __name__ == "__main__":
    main()