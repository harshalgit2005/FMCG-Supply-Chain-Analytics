
"""
FMCG PURCHASE ORDER GENERATION ENGINE

Purpose:
    Generate realistic purchase orders from inventory,
    product, supplier, and warehouse master data.

Output:
    data/raw/operational/fact_purchase_orders.csv
    data/processed/fact_purchase_orders.csv

Important:
    The generated data includes received_quantity because
    the MySQL fact_purchase_orders table expects it.
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OPERATIONAL_DIR = PROJECT_ROOT / "data" / "raw" / "operational"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OPERATIONAL_DIR.mkdir(parents=True, exist_ok=True)


# Reproducible results
SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# =========================================================
# PURCHASE ORDER PARAMETERS
# =========================================================

# Percentage of lead-time demand maintained as safety stock.
SAFETY_STOCK_PERCENT = 0.20

# Target number of days of demand after replenishment.
TARGET_COVERAGE_DAYS = 30

# Review cycle.
REVIEW_PERIOD_DAYS = 7

# Minimum PO quantity.
MIN_ORDER_QTY = 100

# Maximum quantity relative to target coverage.
MAX_ORDER_MULTIPLIER = 2.0

# Controlled quantity variation.
ORDER_VARIABILITY_MIN = 0.90
ORDER_VARIABILITY_MAX = 1.10

# Supplier fill-rate ranges.
SUPPLIER_FILL_RATES = {
    "Excellent": (0.97, 1.00),
    "Good": (0.94, 0.99),
    "Average": (0.88, 0.96),
    "Poor": (0.75, 0.92),
}

# Probability of partial receipt even for reasonably
# performing suppliers.
PARTIAL_RECEIPT_PROBABILITY = 0.10

# Historical orders are considered received.
# Orders whose delivery date is after the inventory
# simulation end date remain Pending / In Transit.
IN_TRANSIT_PROBABILITY = 0.08


# =========================================================
# SUPPLIER PROFILES
# =========================================================

SUPPLIER_PROFILES = {
    "Excellent": {
        "lead_time_min": 3,
        "lead_time_max": 7,
        "late_probability": 0.05,
    },
    "Good": {
        "lead_time_min": 5,
        "lead_time_max": 10,
        "late_probability": 0.10,
    },
    "Average": {
        "lead_time_min": 7,
        "lead_time_max": 14,
        "late_probability": 0.18,
    },
    "Poor": {
        "lead_time_min": 10,
        "lead_time_max": 21,
        "late_probability": 0.30,
    },
}


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    print("\nLoading purchase-order master data...")

    inventory_file = (
        OPERATIONAL_DIR /
        "fact_inventory.csv"
    )

    # Fallback in case inventory is stored in processed.
    if not inventory_file.exists():

        inventory_file = (
            PROCESSED_DIR /
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

    inventory = pd.read_csv(inventory_file)
    products = pd.read_csv(products_file)
    suppliers = pd.read_csv(suppliers_file)
    warehouses = pd.read_csv(warehouses_file)

    # -----------------------------------------------------
    # Convert dates
    # -----------------------------------------------------

    if "date" not in inventory.columns:

        raise ValueError(
            "fact_inventory.csv is missing the 'date' column."
        )

    inventory["date"] = pd.to_datetime(
        inventory["date"],
        errors="coerce"
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
    # Clean supplier ratings
    # -----------------------------------------------------

    suppliers["supplier_rating"] = (
        suppliers["supplier_rating"]
        .clip(lower=0)
    )

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

def calculate_demand_profile(inventory):

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
    Select supplier using:

    1. Same region as warehouse
    2. Supplier rating as probability weight
    """

    warehouse_region = warehouse["region"]

    regional = suppliers[
        suppliers["supplier_region"]
        == warehouse_region
    ]

    # If no supplier exists in the same region,
    # use all suppliers.
    if regional.empty:

        regional = suppliers

    if regional.empty:

        raise ValueError(
            "No suppliers available "
            "for purchase-order generation."
        )

    weights = (
        regional["supplier_rating"]
        .astype(float)
    )

    weight_sum = weights.sum()

    if weight_sum <= 0:

        weights = None

    else:

        weights = (
            weights /
            weight_sum
        )

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
    Calculate supplier lead time from
    supplier performance tier.
    """

    performance_tier = supplier[
        "performance_tier"
    ]

    if performance_tier not in SUPPLIER_PROFILES:

        # Safe fallback
        performance_tier = "Average"

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
# CALCULATE RECEIVED QUANTITY
# =========================================================

def calculate_received_quantity(
    ordered_quantity,
    supplier,
    order_status
):

    """
    Generate received quantity based on
    supplier performance.

    Received quantity is always <= ordered quantity.
    """

    ordered_quantity = int(
        max(
            0,
            ordered_quantity
        )
    )

    if ordered_quantity <= 0:
        return 0

    if order_status in [
        "Pending",
        "In Transit"
    ]:

        return 0

    performance_tier = supplier[
        "performance_tier"
    ]

    fill_range = SUPPLIER_FILL_RATES.get(
        performance_tier,
        SUPPLIER_FILL_RATES["Average"]
    )

    fill_rate = random.uniform(
        fill_range[0],
        fill_range[1]
    )

    # Occasionally create a more noticeable
    # partial shipment.
    if random.random() < PARTIAL_RECEIPT_PROBABILITY:

        fill_rate *= random.uniform(
            0.85,
            0.95
        )

    received_quantity = int(
        round(
            ordered_quantity
            * fill_rate
        )
    )

    received_quantity = min(
        ordered_quantity,
        max(
            0,
            received_quantity
        )
    )

    return received_quantity


# =========================================================
# DETERMINE ORDER STATUS
# =========================================================

def determine_order_status(
    order_date,
    expected_delivery_date,
    simulation_end_date
):

    """
    Determine PO status relative to the
    simulation period.

    Historical delivery:
        Received

    Future delivery:
        Pending / In Transit
    """

    if expected_delivery_date > simulation_end_date:

        if random.random() < 0.50:
            return "In Transit"

        return "Pending"

    # Historical orders have normally arrived.
    return "Received"


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
    # Review every 7 days
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
        freq=f"{REVIEW_PERIOD_DAYS}D"
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
        # Process inventory positions
        # -------------------------------------------------

        for row in snapshot.itertuples(
            index=False
        ):

            # -------------------------------------------------
            # Demand profile
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
            # Warehouse
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
            # Supplier
            # -------------------------------------------------

            supplier = select_supplier(
                suppliers,
                warehouse
            )

            # -------------------------------------------------
            # Lead time
            # -------------------------------------------------

            lead_time = calculate_lead_time(
                supplier
            )

            # =================================================
            # SAFETY STOCK
            # =================================================

            safety_stock = (
                average_daily_demand
                * lead_time
                * SAFETY_STOCK_PERCENT
            )

            # =================================================
            # REORDER POINT
            # =================================================

            reorder_point = (
                average_daily_demand
                * (
                    lead_time
                    + REVIEW_PERIOD_DAYS
                )
                + safety_stock
            )

            # =================================================
            # CURRENT INVENTORY
            # =================================================

            current_stock = float(
                row.closing_stock
            )

            # =================================================
            # INVENTORY COVERAGE
            # =================================================

            inventory_days = (
                current_stock
                /
                average_daily_demand
            )

            # =================================================
            # REORDER DECISION
            # =================================================

            # Primary trigger:
            # inventory below reorder point.
            reorder_required = (
                current_stock
                < reorder_point
            )

            # Secondary trigger:
            # inventory coverage is too low.
            #
            # This makes the simulation more realistic
            # when inventory sits slightly above the
            # traditional reorder point.
            low_coverage = (
                inventory_days
                < (
                    lead_time
                    + REVIEW_PERIOD_DAYS
                    + 5
                )
            )

            if not (
                reorder_required
                or low_coverage
            ):
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

            # Controlled variability.
            order_quantity *= random.uniform(
                ORDER_VARIABILITY_MIN,
                ORDER_VARIABILITY_MAX
            )

            # Minimum order quantity.
            order_quantity = int(
                max(
                    MIN_ORDER_QTY,
                    order_quantity
                )
            )

            # =================================================
            # MAXIMUM ORDER QUANTITY
            # =================================================

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
            # ORDER STATUS
            # =================================================

            order_status = determine_order_status(
                review_date,
                expected_delivery,
                end_date
            )

            # =================================================
            # RECEIVED QUANTITY
            # =================================================

            received_quantity = (
                calculate_received_quantity(
                    order_quantity,
                    supplier,
                    order_status
                )
            )

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
                        int(
                            order_quantity
                        ),

                    "received_quantity":
                        int(
                            received_quantity
                        ),

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
                        int(
                            lead_time
                        ),

                    "expected_delivery_date":
                        expected_delivery,

                    "order_status":
                        order_status,
                }
            )

            po_id += 1

    # -----------------------------------------------------
    # Convert to DataFrame
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

    if df.empty:

        print(
            "No purchase orders generated."
        )

        return df

    # -----------------------------------------------------
    # Positive quantities
    # -----------------------------------------------------

    df = df[
        df["ordered_quantity"] > 0
    ]

    # -----------------------------------------------------
    # Received cannot exceed ordered
    # -----------------------------------------------------

    df["received_quantity"] = (
        pd.to_numeric(
            df["received_quantity"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
    )

    df["received_quantity"] = (
        df["received_quantity"]
        .clip(
            lower=0,
            upper=df["ordered_quantity"]
        )
    )

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
    # Pending/In Transit must not have received quantity
    # -----------------------------------------------------

    df.loc[
        df["order_status"].isin(
            [
                "Pending",
                "In Transit"
            ]
        ),
        "received_quantity"
    ] = 0

    # -----------------------------------------------------
    # Received orders must have some receipt
    # -----------------------------------------------------

    received_mask = (
        df["order_status"]
        == "Received"
    )

    df.loc[
        received_mask
        &
        (
            df["received_quantity"]
            <= 0
        ),
        "received_quantity"
    ] = (
        df.loc[
            received_mask
        ]["ordered_quantity"]
        * 0.90
    ).round().astype(int)

    # -----------------------------------------------------
    # Remove duplicate POs
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "po_id"
        ]
    )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    df = df.sort_values(
        by=[
            "order_date",
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

    raw_output = (
        OPERATIONAL_DIR /
        "fact_purchase_orders.csv"
    )

    processed_output = (
        PROCESSED_DIR /
        "fact_purchase_orders.csv"
    )

    # Save operational copy.
    df.to_csv(
        raw_output,
        index=False
    )

    # Save processed copy as well.
    #
    # This keeps the file available to the current
    # MySQL loading pipeline.
    df.to_csv(
        processed_output,
        index=False
    )

    print(
        "\nSaved purchase orders:"
    )

    print(
        raw_output.resolve()
    )

    print(
        processed_output.resolve()
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
    # Generate
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
            "Check inventory levels and demand."
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

    received_units = int(
        df[
            "received_quantity"
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
        f"Received units: "
        f"{received_units:,}"
    )

    print(
        f"PO value: "
        f"Rs. {po_value:,.2f}"
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

    print(
        "\nOrder status distribution:"
    )

    print(
        df[
            "order_status"
        ]
        .value_counts()
    )

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

