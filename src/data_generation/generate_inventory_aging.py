import random
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

PROCESSED_DIR = Path(
    "data/processed"
)

OPERATIONAL_DIR = Path(
    "data/raw/operational"
)


SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():

    shipments = pd.read_csv(
        OPERATIONAL_DIR /
        "fact_shipments.csv"
    )

    products = pd.read_csv(
        PROCESSED_DIR /
        "dim_product.csv"
    )

    inventory = pd.read_csv(
        OPERATIONAL_DIR /
        "fact_inventory.csv"
    )

    shipments["actual_delivery_date"] = (
        pd.to_datetime(
            shipments[
                "actual_delivery_date"
            ]
        )
    )

    inventory["date"] = pd.to_datetime(
        inventory["date"]
    )

    return (
        shipments,
        products,
        inventory,
    )


# ---------------------------------------------------------
# CREATE INVENTORY RECEIPT LOTS
# ---------------------------------------------------------

def create_receipt_lots(
    shipments,
    products
):

    shipments = shipments.merge(
        products[
            [
                "product_id",
                "shelf_life_days",
                "unit_cost",
            ]
        ],
        on="product_id",
        how="left"
    )

    records = []

    lot_id = 1

    for shipment in shipments.itertuples(
        index=False
    ):

        quantity = (
            shipment.quantity_delivered
        )

        if quantity <= 0:
            continue

        receipt_date = (
            shipment.actual_delivery_date
        )

        shelf_life = (
            shipment.shelf_life_days
        )

        expiry_date = (
            receipt_date
            +
            pd.Timedelta(
                days=int(
                    shelf_life
                )
            )
        )

        records.append(
            {
                "lot_id":
                    f"LOT{lot_id:09d}",

                "shipment_id":
                    shipment.shipment_id,

                "po_id":
                    shipment.po_id,

                "product_id":
                    shipment.product_id,

                "warehouse_id":
                    shipment.warehouse_id,

                "receipt_date":
                    receipt_date,

                "expiry_date":
                    expiry_date,

                "received_units":
                    quantity,

                "remaining_units":
                    quantity,

                "unit_cost":
                    shipment.unit_cost,

                "shelf_life_days":
                    shelf_life,
            }
        )

        lot_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------
# CALCULATE INVENTORY AGE
# ---------------------------------------------------------

def calculate_age(
    lots,
    analysis_date
):

    lots = lots.copy()

    lots["analysis_date"] = (
        pd.to_datetime(
            analysis_date
        )
    )

    lots["age_days"] = (
        lots["analysis_date"]
        -
        lots["receipt_date"]
    ).dt.days

    lots["remaining_shelf_life_days"] = (
        lots["expiry_date"]
        -
        lots["analysis_date"]
    ).dt.days

    lots["age_days"] = (
        lots["age_days"]
        .clip(lower=0)
    )

    return lots


# ---------------------------------------------------------
# AGE BUCKET
# ---------------------------------------------------------

def assign_age_bucket(
    age
):

    if age <= 30:
        return "0-30 Days"

    elif age <= 60:
        return "31-60 Days"

    elif age <= 90:
        return "61-90 Days"

    elif age <= 180:
        return "91-180 Days"

    return "180+ Days"


# ---------------------------------------------------------
# EXPIRY RISK
# ---------------------------------------------------------

def assign_expiry_risk(
    remaining_days,
    shelf_life
):

    if remaining_days <= 0:
        return "EXPIRED"

    remaining_ratio = (
        remaining_days
        /
        max(
            shelf_life,
            1
        )
    )

    if remaining_ratio <= 0.10:
        return "CRITICAL"

    elif remaining_ratio <= 0.25:
        return "HIGH"

    elif remaining_ratio <= 0.50:
        return "MEDIUM"

    return "LOW"


# ---------------------------------------------------------
# APPLY FIFO INVENTORY CONSUMPTION
# ---------------------------------------------------------

