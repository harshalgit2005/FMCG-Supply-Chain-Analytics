import random
from pathlib import Path

import numpy as np
import pandas as pd


PROCESSED_DIR = Path("data/processed")
OPERATIONAL_DIR = Path("data/raw/operational")

OPERATIONAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INITIAL_STOCK_DAYS = 15

DAMAGE_RATE = 0.002

EXPIRY_RATE = 0.001

RECEIPT_PROBABILITY = 0.08


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_data():

    sales = pd.read_csv(
        OPERATIONAL_DIR /
        "fact_sales.csv"
    )

    products = pd.read_csv(
        PROCESSED_DIR /
        "dim_product.csv"
    )

    warehouses = pd.read_csv(
        PROCESSED_DIR /
        "dim_warehouse.csv"
    )

    stores = pd.read_csv(
        PROCESSED_DIR /
        "dim_store.csv"
    )

    mapping = pd.read_csv(
        PROCESSED_DIR /
        "store_warehouse_mapping.csv"
    )

    sales["date"] = pd.to_datetime(
        sales["date"]
    )

    return (
        sales,
        products,
        warehouses,
        stores,
        mapping,
    )


# ---------------------------------------------------------
# Aggregate sales to warehouse level
# ---------------------------------------------------------

def aggregate_demand(
    sales,
    mapping
):

    sales = sales.merge(
        mapping,
        on="store_id",
        how="left"
    )

    warehouse_demand = (
        sales
        .groupby(
            [
                "date",
                "product_id",
                "warehouse_id",
            ],
            as_index=False
        )
        ["quantity_sold"]
        .sum()
    )

    warehouse_demand = (
        warehouse_demand
        .rename(
            columns={
                "quantity_sold":
                "demand_units"
            }
        )
    )

    return warehouse_demand


# ---------------------------------------------------------
# Create product warehouse combinations
# ---------------------------------------------------------

def create_inventory_universe(
    products,
    warehouses
):

    records = []

    for product in products.itertuples(
        index=False
    ):

        for warehouse in warehouses.itertuples(
            index=False
        ):

            records.append(
                {
                    "product_id":
                        product.product_id,

                    "warehouse_id":
                        warehouse.warehouse_id,
                }
            )

    return pd.DataFrame(records)


# ---------------------------------------------------------
# Generate inventory
# ---------------------------------------------------------

