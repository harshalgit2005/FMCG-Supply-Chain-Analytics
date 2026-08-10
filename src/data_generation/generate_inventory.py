import random
from pathlib import Path

import numpy as np
import pandas as pd


PROCESSED_DIR = Path("data/processed")
OPERATIONAL_DIR = Path("data/raw/operational")

SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

INITIAL_STOCK_DAYS = 15

DAMAGE_RATE = 0.002

EXPIRY_PROBABILITY = 0.001


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():

    sales = pd.read_csv(
        OPERATIONAL_DIR /
        "fact_sales.csv"
    )

    shipments = pd.read_csv(
        OPERATIONAL_DIR /
        "fact_shipments.csv"
    )

    products = pd.read_csv(
        PROCESSED_DIR /
        "dim_product.csv"
    )

    warehouses = pd.read_csv(
        PROCESSED_DIR /
        "dim_warehouse.csv"
    )

    mapping = pd.read_csv(
        PROCESSED_DIR /
        "store_warehouse_mapping.csv"
    )

    sales["date"] = pd.to_datetime(
        sales["date"]
    )

    shipments["shipment_date"] = (
        pd.to_datetime(
            shipments["shipment_date"]
        )
    )

    shipments["actual_delivery_date"] = (
        pd.to_datetime(
            shipments[
                "actual_delivery_date"
            ]
        )
    )

    return (
        sales,
        shipments,
        products,
        warehouses,
        mapping,
    )


# ---------------------------------------------------------
# MAP STORE SALES TO WAREHOUSES
# ---------------------------------------------------------