def apply_fifo_consumption(
    lots,
    inventory
):

    lots = lots.copy()

    lots["remaining_units"] = (
        lots["received_units"]
    )

    inventory = (
        inventory
        .sort_values("date")
    )

    # Process each warehouse + product
    # independently.

    groups = inventory[
        [
            "product_id",
            "warehouse_id",
        ]
    ].drop_duplicates()

    for group in groups.itertuples(
        index=False
    ):

        product_id = (
            group.product_id
        )

        warehouse_id = (
            group.warehouse_id
        )

        group_lots = lots[
            (
                lots["product_id"]
                == product_id
            )
            &
            (
                lots["warehouse_id"]
                == warehouse_id
            )
        ].sort_values(
            "receipt_date"
        )

        if group_lots.empty:
            continue

        group_inventory = inventory[
            (
                inventory["product_id"]
                == product_id
            )
            &
            (
                inventory["warehouse_id"]
                == warehouse_id
            )
        ]

        for day in group_inventory.itertuples(
            index=False
        ):

            sold = int(
                day.sold_units
            )

            if sold <= 0:
                continue

            for idx in group_lots.index:

                available = (
                    lots.loc[
                        idx,
                        "remaining_units"
                    ]
                )

                if available <= 0:
                    continue

                consumption = min(
                    available,
                    sold
                )

                lots.loc[
                    idx,
                    "remaining_units"
                ] -= consumption

                sold -= consumption

                if sold <= 0:
                    break

    return lots


# ---------------------------------------------------------
# GENERATE AGING
# ---------------------------------------------------------

def generate_aging():

    (
        shipments,
        products,
        inventory,
    ) = load_data()

    lots = create_receipt_lots(
        shipments,
        products
    )

    if lots.empty:

        print(
            "No shipment lots found."
        )

        return pd.DataFrame()

    # -----------------------------------------------------
    # Apply FIFO consumption
    # -----------------------------------------------------

    lots = apply_fifo_consumption(
        lots,
        inventory
    )

    # -----------------------------------------------------
    # Analysis date
    # -----------------------------------------------------

    analysis_date = (
        inventory["date"].max()
    )

    lots = calculate_age(
        lots,
        analysis_date
    )

    # -----------------------------------------------------
    # Age buckets
    # -----------------------------------------------------

    lots["age_bucket"] = (
        lots["age_days"]
        .apply(
            assign_age_bucket
        )
    )

    # -----------------------------------------------------
    # Expiry risk
    # -----------------------------------------------------

    lots["expiry_risk"] = lots.apply(
        lambda row:
        assign_expiry_risk(
            row[
                "remaining_shelf_life_days"
            ],
            row[
                "shelf_life_days"
            ]
        ),
        axis=1
    )

    # -----------------------------------------------------
    # Inventory value
    # -----------------------------------------------------

    lots["inventory_value"] = (
        lots["remaining_units"]
        *
        lots["unit_cost"]
    )

    # -----------------------------------------------------
    # Expiry risk value
    # -----------------------------------------------------

    lots["expiry_risk_value"] = np.where(
        lots["expiry_risk"].isin(
            [
                "CRITICAL",
                "HIGH",
                "EXPIRED",
            ]
        ),
        lots["inventory_value"],
        0
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    output_file = (
        OPERATIONAL_DIR /
        "fact_inventory_aging.csv"
    )

    lots.to_csv(
        output_file,
        index=False
    )

    return lots


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_aging(
    df
):

    print(
        "\n" + "=" * 60
    )

    print(
        "INVENTORY AGING VALIDATION"
    )

    print(
        "=" * 60
    )

    print(
        f"Negative remaining units: "
        f"{(df['remaining_units'] < 0).sum():,}"
    )

    print(
        f"Negative age values: "
        f"{(df['age_days'] < 0).sum():,}"
    )

    print(
        f"Expired lots: "
        f"{(df['expiry_risk'] == 'EXPIRED').sum():,}"
    )

    print(
        f"Critical lots: "
        f"{(df['expiry_risk'] == 'CRITICAL').sum():,}"
    )

    print(
        f"High-risk lots: "
        f"{(df['expiry_risk'] == 'HIGH').sum():,}"
    )


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

def print_summary(
    df
):

    print(
        "\nInventory Aging Summary"
    )

    print(
        "-" * 50
    )

    print(
        "\nAge Distribution:"
    )

    print(
        df.groupby(
            "age_bucket"
        )[
            "remaining_units"
        ]
        .sum()
        .sort_index()
        .to_string()
    )

    print(
        "\nExpiry Risk:"
    )

    print(
        df.groupby(
            "expiry_risk"
        )[
            "remaining_units"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
        .to_string()
    )

    print(
        "\nExpiry Risk Value:"
    )

    print(
        f"₹{df['expiry_risk_value'].sum():,.2f}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)

    print(
        "FMCG INVENTORY AGING ENGINE"
    )

    print("=" * 60)

    df = generate_aging()

    if df.empty:
        return

    validate_aging(
        df
    )

    print_summary(
        df
    )

    print(
        "\nSaved:"
        "\ndata/raw/operational/"
        "fact_inventory_aging.csv"
    )


if __name__ == "__main__":
    main()