def generate_inventory():

    (
        sales,
        products,
        warehouses,
        stores,
        mapping,
    ) = load_data()

    demand = aggregate_demand(
        sales,
        mapping
    )

    universe = create_inventory_universe(
        products,
        warehouses
    )

    dates = pd.date_range(
        sales["date"].min(),
        sales["date"].max(),
        freq="D"
    )

    # -----------------------------------------------------
    # Demand lookup
    # -----------------------------------------------------

    demand_lookup = {
        (
            row.date,
            row.product_id,
            row.warehouse_id,
        ): row.demand_units

        for row in demand.itertuples(
            index=False
        )
    }

    # -----------------------------------------------------
    # Initial stock
    # -----------------------------------------------------

    current_stock = {}

    for row in universe.itertuples(
        index=False
    ):

        product = products[
            products["product_id"]
            == row.product_id
        ].iloc[0]

        # Estimate a starting daily demand.
        #
        # We use a conservative baseline
        # because inventory replenishment
        # will be generated later.

        estimated_daily_demand = 20

        initial_stock = int(
            estimated_daily_demand
            * INITIAL_STOCK_DAYS
            * random.uniform(
                0.7,
                1.5
            )
        )

        current_stock[
            (
                row.product_id,
                row.warehouse_id
            )
        ] = max(
            initial_stock,
            10
        )

    # -----------------------------------------------------
    # Generate daily inventory
    # -----------------------------------------------------

    records = []

    inventory_id = 1

    for date in dates:

        for row in universe.itertuples(
            index=False
        ):

            key = (
                row.product_id,
                row.warehouse_id
            )

            opening_stock = current_stock[key]

            # -------------------------------------------------
            # Receipts
            # -------------------------------------------------
            #
            # At this stage we don't yet have purchase orders.
            # We therefore allow occasional replenishment.
            #
            # In the next phase this will be replaced by
            # purchase-order-driven receipts.

            received_units = 0

            if (
                random.random()
                < RECEIPT_PROBABILITY
            ):

                received_units = random.randint(
                    100,
                    1000
                )

            # -------------------------------------------------
            # Demand
            # -------------------------------------------------

            demand_units = demand_lookup.get(
                (
                    date,
                    row.product_id,
                    row.warehouse_id,
                ),
                0
            )

            # -------------------------------------------------
            # Damage
            # -------------------------------------------------

            damage_units = int(
                opening_stock
                * DAMAGE_RATE
            )

            # -------------------------------------------------
            # Expiry
            # -------------------------------------------------

            expiry_units = 0

            if (
                random.random()
                < EXPIRY_RATE
            ):

                expiry_units = min(
                    int(
                        opening_stock
                        * random.uniform(
                            0.01,
                            0.05
                        )
                    ),
                    opening_stock
                )

            # -------------------------------------------------
            # Available stock
            # -------------------------------------------------

            available_stock = max(
                opening_stock
                + received_units
                - damage_units
                - expiry_units,
                0
            )

            # -------------------------------------------------
            # Actual fulfilled sales
            # -------------------------------------------------

            sold_units = min(
                demand_units,
                available_stock
            )

            stockout_units = max(
                demand_units
                - sold_units,
                0
            )

            closing_stock = max(
                available_stock
                - sold_units,
                0
            )

            # -------------------------------------------------
            # Save record
            # -------------------------------------------------

            records.append(
                {
                    "inventory_id":
                        f"INV{inventory_id:09d}",

                    "date_id":
                        int(
                            date.strftime("%Y%m%d")
                        ),

                    "date":
                        date,

                    "product_id":
                        row.product_id,

                    "warehouse_id":
                        row.warehouse_id,

                    "opening_stock":
                        opening_stock,

                    "demand_units":
                        demand_units,

                    "received_units":
                        received_units,

                    "sold_units":
                        sold_units,

                    "closing_stock":
                        closing_stock,

                    "damaged_units":
                        damage_units,

                    "expired_units":
                        expiry_units,

                    "stockout_units":
                        stockout_units,
                }
            )

            current_stock[key] = closing_stock

            inventory_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_inventory(df):

    print(
        "\nValidating inventory..."
    )

    # Inventory equation
    calculated_closing = (
        df["opening_stock"]
        + df["received_units"]
        - df["sold_units"]
        - df["damaged_units"]
        - df["expired_units"]
    )

    # Negative values should never occur.
    invalid_negative = (
        df["closing_stock"] < 0
    ).sum()

    print(
        f"Negative inventory rows: "
        f"{invalid_negative:,}"
    )

    # Reconciliation check
    reconciliation_errors = (
        df["closing_stock"]
        != calculated_closing.clip(
            lower=0
        )
    ).sum()

    print(
        f"Reconciliation errors: "
        f"{reconciliation_errors:,}"
    )

    # Demand >= actual sales
    invalid_sales = (
        df["sold_units"]
        >
        df["demand_units"]
    ).sum()

    print(
        f"Demand/sales violations: "
        f"{invalid_sales:,}"
    )

    return df


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

def save_inventory(df):

    output_file = (
        OPERATIONAL_DIR /
        "fact_inventory.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nSaved inventory data:"
        f"\n{output_file}"
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("FMCG INVENTORY ENGINE")
    print("=" * 60)

    df = generate_inventory()

    print(
        f"\nGenerated inventory records: "
        f"{len(df):,}"
    )

    df = validate_inventory(df)

    save_inventory(df)

    print("\nInventory summary:")

    print(
        f"Opening stock: "
        f"{df['opening_stock'].sum():,}"
    )

    print(
        f"Received: "
        f"{df['received_units'].sum():,}"
    )

    print(
        f"Sold: "
        f"{df['sold_units'].sum():,}"
    )

    print(
        f"Stockout units: "
        f"{df['stockout_units'].sum():,}"
    )

    print(
        f"Closing stock: "
        f"{df['closing_stock'].sum():,}"
    )

    print(
        f"Expired: "
        f"{df['expired_units'].sum():,}"
    )

    print(
        f"Damaged: "
        f"{df['damaged_units'].sum():,}"
    )


if __name__ == "__main__":
    main()