import random
from pathlib import Path

import numpy as np
import pandas as pd

from demand_config import (
    CATEGORY_DEMAND,
    REGION_DEMAND,
    STORE_TYPE_DEMAND,
    MONTHLY_SEASONALITY,
    WEEKEND_MULTIPLIER,
    PROMOTION_PROBABILITY,
    PROMOTION_MULTIPLIER,
    DEMAND_NOISE,
)


# =========================================================
# PATHS
# =========================================================

PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("data/raw/operational")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# =========================================================
# PRODUCT POPULARITY
# =========================================================

def assign_product_popularity(products):
    """
    Assign a long-term demand factor to every product.

    Lognormal distribution creates:
    - a few highly popular products
    - many medium-demand products
    - some low-demand products

    This helps create realistic SKU-level demand variation.
    """

    products = products.copy()

    popularity = np.random.lognormal(
        mean=0,
        sigma=0.8,
        size=len(products)
    )

    popularity = popularity / popularity.mean()

    products["demand_factor"] = popularity

    return products


# =========================================================
# STORE DEMAND PROFILE
# =========================================================

def assign_store_demand(stores):
    """
    Assign demand multiplier based on store type.
    """

    stores = stores.copy()

    stores["store_demand_factor"] = (
        stores["store_type"]
        .map(STORE_TYPE_DEMAND)
        .fillna(1.0)
    )

    return stores


# =========================================================
# PRODUCT BASE DEMAND
# =========================================================

def calculate_base_demand(product):
    """
    Calculate the base daily demand for a product.
    """

    category = product["category"]

    product_factor = product["demand_factor"]

    category_factor = CATEGORY_DEMAND.get(
        category,
        1.0
    )

    base = (
        20
        * product_factor
        * category_factor
    )

    return max(
        1,
        base
    )


# =========================================================
# DAILY DEMAND
# =========================================================

def calculate_daily_demand(
    product,
    store,
    date
):
    """
    Calculate daily demand for a product at a store.
    """

    base_demand = calculate_base_demand(
        product
    )

    store_factor = store[
        "store_demand_factor"
    ]

    region_factor = REGION_DEMAND.get(
        store["region"],
        1.0
    )

    month_factor = MONTHLY_SEASONALITY.get(
        date.month,
        1.0
    )

    weekend_factor = (
        WEEKEND_MULTIPLIER
        if date.dayofweek >= 5
        else 1.0
    )

    # Product-specific demand volatility
    noise_factor = np.random.normal(
        loc=1.0,
        scale=DEMAND_NOISE.get(
            product["category"],
            0.15
        )
    )

    # Prevent unrealistic negative/very-low demand
    noise_factor = max(
        0.40,
        noise_factor
    )

    # Promotion
    is_promotion = (
        random.random()
        < PROMOTION_PROBABILITY
    )

    promotion_factor = (
        PROMOTION_MULTIPLIER
        if is_promotion
        else 1.0
    )

    demand = (
        base_demand
        * store_factor
        * region_factor
        * month_factor
        * weekend_factor
        * noise_factor
        * promotion_factor
    )

    return (
        max(
            0,
            int(round(demand))
        ),
        is_promotion
    )


# =========================================================
# GENERATE SALES
# =========================================================

