import random
from pathlib import Path

import numpy as np
import pandas as pd

from supplier_config import SUPPLIER_PROFILES

from shipment_config import (
    SHIPPING_COST_PER_UNIT,
    BASE_COST_PER_SHIPMENT,
)


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
        "\nLoading shipment master data..."
    )

    purchase_orders_file = (
        OPERATIONAL_DIR
        / "fact_purchase_orders.csv"
    )

    suppliers_file = (
        PROCESSED_DIR
        / "dim_supplier.csv"
    )

    warehouses_file = (
        PROCESSED_DIR
        / "dim_warehouse.csv"
    )

    # -----------------------------------------------------
    # Check required files
    # -----------------------------------------------------

    required_files = {
        "Purchase Orders": purchase_orders_file,
        "Suppliers": suppliers_file,
        "Warehouses": warehouses_file,
    }

    for name, file_path in required_files.items():

        if not file_path.exists():

            raise FileNotFoundError(
                f"\nRequired {name.lower()} file not found:\n"
                f"{file_path.resolve()}\n\n"
                f"Please generate the required data first."
            )

    # -----------------------------------------------------
    # Read files
    # -----------------------------------------------------

    purchase_orders = pd.read_csv(
        purchase_orders_file
    )

    suppliers = pd.read_csv(
        suppliers_file
    )

    warehouses = pd.read_csv(
        warehouses_file
    )

    # -----------------------------------------------------
    # Validate required columns
    # -----------------------------------------------------

    required_po_columns = [
        "po_id",
        "supplier_id",
        "product_id",
        "warehouse_id",
        "order_date",
        "expected_delivery_date",
        "ordered_quantity",
    ]

    required_supplier_columns = [
        "supplier_id",
        "supplier_region",
        "performance_tier",
    ]

    required_warehouse_columns = [
        "warehouse_id",
        "region",
    ]

    missing_po_columns = [
        column
        for column in required_po_columns
        if column not in purchase_orders.columns
    ]

    missing_supplier_columns = [
        column
        for column in required_supplier_columns
        if column not in suppliers.columns
    ]

    missing_warehouse_columns = [
        column
        for column in required_warehouse_columns
        if column not in warehouses.columns
    ]

    if missing_po_columns:

        raise ValueError(
            "Missing columns in fact_purchase_orders.csv: "
            + ", ".join(missing_po_columns)
        )

    if missing_supplier_columns:

        raise ValueError(
            "Missing columns in dim_supplier.csv: "
            + ", ".join(missing_supplier_columns)
        )

    if missing_warehouse_columns:

        raise ValueError(
            "Missing columns in dim_warehouse.csv: "
            + ", ".join(missing_warehouse_columns)
        )

    # -----------------------------------------------------
    # Convert dates
    # -----------------------------------------------------

    purchase_orders["order_date"] = (
        pd.to_datetime(
            purchase_orders["order_date"],
            errors="coerce"
        )
    )

    purchase_orders[
        "expected_delivery_date"
    ] = pd.to_datetime(
        purchase_orders[
            "expected_delivery_date"
        ],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Convert quantities
    # -----------------------------------------------------

    purchase_orders[
        "ordered_quantity"
    ] = pd.to_numeric(
        purchase_orders[
            "ordered_quantity"
        ],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Remove invalid records
    # -----------------------------------------------------

    purchase_orders = purchase_orders.dropna(
        subset=[
            "po_id",
            "supplier_id",
            "product_id",
            "warehouse_id",
            "order_date",
            "expected_delivery_date",
            "ordered_quantity",
        ]
    )

    purchase_orders = purchase_orders[
        purchase_orders[
            "ordered_quantity"
        ] > 0
    ].reset_index(
        drop=True
    )

    suppliers = suppliers.dropna(
        subset=[
            "supplier_id",
            "supplier_region",
            "performance_tier",
        ]
    ).reset_index(
        drop=True
    )

    warehouses = warehouses.dropna(
        subset=[
            "warehouse_id",
            "region",
        ]
    ).reset_index(
        drop=True
    )

    # -----------------------------------------------------
    # Print summary
    # -----------------------------------------------------

    print(
        f"Purchase Orders : {len(purchase_orders):,}"
    )

    print(
        f"Suppliers       : {len(suppliers):,}"
    )

    print(
        f"Warehouses      : {len(warehouses):,}"
    )

    return (
        purchase_orders,
        suppliers,
        warehouses,
    )


# =========================================================
# SUPPLIER PROFILE
# =========================================================

def get_supplier_profile(
    supplier
):

    performance_tier = supplier[
        "performance_tier"
    ]

    if performance_tier not in SUPPLIER_PROFILES:

        raise ValueError(
            f"Unknown supplier performance tier: "
            f"{performance_tier}"
        )

    return SUPPLIER_PROFILES[
        performance_tier
    ]


# =========================================================
# SHIPPING REGION
# =========================================================

def determine_shipping_region(
    supplier,
    warehouse
):

    supplier_region = supplier[
        "supplier_region"
    ]

    warehouse_region = warehouse[
        "region"
    ]

    # -----------------------------------------------------
    # Same region
    # -----------------------------------------------------

    if supplier_region == warehouse_region:

        return "Local"

    # -----------------------------------------------------
    # Regional movement
    # -----------------------------------------------------

    regional_pairs = {
        ("West", "North"),
        ("West", "South"),
        ("West", "East"),

        ("North", "West"),
        ("South", "West"),
        ("East", "West"),
    }

    if (
        supplier_region,
        warehouse_region
    ) in regional_pairs:

        return "Regional"

    # -----------------------------------------------------
    # National movement
    # -----------------------------------------------------

    return "National"


# =========================================================
# SHIPPED QUANTITY
# =========================================================

def calculate_shipped_quantity(
    ordered_quantity,
    fill_rate
):

    quantity = (
        ordered_quantity
        * np.random.normal(
            fill_rate,
            0.02
        )
    )

    quantity = int(
        round(
            max(
                0,
                quantity
            )
        )
    )

    return min(
        quantity,
        int(ordered_quantity)
    )


# =========================================================
# ACTUAL DELIVERY DATE
# =========================================================

def calculate_actual_delivery(
    expected_delivery,
    profile
):

    actual_delivery = (
        expected_delivery
    )

    late = False

    # -----------------------------------------------------
    # Late delivery
    # -----------------------------------------------------

    if (
        random.random()
        < profile["late_probability"]
    ):

        delay_days = random.randint(
            1,
            5
        )

        actual_delivery = (
            expected_delivery
            +
            pd.Timedelta(
                days=delay_days
            )
        )

        late = True

    return (
        actual_delivery,
        late
    )


# =========================================================
# DAMAGE
# =========================================================

def calculate_damage(
    quantity_shipped,
    damage_rate
):

    # Prevent invalid standard deviation
    damage_std = max(
        damage_rate * 0.25,
        0.0001
    )

    damaged_units = int(
        round(
            quantity_shipped
            * np.random.normal(
                damage_rate,
                damage_std
            )
        )
    )

    damaged_units = max(
        0,
        damaged_units
    )

    return min(
        damaged_units,
        quantity_shipped
    )


# =========================================================
# GENERATE SHIPMENTS
# =========================================================

def generate_shipments():

    (
        purchase_orders,
        suppliers,
        warehouses,
    ) = load_data()

    records = []

    shipment_id = 1

    # -----------------------------------------------------
    # Process each purchase order
    # -----------------------------------------------------

    for po in purchase_orders.itertuples(
        index=False
    ):

        # -------------------------------------------------
        # Find supplier
        # -------------------------------------------------

        supplier_match = suppliers[
            suppliers[
                "supplier_id"
            ]
            == po.supplier_id
        ]

        # -------------------------------------------------
        # Find warehouse
        # -------------------------------------------------

        warehouse_match = warehouses[
            warehouses[
                "warehouse_id"
            ]
            == po.warehouse_id
        ]

        if supplier_match.empty:

            continue

        if warehouse_match.empty:

            continue

        # -------------------------------------------------
        # Extract records
        # -------------------------------------------------

        supplier = (
            supplier_match
            .iloc[0]
        )

        warehouse = (
            warehouse_match
            .iloc[0]
        )

        # -------------------------------------------------
        # Supplier profile
        # -------------------------------------------------

        profile = get_supplier_profile(
            supplier
        )

        # =================================================
        # QUANTITY SHIPPED
        # =================================================

        quantity_shipped = (
            calculate_shipped_quantity(
                po.ordered_quantity,
                profile["fill_rate"]
            )
        )

        # =================================================
        # ACTUAL DELIVERY
        # =================================================

        (
            actual_delivery,
            late_flag
        ) = calculate_actual_delivery(
            po.expected_delivery_date,
            profile
        )

        # =================================================
        # DAMAGE
        # =================================================

        damage_units = (
            calculate_damage(
                quantity_shipped,
                profile["damage_rate"]
            )
        )

        # =================================================
        # QUANTITY DELIVERED
        # =================================================

        quantity_delivered = max(
            quantity_shipped
            - damage_units,
            0
        )

        # =================================================
        # SHIPPING REGION
        # =================================================

        shipping_region = (
            determine_shipping_region(
                supplier,
                warehouse
            )
        )

        # =================================================
        # SHIPPING COST
        # =================================================

        cost_per_unit = (
            SHIPPING_COST_PER_UNIT[
                shipping_region
            ]
        )

        shipping_cost = (
            BASE_COST_PER_SHIPMENT
            +
            quantity_shipped
            * cost_per_unit
        )

        # =================================================
        # DELIVERY DELAY
        # =================================================

        delivery_delay_days = max(
            (
                actual_delivery
                -
                po.expected_delivery_date
            ).days,
            0
        )

        # =================================================
        # FILL RATE
        # =================================================

        if po.ordered_quantity > 0:

            fill_rate = (
                quantity_delivered
                /
                po.ordered_quantity
            )

        else:

            fill_rate = 0.0

        # =================================================
        # ON TIME
        # =================================================

        on_time = (
            actual_delivery
            <=
            po.expected_delivery_date
        )

        # =================================================
        # IN FULL
        # =================================================

        in_full = (
            quantity_delivered
            >=
            po.ordered_quantity
        )

        # =================================================
        # OTIF
        # =================================================

        otif_flag = int(
            on_time
            and
            in_full
        )

        # =================================================
        # RECORD
        # =================================================

        records.append(
            {
                "shipment_id":
                    f"SH{shipment_id:09d}",

                "po_id":
                    po.po_id,

                "supplier_id":
                    po.supplier_id,

                "product_id":
                    po.product_id,

                "warehouse_id":
                    po.warehouse_id,

                "shipment_date":
                    po.order_date,

                "expected_delivery_date":
                    po.expected_delivery_date,

                "actual_delivery_date":
                    actual_delivery,

                "ordered_quantity":
                    int(
                        po.ordered_quantity
                    ),

                "quantity_shipped":
                    quantity_shipped,

                "quantity_delivered":
                    quantity_delivered,

                "damage_units":
                    damage_units,

                "delivery_delay_days":
                    delivery_delay_days,

                "fill_rate":
                    round(
                        fill_rate,
                        4
                    ),

                "on_time_flag":
                    int(on_time),

                "in_full_flag":
                    int(in_full),

                "otif_flag":
                    otif_flag,

                "shipping_region":
                    shipping_region,

                "shipping_cost":
                    round(
                        shipping_cost,
                        2
                    ),
            }
        )

        shipment_id += 1

    # -----------------------------------------------------
    # Convert to DataFrame
    # -----------------------------------------------------

    return pd.DataFrame(
        records
    )


# =========================================================
# VALIDATION
# =========================================================

def validate_shipments(
    df
):

    print(
        "\nValidating shipments..."
    )

    # -----------------------------------------------------
    # Empty dataset
    # -----------------------------------------------------

    if df.empty:

        print(
            "No shipment records generated."
        )

        return df

    # -----------------------------------------------------
    # Shipped cannot exceed ordered
    # -----------------------------------------------------

    violations = (
        df[
            "quantity_shipped"
        ]
        >
        df[
            "ordered_quantity"
        ]
    ).sum()

    print(
        f"Quantity violations: "
        f"{violations:,}"
    )

    # -----------------------------------------------------
    # Delivered cannot exceed shipped
    # -----------------------------------------------------

    violations = (
        df[
            "quantity_delivered"
        ]
        >
        df[
            "quantity_shipped"
        ]
    ).sum()

    print(
        f"Delivery violations: "
        f"{violations:,}"
    )

    # -----------------------------------------------------
    # Damage cannot exceed shipped
    # -----------------------------------------------------

    violations = (
        df[
            "damage_units"
        ]
        >
        df[
            "quantity_shipped"
        ]
    ).sum()

    print(
        f"Damage violations: "
        f"{violations:,}"
    )

    # -----------------------------------------------------
    # Convert dates
    # -----------------------------------------------------

    df["shipment_date"] = (
        pd.to_datetime(
            df["shipment_date"],
            errors="coerce"
        )
    )

    df["actual_delivery_date"] = (
        pd.to_datetime(
            df["actual_delivery_date"],
            errors="coerce"
        )
    )

    # -----------------------------------------------------
    # Delivery date validation
    # -----------------------------------------------------

    violations = (
        df[
            "actual_delivery_date"
        ]
        <
        df[
            "shipment_date"
        ]
    ).sum()

    print(
        f"Date violations: "
        f"{violations:,}"
    )

    # -----------------------------------------------------
    # Remove invalid records
    # -----------------------------------------------------

    df = df[
        df["quantity_shipped"]
        <=
        df["ordered_quantity"]
    ]

    df = df[
        df["quantity_delivered"]
        <=
        df["quantity_shipped"]
    ]

    df = df[
        df["damage_units"]
        <=
        df["quantity_shipped"]
    ]

    # -----------------------------------------------------
    # Remove duplicate shipments
    # -----------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "shipment_id"
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

def save_shipments(
    df
):

    output_file = (
        OPERATIONAL_DIR
        /
        "fact_shipments.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "\nSaved shipments:"
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
        "FMCG SHIPMENT / LOGISTICS ENGINE"
    )

    print(
        "=" * 60
    )

    # -----------------------------------------------------
    # Generate
    # -----------------------------------------------------

    df = generate_shipments()

    print(
        f"\nGenerated shipments: "
        f"{len(df):,}"
    )

    # -----------------------------------------------------
    # Handle no shipments
    # -----------------------------------------------------

    if df.empty:

        print(
            "\nNo shipments were generated."
        )

        print(
            "Check fact_purchase_orders.csv "
            "and supplier configuration."
        )

        return

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    df = validate_shipments(
        df
    )

    print(
        f"\nValid shipments: "
        f"{len(df):,}"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_shipments(
        df
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    print(
        "\nShipment summary:"
    )

    ordered_units = int(
        df[
            "ordered_quantity"
        ].sum()
    )

    shipped_units = int(
        df[
            "quantity_shipped"
        ].sum()
    )

    delivered_units = int(
        df[
            "quantity_delivered"
        ].sum()
    )

    damaged_units = int(
        df[
            "damage_units"
        ].sum()
    )

    shipping_cost = float(
        df[
            "shipping_cost"
        ].sum()
    )

    otif_percentage = float(
        df[
            "otif_flag"
        ].mean()
        * 100
    )

    fill_rate_percentage = float(
        df[
            "fill_rate"
        ].mean()
        * 100
    )

    late_percentage = float(
        (
            1
            -
            df[
                "on_time_flag"
            ].mean()
        )
        * 100
    )

    print(
        f"Ordered: "
        f"{ordered_units:,}"
    )

    print(
        f"Shipped: "
        f"{shipped_units:,}"
    )

    print(
        f"Delivered: "
        f"{delivered_units:,}"
    )

    print(
        f"Damaged: "
        f"{damaged_units:,}"
    )

    print(
        f"Shipping cost: "
        f"₹{shipping_cost:,.2f}"
    )

    print(
        f"OTIF: "
        f"{otif_percentage:.2f}%"
    )

    print(
        f"Fill Rate: "
        f"{fill_rate_percentage:.2f}%"
    )

    print(
        f"Late Shipments: "
        f"{late_percentage:.2f}%"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()