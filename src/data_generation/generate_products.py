import json
import random
import re
from pathlib import Path

import pandas as pd


# =========================================================
# PATHS
# =========================================================

RAW_DIR = Path(
    "data/raw/openfoodfacts"
)

OUTPUT_DIR = Path(
    "data/processed"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# RANDOM SEED
# =========================================================

SEED = 42

random.seed(
    SEED
)


# =========================================================
# FMCG BUSINESS MAPPINGS
# =========================================================

CATEGORY_MAPPING = {

    "beverages":
        "Food & Beverages",

    "drinks":
        "Food & Beverages",

    "juices":
        "Food & Beverages",

    "juice":
        "Food & Beverages",

    "water":
        "Food & Beverages",

    "tea":
        "Food & Beverages",

    "coffee":
        "Food & Beverages",

    "snacks":
        "Packaged Foods",

    "biscuits":
        "Packaged Foods",

    "cookies":
        "Packaged Foods",

    "chocolates":
        "Packaged Foods",

    "chocolate":
        "Packaged Foods",

    "cereals":
        "Packaged Foods",

    "breakfast cereals":
        "Packaged Foods",

    "sauces":
        "Packaged Foods",

    "sauce":
        "Packaged Foods",

    "pasta":
        "Packaged Foods",

    "noodles":
        "Packaged Foods",

    "chips":
        "Packaged Foods",

    "shampoo":
        "Personal Care",

    "hair care":
        "Personal Care",

    "skin care":
        "Personal Care",

    "soap":
        "Personal Care",

    "toothpaste":
        "Personal Care",

    "deodorants":
        "Personal Care",

    "deodorant":
        "Personal Care",

    "detergents":
        "Household Care",

    "detergent":
        "Household Care",

    "cleaning products":
        "Household Care",

    "dishwashing":
        "Household Care",

    "dishwasher":
        "Household Care",

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


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(
    value
):

    if value is None:

        return None

    value = str(
        value
    ).strip()

    if not value:

        return None

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


# =========================================================
# CATEGORY
# =========================================================

def determine_category(
    raw_category
):

    if not raw_category:

        return random.choice(
            DEFAULT_CATEGORIES
        )

    category_text = (
        raw_category
        .lower()
    )

    for keyword, category in (
        CATEGORY_MAPPING.items()
    ):

        if keyword in category_text:

            return category

    return random.choice(
        DEFAULT_CATEGORIES
    )


# =========================================================
# UNIT SIZE PARSER
# =========================================================

def parse_quantity(
    quantity
):

    """
    Convert strings such as:

        400 g
        1 kg
        500 ml
        1 L
        12 pieces

    into:

        numeric unit_size
        unit_of_measure
    """

    if not quantity:

        return (
            None,
            "unit"
        )

    text = str(
        quantity
    ).strip().lower()

    # -----------------------------------------------------
    # Find numeric value
    # -----------------------------------------------------

    match = re.search(
        r"(\d+(?:[.,]\d+)?)",
        text
    )

    if not match:

        return (
            None,
            "unit"
        )

    try:

        value = float(
            match.group(1)
            .replace(",", ".")
        )

    except ValueError:

        return (
            None,
            "unit"
        )

    # -----------------------------------------------------
    # Determine measurement
    # -----------------------------------------------------

    if re.search(
        r"\bkg\b",
        text
    ):

        unit = "kg"

    elif re.search(
        r"\bmg\b",
        text
    ):

        unit = "mg"

    elif re.search(
        r"\bg\b",
        text
    ):

        unit = "g"

    elif re.search(
        r"\bl\b",
        text
    ):

        unit = "L"

    elif re.search(
        r"\bml\b",
        text
    ):

        unit = "ml"

    elif re.search(
        r"\bcl\b",
        text
    ):

        unit = "cl"

    elif re.search(
        r"\bpcs\b|\bpieces?\b|\bunit\b",
        text
    ):

        unit = "unit"

    else:

        unit = "unit"

    return (
        round(value, 2),
        unit
    )


# =========================================================
# BUSINESS ATTRIBUTES
# =========================================================

def generate_product_attributes(
    category
):

    subcategory = random.choice(
        SUBCATEGORIES[
            category
        ]
    )

    if category == "Food & Beverages":

        shelf_life = random.randint(
            90,
            540
        )

    elif category == "Packaged Foods":

        shelf_life = random.randint(
            120,
            720
        )

    elif category == "Personal Care":

        shelf_life = random.randint(
            365,
            1095
        )

    else:

        shelf_life = random.randint(
            365,
            1095
        )

    unit_cost = round(
        random.uniform(
            20,
            400
        ),
        2
    )

    selling_price = round(
        unit_cost
        *
        random.uniform(
            1.15,
            1.60
        ),
        2
    )

    return (
        subcategory,
        shelf_life,
        unit_cost,
        selling_price
    )


# =========================================================
# EXTRACT PRODUCTS
# =========================================================

def extract_products():

    records = []

    json_files = sorted(
        RAW_DIR.glob(
            "*.json"
        )
    )

    print(
        f"Found {len(json_files):,} "
        f"Open Food Facts files."
    )

    for file in json_files:

        try:

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(
                    f
                )

            product = data.get(
                "product",
                {}
            )

            barcode = (
                product.get(
                    "code"
                )
                or file.stem
            )

            barcode = str(
                barcode
            ).strip()

            product_name = normalize_text(
                product.get(
                    "product_name"
                )
            )

            if not product_name:

                continue

            brands = normalize_text(
                product.get(
                    "brands"
                )
            )

            categories = normalize_text(
                product.get(
                    "categories"
                )
            )

            quantity = normalize_text(
                product.get(
                    "quantity"
                )
            )

            countries = normalize_text(
                product.get(
                    "countries"
                )
            )

            packaging = normalize_text(
                product.get(
                    "packaging"
                )
            )

            # -------------------------------------------------
            # Business category
            # -------------------------------------------------

            category = determine_category(
                categories
            )

            # -------------------------------------------------
            # Synthetic business attributes
            # -------------------------------------------------

            (
                subcategory,
                shelf_life,
                unit_cost,
                selling_price,
            ) = generate_product_attributes(
                category
            )

            # -------------------------------------------------
            # Parse quantity
            # -------------------------------------------------

            (
                unit_size,
                unit_of_measure
            ) = parse_quantity(
                quantity
            )

            # -------------------------------------------------
            # Product record
            # -------------------------------------------------

            records.append(
                {

                    "product_id":
                        f"P{barcode}",

                    "barcode":
                        barcode,

                    "product_name":
                        product_name,

                    "brand":
                        brands
                        or
                        "Unknown",

                    "category":
                        category,

                    "subcategory":
                        subcategory,

                    "unit_size":
                        unit_size,

                    "unit_of_measure":
                        unit_of_measure,

                    "countries":
                        countries
                        or
                        "Unknown",

                    "packaging":
                        packaging
                        or
                        "Unknown",

                    "shelf_life_days":
                        shelf_life,

                    "unit_cost":
                        unit_cost,

                    "selling_price":
                        selling_price,

                }
            )

        except Exception as e:

            print(
                f"Error processing "
                f"{file.name}: {e}"
            )

    return pd.DataFrame(
        records
    )


# =========================================================
# VALIDATION
# =========================================================

def validate_products(
    df
):

    print(
        "\nRunning product validation..."
    )

    if df.empty:

        return df

    # -----------------------------------------------------
    # Duplicate barcodes
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "barcode"
        ]
    )

    # -----------------------------------------------------
    # Product name
    # -----------------------------------------------------

    df = df[
        df[
            "product_name"
        ].notna()
    ]

    # -----------------------------------------------------
    # Prices
    # -----------------------------------------------------

    df = df[
        (
            df[
                "unit_cost"
            ] > 0
        )
        &
        (
            df[
                "selling_price"
            ] > 0
        )
    ]

    # -----------------------------------------------------
    # Selling price > cost
    # -----------------------------------------------------

    df = df[
        df[
            "selling_price"
        ]
        >
        df[
            "unit_cost"
        ]
    ]

    # -----------------------------------------------------
    # Numeric unit size
    # -----------------------------------------------------

    df[
        "unit_size"
    ] = pd.to_numeric(
        df[
            "unit_size"
        ],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Reset index
    # -----------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    print(
        f"Valid products: "
        f"{len(df):,}"
    )

    return df


# =========================================================
# SAVE
# =========================================================

def save_products(
    df
):

    output_file = (
        OUTPUT_DIR
        /
        "dim_product.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved product master to:"
        f"\n{output_file.resolve()}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "=" * 60
    )

    print(
        "FMCG PRODUCT MASTER GENERATION"
    )

    print(
        "=" * 60
    )

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

    df = validate_products(
        df
    )

    save_products(
        df
    )

    print(
        "\nCategory distribution:"
    )

    print(
        df[
            "category"
        ].value_counts()
    )

    print(
        "\nSample products:"
    )

    print(
        df[
            [
                "product_id",
                "product_name",
                "brand",
                "category",
                "subcategory",
                "unit_size",
                "unit_of_measure",
                "unit_cost",
                "selling_price",
            ]
        ].head(10).to_string(
            index=False
        )
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()