def generate_sales():

    print(
        "Loading master data..."
    )

    # -----------------------------------------------------
    # Load master data
    # -----------------------------------------------------

    products_file = (
        PROCESSED_DIR /
        "dim_product.csv"
    )

    stores_file = (
        PROCESSED_DIR /
        "dim_store.csv"
    )

    dates_file = (
        PROCESSED_DIR /
        "dim_date.csv"
    )

    # -----------------------------------------------------
    # Validate required files
    # -----------------------------------------------------

    required_files = [
        products_file,
        stores_file,
        dates_file
    ]

    for file_path in required_files:

        if not file_path.exists():

            raise FileNotFoundError(
                f"\nRequired file not found:\n"
                f"{file_path.resolve()}\n\n"
                f"Please generate the required "
                f"master data before running sales generation."
            )

    # -----------------------------------------------------
    # Read master data
    # -----------------------------------------------------

    products = pd.read_csv(
        products_file
    )

    stores = pd.read_csv(
        stores_file
    )

    dates = pd.read_csv(
        dates_file
    )

    # -----------------------------------------------------
    # Validate columns
    # -----------------------------------------------------

    required_product_columns = [
        "product_id",
        "category",
        "selling_price"
    ]

    required_store_columns = [
        "store_id",
        "store_type",
        "region"
    ]

    required_date_columns = [
        "date"
    ]

    missing_product_columns = [
        col
        for col in required_product_columns
        if col not in products.columns
    ]

    missing_store_columns = [
        col
        for col in required_store_columns
        if col not in stores.columns
    ]

    missing_date_columns = [
        col
        for col in required_date_columns
        if col not in dates.columns
    ]

    if missing_product_columns:

        raise ValueError(
            "Missing columns in dim_product.csv: "
            + ", ".join(missing_product_columns)
        )

    if missing_store_columns:

        raise ValueError(
            "Missing columns in dim_store.csv: "
            + ", ".join(missing_store_columns)
        )

    if missing_date_columns:

        raise ValueError(
            "Missing columns in dim_date.csv: "
            + ", ".join(missing_date_columns)
        )

    # -----------------------------------------------------
    # Convert dates
    # -----------------------------------------------------

    dates["date"] = pd.to_datetime(
        dates["date"]
    )

    # -----------------------------------------------------
    # Remove invalid products
    # -----------------------------------------------------

    products = products.dropna(
        subset=[
            "product_id",
            "category",
            "selling_price"
        ]
    )

    products = products[
        products["selling_price"] > 0
    ].reset_index(
        drop=True
    )

    # -----------------------------------------------------
    # Remove invalid stores
    # -----------------------------------------------------

    stores = stores.dropna(
        subset=[
            "store_id",
            "store_type",
            "region"
        ]
    ).reset_index(
        drop=True
    )

    # -----------------------------------------------------
    # Assign demand characteristics
    # -----------------------------------------------------

    products = assign_product_popularity(
        products
    )

    stores = assign_store_demand(
        stores
    )

    # -----------------------------------------------------
    # Print master-data summary
    # -----------------------------------------------------

    print(
        f"Products : {len(products):,}"
    )

    print(
        f"Stores   : {len(stores):,}"
    )

    print(
        f"Dates    : {len(dates):,}"
    )

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------

    if len(products) == 0:

        raise ValueError(
            "No valid products available "
            "in dim_product.csv."
        )

    if len(stores) == 0:

        raise ValueError(
            "No valid stores available "
            "in dim_store.csv."
        )

    if len(dates) == 0:

        raise ValueError(
            "No dates available "
            "in dim_date.csv."
        )

    records = []

    sale_id = 1

    # =====================================================
    # GENERATE TRANSACTIONS
    # =====================================================

    for date in dates["date"]:

        # -------------------------------------------------
        # Iterate over stores as dictionaries
        #
        # IMPORTANT:
        # to_dict("records") prevents the previous error:
        #
        # TypeError:
        # tuple indices must be integers or slices, not str
        # -------------------------------------------------

        for store in stores.to_dict(
            orient="records"
        ):

            # -------------------------------------------------
            # Select a random subset of products
            # -------------------------------------------------

            min_products = max(
                1,
                int(len(products) * 0.15)
            )

            max_products = max(
                min_products,
                int(len(products) * 0.35)
            )

            # Prevent n from exceeding number of products
            max_products = min(
                max_products,
                len(products)
            )

            number_of_products = random.randint(
                min_products,
                max_products
            )

            selected_products = products.sample(
                n=number_of_products,
                replace=False
            )

            # -------------------------------------------------
            # Generate sales for selected products
            # -------------------------------------------------

            for _, product in selected_products.iterrows():

                quantity, is_promotion = (
                    calculate_daily_demand(
                        product,
                        store,
                        date
                    )
                )

                if quantity <= 0:
                    continue

                # -------------------------------------------------
                # Price
                # -------------------------------------------------

                unit_price = float(
                    product["selling_price"]
                )

                # -------------------------------------------------
                # Discount
                # -------------------------------------------------

                discount = (
                    random.uniform(
                        0.05,
                        0.20
                    )
                    if is_promotion
                    else random.uniform(
                        0.00,
                        0.05
                    )
                )

                # -------------------------------------------------
                # Revenue
                # -------------------------------------------------

                sales_amount = (
                    quantity
                    * unit_price
                    * (1 - discount)
                )

                # -------------------------------------------------
                # Transaction record
                # -------------------------------------------------

                records.append(
                    {
                        "sale_id": (
                            f"S{sale_id:09d}"
                        ),

                        "date_id": int(
                            date.strftime(
                                "%Y%m%d"
                            )
                        ),

                        "date": date,

                        "product_id": product[
                            "product_id"
                        ],

                        "store_id": store[
                            "store_id"
                        ],

                        "quantity_sold": quantity,

                        "unit_price": round(
                            unit_price,
                            2
                        ),

                        "discount": round(
                            discount,
                            4
                        ),

                        "sales_amount": round(
                            sales_amount,
                            2
                        ),

                        "promotion_flag": int(
                            is_promotion
                        ),
                    }
                )

                sale_id += 1

    # -----------------------------------------------------
    # Convert records to DataFrame
    # -----------------------------------------------------

    return pd.DataFrame(
        records
    )


# =========================================================
# VALIDATION
# =========================================================

def validate_sales(df):

    print(
        "\nValidating sales..."
    )

    # -----------------------------------------------------
    # Handle empty dataset
    # -----------------------------------------------------

    if df.empty:

        raise ValueError(
            "Sales generation produced "
            "zero transactions."
        )

    # -----------------------------------------------------
    # Positive quantities
    # -----------------------------------------------------

    df = df[
        df["quantity_sold"] > 0
    ]

    # -----------------------------------------------------
    # Positive prices
    # -----------------------------------------------------

    df = df[
        df["unit_price"] > 0
    ]

    # -----------------------------------------------------
    # Positive revenue
    # -----------------------------------------------------

    df = df[
        df["sales_amount"] > 0
    ]

    # -----------------------------------------------------
    # Remove duplicate transactions
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "sale_id"
        ]
    )

    # -----------------------------------------------------
    # Reset index
    # -----------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    return df


# =========================================================
# SAVE
# =========================================================

def save_sales(df):

    output_file = (
        OUTPUT_DIR /
        "fact_sales.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved sales data:"
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
        "FMCG SALES / DEMAND ENGINE"
    )

    print(
        "=" * 60
    )

    # -----------------------------------------------------
    # Generate
    # -----------------------------------------------------

    df = generate_sales()

    print(
        f"\nGenerated transactions:"
        f" {len(df):,}"
    )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    df = validate_sales(
        df
    )

    print(
        f"Valid transactions:"
        f" {len(df):,}"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_sales(
        df
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print(
        "\nSales summary:"
    )

    print(
        f"Revenue: "
        f"₹{df['sales_amount'].sum():,.2f}"
    )

    print(
        f"Units: "
        f"{df['quantity_sold'].sum():,}"
    )

    print(
        f"Products: "
        f"{df['product_id'].nunique():,}"
    )

    print(
        f"Stores: "
        f"{df['store_id'].nunique():,}"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()