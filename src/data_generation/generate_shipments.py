
import random
from pathlib import Path

import numpy as np
import pandas as pd

from supplier_config import SUPPLIER_PROFILES
from shipment_config import (
    SHIPPING_COST_PER_UNIT,
    BASE_COST_PER_SHIPMENT,
)

# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

random.seed(SEED)
np.random.seed(SEED)

PROCESSED_DIR = Path("data/processed")
RAW_OPERATIONAL_DIR = Path("data/raw/operational")

OUTPUT_FILE = PROCESSED_DIR / "fact_shipments.csv"

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\n" + "=" * 70)
    print("LOADING SHIPMENT MASTER DATA")
    print("=" * 70)

    # --------------------------------------------------------
    # Purchase Orders
    # --------------------------------------------------------

    processed_po = (
        PROCESSED_DIR / "fact_purchase_orders.csv"
    )

    raw_po = (
        RAW_OPERATIONAL_DIR / "fact_purchase_orders.csv"
    )

    if processed_po.exists():
        purchase_orders_file = processed_po

    elif raw_po.exists():
        purchase_orders_file = raw_po

    else:
        raise FileNotFoundError(
            "fact_purchase_orders.csv not found in "
            "data/processed or data/raw/operational"
        )

    # --------------------------------------------------------
    # Dimension files
    # --------------------------------------------------------

    supplier_file = (
        PROCESSED_DIR / "dim_supplier.csv"
    )

    warehouse_file = (
        PROCESSED_DIR / "dim_warehouse.csv"
    )

    store_file = (
        PROCESSED_DIR / "dim_store.csv"
    )

    for file_path in [
        supplier_file,
        warehouse_file,
        store_file,
    ]:

        if not file_path.exists():

            raise FileNotFoundError(
                f"Required file not found:\n"
                f"{file_path.resolve()}"
            )

    # --------------------------------------------------------
    # Read
    # --------------------------------------------------------

    purchase_orders = pd.read_csv(
        purchase_orders_file
    )

    suppliers = pd.read_csv(
        supplier_file
    )

    warehouses = pd.read_csv(
        warehouse_file
    )

    stores = pd.read_csv(
        store_file
    )

    print(
        f"Purchase Orders : {len(purchase_orders):,}"
    )

    print(
        f"Suppliers       : {len(suppliers):,}"
    )

    print(
        f"Warehouses      : {len(warehouses):,}"
    )

    print(
        f"Stores          : {len(stores):,}"
    )

    # ========================================================
    # VALIDATE COLUMNS
    # ========================================================

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

    required_store_columns = [
        "store_id",
        "region",
    ]

    for column in required_po_columns:

        if column not in purchase_orders.columns:

            raise ValueError(
                f"Purchase Orders missing column: {column}"
            )

    for column in required_supplier_columns:

        if column not in suppliers.columns:

            raise ValueError(
                f"Suppliers missing column: {column}"
            )

    for column in required_warehouse_columns:

        if column not in warehouses.columns:

            raise ValueError(
                f"Warehouses missing column: {column}"
            )

    for column in required_store_columns:

        if column not in stores.columns:

            raise ValueError(
                f"Stores missing column: {column}"
            )

    # ========================================================
    # CLEAN TYPES
    # ========================================================

    purchase_orders["order_date"] = pd.to_datetime(
        purchase_orders["order_date"],
        errors="coerce"
    )

    purchase_orders["expected_delivery_date"] = pd.to_datetime(
        purchase_orders["expected_delivery_date"],
        errors="coerce"
    )

    purchase_orders["ordered_quantity"] = pd.to_numeric(
        purchase_orders["ordered_quantity"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove invalid POs
    # --------------------------------------------------------

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
        purchase_orders["ordered_quantity"] > 0
    ].copy()

    purchase_orders = purchase_orders.reset_index(
        drop=True
    )

    print(
        f"\nValid Purchase Orders: "
        f"{len(purchase_orders):,}"
    )

    return (
        purchase_orders,
        suppliers,
        warehouses,
        stores,
    )


# ============================================================
# SUPPLIER PROFILE
# ============================================================

def get_supplier_profile(supplier):

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


# ============================================================
# STORE ASSIGNMENT
# ============================================================

def select_store(
    warehouse,
    stores
):
    """
    Select a destination store.

    Priority:
    1. Same-region store
    2. Any available store
    """

    warehouse_region = warehouse["region"]

    regional_stores = stores[
        stores["region"] == warehouse_region
    ]

    if not regional_stores.empty:

        store = regional_stores.sample(
            n=1,
            random_state=random.randint(
                1,
                1_000_000
            )
        ).iloc[0]

    else:

        store = stores.sample(
            n=1,
            random_state=random.randint(
                1,
                1_000_000
            )
        ).iloc[0]

    return store


# ============================================================
# SHIPPING REGION
# ============================================================

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

    if supplier_region == warehouse_region:

        return "Local"

    regional_pairs = {
        ("West", "North"),
        ("West", "South"),
        ("West", "East"),

        ("North", "West"),
        ("North", "South"),

        ("South", "West"),
        ("South", "North"),

        ("East", "West"),
        ("East", "North"),
    }

    if (
        supplier_region,
        warehouse_region
    ) in regional_pairs:

        return "Regional"

    return "National"


# ============================================================
# SHIPPED QUANTITY
# ============================================================

def calculate_shipped_quantity(
    ordered_quantity,
    fill_rate
):

    adjusted_fill_rate = np.random.normal(
        fill_rate,
        0.02
    )

    adjusted_fill_rate = max(
        0.75,
        min(
            adjusted_fill_rate,
            1.00
        )
    )

    quantity = int(
        round(
            ordered_quantity
            * adjusted_fill_rate
        )
    )

    quantity = max(
        1,
        quantity
    )

    return min(
        quantity,
        int(ordered_quantity)
    )


# ============================================================
# DELIVERY DATE
# ============================================================

def calculate_actual_delivery(
    expected_delivery,
    profile
):

    actual_delivery = expected_delivery

    late = False

    if random.random() < profile["late_probability"]:

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


# ============================================================
# DAMAGE
# ============================================================

def calculate_damage(
    quantity_shipped,
    damage_rate
):

    damage_std = max(
        damage_rate * 0.25,
        0.0001
    )

    actual_damage_rate = np.random.normal(
        damage_rate,
        damage_std
    )

    actual_damage_rate = max(
        0,
        actual_damage_rate
    )

    damaged_units = int(
        round(
            quantity_shipped
            * actual_damage_rate
        )
    )

    return min(
        max(
            damaged_units,
            0
        ),
        quantity_shipped
    )


# ============================================================
# GENERATE SHIPMENTS
# ============================================================

def generate_shipments():

    (
        purchase_orders,
        suppliers,
        warehouses,
        stores,
    ) = load_data()

    records = []

    shipment_number = 1

    skipped_supplier = 0
    skipped_warehouse = 0

    print(
        "\nGenerating shipments..."
    )

    # ========================================================
    # PROCESS EVERY PURCHASE ORDER
    # ========================================================

    for po in purchase_orders.itertuples(
        index=False
    ):

        # ----------------------------------------------------
        # Supplier
        # ----------------------------------------------------

        supplier_match = suppliers[
            suppliers["supplier_id"]
            == po.supplier_id
        ]

        if supplier_match.empty:

            skipped_supplier += 1

            continue

        supplier = (
            supplier_match
            .iloc[0]
        )

        # ----------------------------------------------------
        # Warehouse
        # ----------------------------------------------------

        warehouse_match = warehouses[
            warehouses["warehouse_id"]
            == po.warehouse_id
        ]

        if warehouse_match.empty:

            skipped_warehouse += 1

            continue

        warehouse = (
            warehouse_match
            .iloc[0]
        )

        # ----------------------------------------------------
        # Supplier performance profile
        # ----------------------------------------------------

        profile = get_supplier_profile(
            supplier
        )

        # ----------------------------------------------------
        # Destination store
        # ----------------------------------------------------

        store = select_store(
            warehouse,
            stores
        )

        store_id = store[
            "store_id"
        ]

        # ====================================================
        # QUANTITY SHIPPED
        # ====================================================

        # Most orders should be fulfilled close to the
        # supplier's normal fill-rate performance.
        #
        # A smaller percentage of orders are fulfilled
        # completely, allowing realistic OTIF performance.

        if random.random() < profile.get(
            "full_fill_probability",
            0.25
        ):

            quantity_shipped = int(
                po.ordered_quantity
            )

        else:

            quantity_shipped = (
                calculate_shipped_quantity(
                    po.ordered_quantity,
                    profile["fill_rate"]
                )
            )

        # ====================================================
        # DELIVERY
        # ====================================================

        (
            actual_delivery,
            late_flag
        ) = calculate_actual_delivery(
            po.expected_delivery_date,
            profile
        )

        # ====================================================
        # DAMAGE
        # ====================================================

        damage_units = (
            calculate_damage(
                quantity_shipped,
                profile["damage_rate"]
            )
        )

        # ====================================================
        # DELIVERED
        # ====================================================

        quantity_delivered = max(
            quantity_shipped
            - damage_units,
            0
        )

        # ====================================================
        # SHIPPING REGION
        # ====================================================

        shipping_region = (
            determine_shipping_region(
                supplier,
                warehouse
            )
        )

        # ====================================================
        # SHIPPING COST
        # ====================================================

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

        # ====================================================
        # DELIVERY DELAY
        # ====================================================

        delivery_delay_days = max(
            (
                actual_delivery
                -
                po.expected_delivery_date
            ).days,
            0
        )

        # ====================================================
        # FILL RATE
        # ====================================================

        if po.ordered_quantity > 0:

            fill_rate = (
                quantity_delivered
                /
                po.ordered_quantity
            )

        else:

            fill_rate = 0.0

        # ====================================================
        # ON TIME
        # ====================================================

        on_time = (
            actual_delivery
            <=
            po.expected_delivery_date
        )

        # ====================================================
        # IN FULL
        # ====================================================

        in_full = (
            quantity_delivered
            >=
            po.ordered_quantity
        )

        # ====================================================
        # OTIF
        # ====================================================

        otif_flag = int(
            on_time
            and
            in_full
        )

        # ====================================================
        # DAMAGE RATE
        # ====================================================

        if quantity_shipped > 0:

            damage_rate = (
                damage_units
                /
                quantity_shipped
            )

        else:

            damage_rate = 0.0

        # ====================================================
        # LATE SHIPMENT FLAG
        # ====================================================

        late_shipment_flag = int(
            not on_time
        )

        # ====================================================
        # RECORD
        # ====================================================

        records.append(
            {
                "shipment_id":
                    f"SH{shipment_number:09d}",

                "po_id":
                    po.po_id,

                "supplier_id":
                    po.supplier_id,

                "product_id":
                    po.product_id,

                "warehouse_id":
                    po.warehouse_id,

                "store_id":
                    store_id,

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

                "damage_rate":
                    round(
                        damage_rate,
                        4
                    ),

                "late_shipment_flag":
                    late_shipment_flag,
            }
        )

        shipment_number += 1

    # ========================================================
    # DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        records
    )

    print(
        f"\nShipments generated: "
        f"{len(df):,}"
    )

    print(
        f"Skipped - Supplier: "
        f"{skipped_supplier:,}"
    )

    print(
        f"Skipped - Warehouse: "
        f"{skipped_warehouse:,}"
    )

    return df


