import random
from pathlib import Path

import numpy as np
import pandas as pd

from reorder_config import (
    TARGET_COVERAGE_DAYS,
    SAFETY_STOCK_PERCENT,
    MIN_ORDER_QTY,
    MAX_ORDER_MULTIPLIER,
)

from supplier_config import SUPPLIER_PROFILES


# =========================================================
# PATHS
# =========================================================

PROCESSED_DIR = Path("data/processed")

OPERATIONAL_DIR = Path(
    "data/raw/operational"
)

OPERATIONAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# RANDOM SEED
# =========================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print(
        "\nLoading purchase-order master data..."
    )

    inventory_file = (
        OPERATIONAL_DIR /
        "fact_inventory.csv"
    )

    products_file = (
        PROCESSED_DIR /
        "dim_product.csv"
    )

    suppliers_file = (
        PROCESSED_DIR /
        "dim_supplier.csv"
    )

    warehouses_file = (
        PROCESSED_DIR /
        "dim_warehouse.csv"
    )

    required_files = {
        "Inventory": inventory_file,
        "Products": products_file,
        "Suppliers": suppliers_file,
        "Warehouses": warehouses_file,
    }

    for name, file_path in required_files.items():

        if not file_path.exists():

            raise FileNotFoundError(
                f"\nRequired {name.lower()} file not found:\n"
                f"{file_path.resolve()}\n\n"
                f"Please generate the required master/operational "
                f"data before running the purchase-order engine."
            )

    # -----------------------------------------------------
    # Read files
    # -----------------------------------------------------

    inventory = pd.read_csv(
        inventory_file
    )

    products = pd.read_csv(
        products_file
    )

    suppliers = pd.read_csv(
        suppliers_file
    )

    warehouses = pd.read_csv(
        warehouses_file
    )

    # -----------------------------------------------------
    # Convert dates
    # -----------------------------------------------------

    if "date" not in inventory.columns:

        raise ValueError(
            "fact_inventory.csv is missing the 'date' column."
        )

    inventory["date"] = pd.to_datetime(
        inventory["date"]
    )

    # -----------------------------------------------------
    # Required columns
    # -----------------------------------------------------

    required_inventory_columns = [
        "date",
        "product_id",
        "warehouse_id",
        "demand_units",
        "closing_stock",
    ]

    required_product_columns = [
        "product_id",
        "unit_cost",
    ]

    required_supplier_columns = [
        "supplier_id",
        "supplier_region",
        "supplier_rating",
        "performance_tier",
    ]

    required_warehouse_columns = [
        "warehouse_id",
        "region",
    ]

    # -----------------------------------------------------
    # Validate columns
    # -----------------------------------------------------

    missing_inventory = [
        column
        for column in required_inventory_columns
        if column not in inventory.columns
    ]

    missing_products = [
        column
        for column in required_product_columns
        if column not in products.columns
    ]

    missing_suppliers = [
        column
        for column in required_supplier_columns
        if column not in suppliers.columns
    ]

    missing_warehouses = [
        column
        for column in required_warehouse_columns
        if column not in warehouses.columns
    ]

    if missing_inventory:

        raise ValueError(
            "Missing columns in fact_inventory.csv: "
            + ", ".join(missing_inventory)
        )

    if missing_products:

        raise ValueError(
            "Missing columns in dim_product.csv: "
            + ", ".join(missing_products)
        )

    if missing_suppliers:

        raise ValueError(
            "Missing columns in dim_supplier.csv: "
            + ", ".join(missing_suppliers)
        )

    if missing_warehouses:

        raise ValueError(
            "Missing columns in dim_warehouse.csv: "
            + ", ".join(missing_warehouses)
        )

    # -----------------------------------------------------
    # Clean numeric fields
    # -----------------------------------------------------

    inventory["demand_units"] = pd.to_numeric(
        inventory["demand_units"],
        errors="coerce"
    ).fillna(0)

    inventory["closing_stock"] = pd.to_numeric(
        inventory["closing_stock"],
        errors="coerce"
    ).fillna(0)

    products["unit_cost"] = pd.to_numeric(
        products["unit_cost"],
        errors="coerce"
    )

    suppliers["supplier_rating"] = pd.to_numeric(
        suppliers["supplier_rating"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Remove invalid records
    # -----------------------------------------------------

    inventory = inventory.dropna(
        subset=[
            "product_id",
            "warehouse_id",
            "date",
        ]
    )

    products = products.dropna(
        subset=[
            "product_id",
            "unit_cost",
        ]
    )

    suppliers = suppliers.dropna(
        subset=[
            "supplier_id",
            "supplier_region",
            "supplier_rating",
            "performance_tier",
        ]
    )

    warehouses = warehouses.dropna(
        subset=[
            "warehouse_id",
            "region",
        ]
    )

    # -----------------------------------------------------
    # Prevent invalid supplier weights
    # -----------------------------------------------------

    suppliers["supplier_rating"] = suppliers[
        "supplier_rating"
    ].clip(
        lower=0
    )

    # If all ratings are zero, use equal weights later.
    # -----------------------------------------------------

    print(
        f"Inventory records : {len(inventory):,}"
    )

    print(
        f"Products          : {len(products):,}"
    )

    print(
        f"Suppliers         : {len(suppliers):,}"
    )

    print(
        f"Warehouses        : {len(warehouses):,}"
    )

    return (
        inventory,
        products,
        suppliers,
        warehouses,
    )


# =========================================================
# CALCULATE AVERAGE DEMAND
# =========================================================

def calculate_demand_profile(
    inventory
):
    """
    Calculate average daily demand by
    product and warehouse.
    """

    demand_profile = (
        inventory
        .groupby(
            [
                "product_id",
                "warehouse_id",
            ],
            as_index=False
        )
        .agg(
            average_daily_demand=(
                "demand_units",
                "mean"
            )
        )
    )

    demand_profile[
        "average_daily_demand"
    ] = pd.to_numeric(
        demand_profile[
            "average_daily_demand"
        ],
        errors="coerce"
    ).fillna(0)

    return demand_profile


# =========================================================
# SUPPLIER SELECTION
# =========================================================

def select_supplier(
    suppliers,
    warehouse
):
    """
    Select a supplier.

    Priority:
    1. Same region as warehouse
    2. Supplier rating as selection weight
    """

    warehouse_region = warehouse[
        "region"
    ]

    regional = suppliers[
        suppliers["supplier_region"]
        == warehouse_region
    ]

    # If no supplier exists in the same
    # region, use all suppliers.
    if regional.empty:

        regional = suppliers

    if regional.empty:

        raise ValueError(
            "No suppliers available "
            "for purchase-order generation."
        )

    # -----------------------------------------------------
    # Supplier weights
    # -----------------------------------------------------

    weights = regional[
        "supplier_rating"
    ].astype(float)

    weight_sum = weights.sum()

    if weight_sum <= 0:

        # Equal probability if all ratings are zero.
        weights = None

    else:

        weights = (
            weights /
            weight_sum
        )

    # -----------------------------------------------------
    # Select supplier
    # -----------------------------------------------------

    selected = regional.sample(
        n=1,
        weights=weights,
        random_state=random.randint(
            0,
            999999
        )
    ).iloc[0]

    return selected


# =========================================================
# CALCULATE SUPPLIER LEAD TIME
# =========================================================

def calculate_lead_time(
    supplier
):
    """
    Calculate supplier lead time using
    supplier performance tier.
    """

    performance_tier = supplier[
        "performance_tier"
    ]

    if performance_tier not in SUPPLIER_PROFILES:

        raise ValueError(
            f"Unknown supplier performance tier: "
            f"{performance_tier}"
        )

    profile = SUPPLIER_PROFILES[
        performance_tier
    ]

    lead_time = random.randint(
        profile["lead_time_min"],
        profile["lead_time_max"]
    )

    # Poor suppliers occasionally
    # experience additional delays.

    if (
        random.random()
        < profile["late_probability"]
    ):

        lead_time += random.randint(
            1,
            5
        )

    return lead_time


# =========================================================
# GENERATE PURCHASE ORDERS
# =========================================================

def generate_purchase_orders():

    (
        inventory,
        products,
        suppliers,
        warehouses,
    ) = load_data()

    # -----------------------------------------------------
    # Demand profile
    # -----------------------------------------------------

    demand_profile = (
        calculate_demand_profile(
            inventory
        )
    )

    # -----------------------------------------------------
    # Review inventory every 7 days
    # -----------------------------------------------------

    start_date = inventory[
        "date"
    ].min()

    end_date = inventory[
        "date"
    ].max()

    review_dates = pd.date_range(
        start_date,
        end_date,
        freq="7D"
    )

    records = []

    po_id = 1

    # =====================================================
    # GENERATE POs
    # =====================================================

    for review_date in review_dates:

        snapshot = inventory[
            inventory["date"]
            == review_date
        ]

        if snapshot.empty:

            continue

        # -------------------------------------------------
        # Process each inventory position
        # -------------------------------------------------

        for row in snapshot.itertuples(
            index=False
        ):

            # -------------------------------------------------
            # Find demand profile
            # -------------------------------------------------

            demand_row = demand_profile[
                (
                    demand_profile[
                        "product_id"
                    ]
                    == row.product_id
                )
                &
                (
                    demand_profile[
                        "warehouse_id"
                    ]
                    == row.warehouse_id
                )
            ]

            if demand_row.empty:

                continue

            average_daily_demand = float(
                demand_row[
                    "average_daily_demand"
                ].iloc[0]
            )

            if average_daily_demand <= 0:

                continue

            # -------------------------------------------------
            # Find warehouse
            # -------------------------------------------------

            warehouse_matches = warehouses[
                warehouses[
                    "warehouse_id"
                ]
                == row.warehouse_id
            ]

            if warehouse_matches.empty:

                continue

            warehouse = (
                warehouse_matches
                .iloc[0]
            )

            # -------------------------------------------------
            # Select supplier
            # -------------------------------------------------

            supplier = select_supplier(
                suppliers,
                warehouse
            )

            # -------------------------------------------------
            # Calculate lead time
            # -------------------------------------------------

            lead_time = calculate_lead_time(
                supplier
            )

            # =================================================
            # REORDER POINT
            # =================================================

            safety_stock = (
                average_daily_demand
                * lead_time
                * SAFETY_STOCK_PERCENT
            )

            reorder_point = (
                average_daily_demand
                * lead_time
                + safety_stock
            )

            # =================================================
            # CURRENT INVENTORY
            # =================================================

            current_stock = float(
                row.closing_stock
            )

            # No PO required if stock is
            # above reorder point.

            if current_stock >= reorder_point:

                continue

            # =================================================
            # TARGET STOCK
            # =================================================

            target_stock = (
                average_daily_demand
                * TARGET_COVERAGE_DAYS
            )

            # =================================================
            # ORDER QUANTITY
            # =================================================

            order_quantity = (
                target_stock
                + reorder_point
                - current_stock
            )

            # Add controlled variability.

            order_quantity *= random.uniform(
                0.90,
                1.10
            )

            # Apply minimum order quantity.

            order_quantity = int(
                max(
                    MIN_ORDER_QTY,
                    order_quantity
                )
            )

            # -------------------------------------------------
            # Maximum order quantity
            # -------------------------------------------------

            maximum_quantity = int(
                max(
                    MIN_ORDER_QTY,
                    average_daily_demand
                    * TARGET_COVERAGE_DAYS
                    * MAX_ORDER_MULTIPLIER
                )
            )

            order_quantity = min(
                order_quantity,
                maximum_quantity
            )

            # -------------------------------------------------
            # Final safety check
            # -------------------------------------------------

            if order_quantity <= 0:

                continue

            # =================================================
            # EXPECTED DELIVERY
            # =================================================

            expected_delivery = (
                review_date
                +
                pd.Timedelta(
                    days=lead_time
                )
            )

            # =================================================
            # PRODUCT UNIT COST
            # =================================================

            product_matches = products[
                products[
                    "product_id"
                ]
                == row.product_id
            ]

            if product_matches.empty:

                continue

            unit_cost = float(
                product_matches[
                    "unit_cost"
                ].iloc[0]
            )

            if unit_cost <= 0:

                continue

            # =================================================
            # CREATE PO RECORD
            # =================================================

            records.append(
                {
                    "po_id":
                        f"PO{po_id:08d}",

                    "date_id":
                        int(
                            review_date.strftime(
                                "%Y%m%d"
                            )
                        ),

                    "order_date":
                        review_date,

                    "supplier_id":
                        supplier[
                            "supplier_id"
                        ],

                    "product_id":
                        row.product_id,

                    "warehouse_id":
                        row.warehouse_id,

                    "ordered_quantity":
                        order_quantity,

                    "unit_cost":
                        round(
                            unit_cost,
                            2
                        ),

                    "reorder_point":
                        round(
                            reorder_point,
                            2
                        ),

                    "safety_stock":
                        round(
                            safety_stock,
                            2
                        ),

                    "lead_time_days":
                        lead_time,

                    "expected_delivery_date":
                        expected_delivery,

                    "order_status":
                        "Pending",
                }
            )

            po_id += 1

    # -----------------------------------------------------
    # Convert records to DataFrame
    # -----------------------------------------------------

    return pd.DataFrame(
        records
    )


# =========================================================
# VALIDATION
# =========================================================

def validate_purchase_orders(
    df
):

    print(
        "\nValidating purchase orders..."
    )

    # -----------------------------------------------------
    # Empty DataFrame protection
    # -----------------------------------------------------

    if df.empty:

        print(
            "No purchase orders require validation."
        )

        return df

    # -----------------------------------------------------
    # Positive quantities
    # -----------------------------------------------------

    df = df[
        df["ordered_quantity"] > 0
    ]

    # -----------------------------------------------------
    # Positive unit costs
    # -----------------------------------------------------

    df = df[
        df["unit_cost"] > 0
    ]

    # -----------------------------------------------------
    # Valid reorder points
    # -----------------------------------------------------

    df = df[
        df["reorder_point"] >= 0
    ]

    # -----------------------------------------------------
    # Valid safety stock
    # -----------------------------------------------------

    df = df[
        df["safety_stock"] >= 0
    ]

    # -----------------------------------------------------
    # Remove duplicate POs
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "po_id"
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

def save_purchase_orders(
    df
):

    output_file = (
        OPERATIONAL_DIR
        /
        "fact_purchase_orders.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved purchase orders:"
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
        "FMCG PURCHASE ORDER ENGINE"
    )

    print(
        "=" * 60
    )

    # -----------------------------------------------------
    # Generate POs
    # -----------------------------------------------------

    df = generate_purchase_orders()

    print(
        f"\nGenerated POs: "
        f"{len(df):,}"
    )

    # -----------------------------------------------------
    # No POs
    # -----------------------------------------------------

    if df.empty:

        print(
            "\nNo purchase orders generated."
        )

        print(
            "This means current inventory "
            "levels are above reorder points."
        )

        return

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    df = validate_purchase_orders(
        df
    )

    print(
        f"Valid POs: "
        f"{len(df):,}"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_purchase_orders(
        df
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    print(
        "\nPO summary:"
    )

    ordered_units = int(
        df[
            "ordered_quantity"
        ].sum()
    )

    po_value = float(
        (
            df[
                "ordered_quantity"
            ]
            *
            df[
                "unit_cost"
            ]
        ).sum()
    )

    print(
        f"Ordered units: "
        f"{ordered_units:,}"
    )

    print(
        f"PO value: "
        f"₹{po_value:,.2f}"
    )

    print(
        f"Suppliers used: "
        f"{df['supplier_id'].nunique():,}"
    )

    print(
        f"Products ordered: "
        f"{df['product_id'].nunique():,}"
    )

    print(
        f"Warehouses supplied: "
        f"{df['warehouse_id'].nunique():,}"
    )

    # -----------------------------------------------------
    # Supplier distribution
    # -----------------------------------------------------

    print(
        "\nSupplier distribution:"
    )

    print(
        df[
            "supplier_id"
        ]
        .value_counts()
        .head(10)
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()