def aggregate_sales(
    sales,
    mapping
):

    sales = sales.merge(
        mapping,
        on="store_id",
        how="left"
    )

    warehouse_sales = (
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

    warehouse_sales = (
        warehouse_sales
        .rename(
            columns={
                "quantity_sold":
                "demand_units"
            }
        )
    )

    return warehouse_sales


# ---------------------------------------------------------
# AGGREGATE ACTUAL SHIPMENT RECEIPTS
# ---------------------------------------------------------

def aggregate_receipts(
    shipments
):

    receipts = (
        shipments
        .groupby(
            [
                "actual_delivery_date",
                "product_id",
                "warehouse_id",
            ],
            as_index=False
        )
        ["quantity_delivered"]
        .sum()
    )

    receipts = (
        receipts
        .rename(
            columns={
                "actual_delivery_date":
                "date",

                "quantity_delivered":
                "received_units",
            }
        )
    )

    return receipts


# ---------------------------------------------------------
# CREATE INVENTORY UNIVERSE
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
# INITIAL STOCK
# ---------------------------------------------------------

def initialize_stock(
    universe,
    demand
):

    current_stock = {}

    # Calculate average demand for each SKU
    # and warehouse.

    demand_profile = (
        demand
        .groupby(
            [
                "product_id",
                "warehouse_id",
            ],
            as_index=False
        )
        ["demand_units"]
        .mean()
    )

    demand_lookup = {
        (
            row.product_id,
            row.warehouse_id,
        ): row.demand_units

        for row in demand_profile.itertuples(
            index=False
        )
    }

    for row in universe.itertuples(
        index=False
    ):

        avg_demand = demand_lookup.get(
            (
                row.product_id,
                row.warehouse_id,
            ),
            10
        )

        initial_stock = int(
            max(
                10,
                avg_demand
                * INITIAL_STOCK_DAYS
                * random.uniform(
                    0.8,
                    1.5
                )
            )
        )

        current_stock[
            (
                row.product_id,
                row.warehouse_id
            )
        ] = initial_stock

    return current_stock


# ---------------------------------------------------------
# GENERATE INVENTORY
# ---------------------------------------------------------

def generate_inventory():

    (
        sales,
        shipments,
        products,
        warehouses,
        mapping,
    ) = load_data()

    # -----------------------------------------------------
    # Aggregate demand
    # -----------------------------------------------------

    demand = aggregate_sales(
        sales,
        mapping
    )

    # -----------------------------------------------------
    # Aggregate actual shipment receipts
    # -----------------------------------------------------

    receipts = aggregate_receipts(
        shipments
    )

    # -----------------------------------------------------
    # Inventory universe
    # -----------------------------------------------------

    universe = create_inventory_universe(
        products,
        warehouses
    )

    # -----------------------------------------------------
    # Date range
    # -----------------------------------------------------

    start_date = min(
        demand["date"].min(),
        receipts["date"].min()
    )

    end_date = max(
        demand["date"].max(),
        receipts["date"].max()
    )

    dates = pd.date_range(
        start_date,
        end_date,
        freq="D"
    )

    # -----------------------------------------------------
    # Lookup dictionaries
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

    receipt_lookup = {
        (
            row.date,
            row.product_id,
            row.warehouse_id,
        ): row.received_units

        for row in receipts.itertuples(
            index=False
        )
    }

    # -----------------------------------------------------
    # Initialize stock
    # -----------------------------------------------------

    current_stock = initialize_stock(
        universe,
        demand
    )

    records = []

    inventory_id = 1

    # -----------------------------------------------------
    # Daily inventory simulation
    # -----------------------------------------------------

    for date in dates:

        for row in universe.itertuples(
            index=False
        ):

            key = (
                row.product_id,
                row.warehouse_id
            )

            opening_stock = (
                current_stock[key]
            )

            # -------------------------------------------------
            # ACTUAL shipment receipts
            # -------------------------------------------------

            received_units = receipt_lookup.get(
                (
                    date,
                    row.product_id,
                    row.warehouse_id,
                ),
                0
            )

            # -------------------------------------------------
            # Customer demand
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
                round(
                    opening_stock
                    * DAMAGE_RATE
                )
            )

            damage_units = min(
                damage_units,
                opening_stock
            )

            # -------------------------------------------------
            # Expiry
            # -------------------------------------------------

            expired_units = 0

            if (
                opening_stock > 0
                and
                random.random()
                < EXPIRY_PROBABILITY
            ):

                expired_units = int(
                    opening_stock
                    * random.uniform(
                        0.01,
                        0.05
                    )
                )

                expired_units = min(
                    expired_units,
                    max(
                        opening_stock
                        - damage_units,
                        0
                    )
                )

            # -------------------------------------------------
            # Available stock
            # -------------------------------------------------

            available_stock = max(
                opening_stock
                + received_units
                - damage_units
                - expired_units,
                0
            )

            # -------------------------------------------------
            # Fulfilled demand
            # -------------------------------------------------

            sold_units = min(
                demand_units,
                available_stock
            )

            # -------------------------------------------------
            # Stockout
            # -------------------------------------------------

            stockout_units = max(
                demand_units
                - sold_units,
                0
            )

            stockout_flag = int(
                stockout_units > 0
            )

            # -------------------------------------------------
            # Closing inventory
            # -------------------------------------------------

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
                            date.strftime(
                                "%Y%m%d"
                            )
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
                        expired_units,

                    "stockout_units":
                        stockout_units,

                    "stockout_flag":
                        stockout_flag,
                }
            )

            current_stock[key] = (
                closing_stock
            )

            inventory_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_inventory(df):

    print(
        "\n" + "=" * 60
    )

    print(
        "INVENTORY VALIDATION"
    )

    print(
        "=" * 60
    )

    # -----------------------------------------------------
    # Negative inventory
    # -----------------------------------------------------

    negative_inventory = (
        df["closing_stock"] < 0
    ).sum()

    print(
        f"Negative inventory rows: "
        f"{negative_inventory:,}"
    )

    # -----------------------------------------------------
    # Inventory equation
    # -----------------------------------------------------

    calculated_closing = (
        df["opening_stock"]
        + df["received_units"]
        - df["sold_units"]
        - df["damaged_units"]
        - df["expired_units"]
    )

    calculated_closing = (
        calculated_closing.clip(
            lower=0
        )
    )

    reconciliation_errors = (
        df["closing_stock"]
        != calculated_closing
    ).sum()

    print(
        f"Reconciliation errors: "
        f"{reconciliation_errors:,}"
    )

    # -----------------------------------------------------
    # Sales cannot exceed demand
    # -----------------------------------------------------

    demand_errors = (
        df["sold_units"]
        >
        df["demand_units"]
    ).sum()

    print(
        f"Sales > demand errors: "
        f"{demand_errors:,}"
    )

    # -----------------------------------------------------
    # Stockout validation
    # -----------------------------------------------------

    calculated_stockout = (
        df["demand_units"]
        -
        df["sold_units"]
    ).clip(
        lower=0
    )

    stockout_errors = (
        df["stockout_units"]
        != calculated_stockout
    ).sum()

    print(
        f"Stockout calculation errors: "
        f"{stockout_errors:,}"
    )

    # -----------------------------------------------------
    # Receipt validation
    # -----------------------------------------------------

    negative_receipts = (
        df["received_units"] < 0
    ).sum()

    print(
        f"Negative receipts: "
        f"{negative_receipts:,}"
    )

    return df


# ---------------------------------------------------------
# SAVE
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
        f"\nSaved:"
        f"\n{output_file}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)

    print(
        "FMCG INVENTORY ENGINE"
    )

    print("=" * 60)

    df = generate_inventory()

    print(
        f"\nGenerated records: "
        f"{len(df):,}"
    )

    df = validate_inventory(
        df
    )

    save_inventory(
        df
    )

    print(
        "\nInventory Summary"
    )

    print(
        "-" * 40
    )

    print(
        f"Demand: "
        f"{df['demand_units'].sum():,}"
    )

    print(
        f"Sold: "
        f"{df['sold_units'].sum():,}"
    )

    print(
        f"Received: "
        f"{df['received_units'].sum():,}"
    )

    print(
        f"Closing Stock: "
        f"{df['closing_stock'].sum():,}"
    )

    print(
        f"Stockout Units: "
        f"{df['stockout_units'].sum():,}"
    )

    print(
        f"Expired Units: "
        f"{df['expired_units'].sum():,}"
    )

    print(
        f"Damaged Units: "
        f"{df['damaged_units'].sum():,}"
    )

    stockout_rate = (
        df["stockout_units"].sum()
        /
        max(
            df["demand_units"].sum(),
            1
        )
    )

    print(
        f"Stockout Rate: "
        f"{stockout_rate * 100:.2f}%"
    )


if __name__ == "__main__":
    main()