# ============================================================
# VALIDATION
# ============================================================

def validate_shipments(df):

    print(
        "\nValidating shipment data..."
    )

    if df.empty:

        raise ValueError(
            "No shipments were generated."
        )

    # --------------------------------------------------------
    # Shipment ID uniqueness
    # --------------------------------------------------------

    duplicate_ids = (
        df["shipment_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate shipment IDs: "
        f"{duplicate_ids}"
    )

    # --------------------------------------------------------
    # Shipped <= Ordered
    # --------------------------------------------------------

    violations = (
        df["quantity_shipped"]
        >
        df["ordered_quantity"]
    ).sum()

    print(
        f"Shipped > Ordered violations: "
        f"{violations}"
    )

    # --------------------------------------------------------
    # Delivered <= Shipped
    # --------------------------------------------------------

    violations = (
        df["quantity_delivered"]
        >
        df["quantity_shipped"]
    ).sum()

    print(
        f"Delivered > Shipped violations: "
        f"{violations}"
    )

    # --------------------------------------------------------
    # Damage <= Shipped
    # --------------------------------------------------------

    violations = (
        df["damage_units"]
        >
        df["quantity_shipped"]
    ).sum()

    print(
        f"Damage > Shipped violations: "
        f"{violations}"
    )

    # --------------------------------------------------------
    # Delivery date
    # --------------------------------------------------------

    df["shipment_date"] = pd.to_datetime(
        df["shipment_date"],
        errors="coerce"
    )

    df["expected_delivery_date"] = pd.to_datetime(
        df["expected_delivery_date"],
        errors="coerce"
    )

    df["actual_delivery_date"] = pd.to_datetime(
        df["actual_delivery_date"],
        errors="coerce"
    )

    violations = (
        df["actual_delivery_date"]
        <
        df["shipment_date"]
    ).sum()

    print(
        f"Invalid delivery dates: "
        f"{violations}"
    )

    # --------------------------------------------------------
    # Fill rate
    # --------------------------------------------------------

    calculated_fill_rate = (
        df["quantity_delivered"]
        /
        df["ordered_quantity"]
    )

    fill_rate_difference = (
        calculated_fill_rate
        -
        df["fill_rate"]
    ).abs()

    violations = (
        fill_rate_difference > 0.01
    ).sum()

    print(
        f"Fill rate violations: "
        f"{violations}"
    )

    # --------------------------------------------------------
    # OTIF validation
    # --------------------------------------------------------

    calculated_otif = (
        (
            df["actual_delivery_date"]
            <=
            df["expected_delivery_date"]
        )
        &
        (
            df["quantity_delivered"]
            >=
            df["ordered_quantity"]
        )
    ).astype(int)

    violations = (
        calculated_otif
        !=
        df["otif_flag"]
    ).sum()

    print(
        f"OTIF violations: "
        f"{violations}"
    )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    if duplicate_ids > 0:

        raise ValueError(
            "Duplicate shipment IDs detected."
        )

    # --------------------------------------------------------
    # Hard validation
    # --------------------------------------------------------

    if (
        df["quantity_shipped"]
        >
        df["ordered_quantity"]
    ).any():

        raise ValueError(
            "Some shipments have shipped quantity "
            "greater than ordered quantity."
        )

    if (
        df["quantity_delivered"]
        >
        df["quantity_shipped"]
    ).any():

        raise ValueError(
            "Some shipments have delivered quantity "
            "greater than shipped quantity."
        )

    return df


# ============================================================
# SAVE
# ============================================================

def save_shipments(df):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Convert dates
    # --------------------------------------------------------

    date_columns = [
        "shipment_date",
        "expected_delivery_date",
        "actual_delivery_date",
    ]

    for column in date_columns:

        df[column] = pd.to_datetime(
            df[column]
        ).dt.strftime(
            "%Y-%m-%d"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nSaved shipment data to:"
    )

    print(
        OUTPUT_FILE.resolve()
    )

    print(
        f"Rows saved: "
        f"{len(df):,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n" + "=" * 70
    )

    print(
        "FMCG SUPPLY CHAIN - SHIPMENT GENERATOR"
    )

    print(
        "=" * 70
    )

    df = generate_shipments()

    df = validate_shipments(
        df
    )

    save_shipments(
        df
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "SHIPMENT SUMMARY"
    )

    print(
        "=" * 70
    )

    ordered_units = int(
        df["ordered_quantity"].sum()
    )

    shipped_units = int(
        df["quantity_shipped"].sum()
    )

    delivered_units = int(
        df["quantity_delivered"].sum()
    )

    damaged_units = int(
        df["damage_units"].sum()
    )

    shipping_cost = float(
        df["shipping_cost"].sum()
    )

    avg_fill_rate = (
        df["fill_rate"].mean()
        * 100
    )

    otif_percentage = (
        df["otif_flag"].mean()
        * 100
    )

    late_percentage = (
        df["late_shipment_flag"].mean()
        * 100
    )

    damage_percentage = (
        df["damage_rate"].mean()
        * 100
    )

    print(
        f"Purchase Orders : {len(df):,}"
    )

    print(
        f"Ordered Units   : {ordered_units:,}"
    )

    print(
        f"Shipped Units   : {shipped_units:,}"
    )

    print(
        f"Delivered Units : {delivered_units:,}"
    )

    print(
        f"Damaged Units   : {damaged_units:,}"
    )

    print(
        f"Shipping Cost   : Rs {shipping_cost:,.2f}"
    )

    print(
        f"Average Fill Rate: {avg_fill_rate:.2f}%"
    )

    print(
        f"OTIF            : {otif_percentage:.2f}%"
    )

    print(
        f"Late Shipments  : {late_percentage:.2f}%"
    )

    print(
        f"Damage Rate     : {damage_percentage:.2f}%"
    )

    print(
        "\nShipment generation completed successfully."
    )


if __name__ == "__main__":
    main()

