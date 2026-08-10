from pathlib import Path

import pandas as pd

from data_quality import (
    check_nulls,
    check_duplicates,
    check_negative_values,
    check_range,
    check_foreign_key,
    save_quality_report,
)


RAW_DIR = Path(
    "data/raw/operational"
)

PROCESSED_DIR = Path(
    "data/processed"
)


# ---------------------------------------------------------
# LOAD TABLE
# ---------------------------------------------------------

def load_table(
    filename
):

    filepath = (
        RAW_DIR /
        filename
    )

    print(
        f"Loading: {filepath}"
    )

    return pd.read_csv(
        filepath
    )


# ---------------------------------------------------------
# CLEAN COLUMN NAMES
# ---------------------------------------------------------

def clean_column_names(
    df
):

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(
            " ",
            "_"
        )
    )

    return df


# ---------------------------------------------------------
# CLEAN NUMERIC COLUMNS
# ---------------------------------------------------------

def clean_numeric_columns(
    df,
    columns
):

    df = df.copy()

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# ---------------------------------------------------------
# CLEAN DATES
# ---------------------------------------------------------

def clean_date_columns(
    df,
    columns
):

    df = df.copy()

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    return df


# ---------------------------------------------------------
# REMOVE DUPLICATES
# ---------------------------------------------------------

def remove_duplicates(
    df,
    key
):

    if key not in df.columns:

        return df

    before = len(df)

    df = (
        df
        .drop_duplicates(
            subset=[key]
        )
        .copy()
    )

    after = len(df)

    print(
        f"{key}: removed "
        f"{before - after:,} duplicates"
    )

    return df


# ---------------------------------------------------------
# PROCESS SALES
# ---------------------------------------------------------

def process_sales():

    df = load_table(
        "fact_sales.csv"
    )

    df = clean_column_names(
        df
    )

    df = clean_numeric_columns(
        df,
        [
            "quantity_sold",
            "unit_price",
            "discount",
            "sales_amount",
        ]
    )

    df = clean_date_columns(
        df,
        ["date"]
    )

    df = remove_duplicates(
        df,
        "sale_id"
    )

    return df


# ---------------------------------------------------------
# PROCESS INVENTORY
# ---------------------------------------------------------

def process_inventory():

    df = load_table(
        "fact_inventory.csv"
    )

    df = clean_column_names(
        df
    )

    df = clean_numeric_columns(
        df,
        [
            "opening_stock",
            "demand_units",
            "received_units",
            "sold_units",
            "closing_stock",
            "damaged_units",
            "expired_units",
            "stockout_units",
        ]
    )

    df = clean_date_columns(
        df,
        ["date"]
    )

    df = remove_duplicates(
        df,
        "inventory_id"
    )

    return df


# ---------------------------------------------------------
# PROCESS PURCHASE ORDERS
# ---------------------------------------------------------

def process_purchase_orders():

    df = load_table(
        "fact_purchase_orders.csv"
    )

    df = clean_column_names(
        df
    )

    df = clean_numeric_columns(
        df,
        [
            "ordered_quantity",
            "received_quantity",
            "unit_cost",
        ]
    )

    df = clean_date_columns(
        df,
        [
            "order_date",
            "expected_delivery_date",
        ]
    )

    df = remove_duplicates(
        df,
        "po_id"
    )

    return df


# ---------------------------------------------------------
# PROCESS SHIPMENTS
# ---------------------------------------------------------

def process_shipments():

    df = load_table(
        "fact_shipments.csv"
    )

    df = clean_column_names(
        df
    )

    df = clean_numeric_columns(
        df,
        [
            "ordered_quantity",
            "quantity_shipped",
            "quantity_delivered",
            "damage_units",
            "delivery_delay_days",
            "fill_rate",
            "shipping_cost",
        ]
    )

    df = clean_date_columns(
        df,
        [
            "shipment_date",
            "expected_delivery_date",
            "actual_delivery_date",
        ]
    )

    df = remove_duplicates(
        df,
        "shipment_id"
    )

    return df


# ---------------------------------------------------------
# PROCESS AGING
# ---------------------------------------------------------

def process_inventory_aging():

    df = load_table(
        "fact_inventory_aging.csv"
    )

    df = clean_column_names(
        df
    )

    df = clean_numeric_columns(
        df,
        [
            "received_units",
            "remaining_units",
            "unit_cost",
            "shelf_life_days",
            "age_days",
            "remaining_shelf_life_days",
            "inventory_value",
            "expiry_risk_value",
        ]
    )

    df = clean_date_columns(
        df,
        [
            "receipt_date",
            "expiry_date",
            "analysis_date",
        ]
    )

    df = remove_duplicates(
        df,
        "lot_id"
    )

    return df


# ---------------------------------------------------------
# DATA QUALITY
# ---------------------------------------------------------

def run_quality_checks(
    sales,
    inventory,
    purchase_orders,
    shipments,
    aging,
):

    results = []

    # -----------------------------------------------------
    # Sales
    # -----------------------------------------------------

    results += check_nulls(
        sales,
        "fact_sales"
    )

    results += check_duplicates(
        sales,
        "fact_sales",
        "sale_id"
    )

    results += check_negative_values(
        sales,
        "fact_sales",
        [
            "quantity_sold",
            "sales_amount",
        ]
    )

    results += check_range(
        sales,
        "fact_sales",
        "discount",
        minimum=0,
        maximum=1
    )

    # -----------------------------------------------------
    # Inventory
    # -----------------------------------------------------

    results += check_nulls(
        inventory,
        "fact_inventory"
    )

    results += check_duplicates(
        inventory,
        "fact_inventory",
        "inventory_id"
    )

    results += check_negative_values(
        inventory,
        "fact_inventory",
        [
            "opening_stock",
            "received_units",
            "sold_units",
            "closing_stock",
            "damaged_units",
            "expired_units",
            "stockout_units",
        ]
    )

    # -----------------------------------------------------
    # Purchase Orders
    # -----------------------------------------------------

    results += check_nulls(
        purchase_orders,
        "fact_purchase_orders"
    )

    results += check_duplicates(
        purchase_orders,
        "fact_purchase_orders",
        "po_id"
    )

    results += check_negative_values(
        purchase_orders,
        "fact_purchase_orders",
        [
            "ordered_quantity",
            "received_quantity",
            "unit_cost",
        ]
    )

    # -----------------------------------------------------
    # Shipments
    # -----------------------------------------------------

    results += check_nulls(
        shipments,
        "fact_shipments"
    )

    results += check_duplicates(
        shipments,
        "fact_shipments",
        "shipment_id"
    )

    results += check_negative_values(
        shipments,
        "fact_shipments",
        [
            "quantity_shipped",
            "quantity_delivered",
            "damage_units",
            "shipping_cost",
        ]
    )

    results += check_range(
        shipments,
        "fact_shipments",
        "fill_rate",
        minimum=0,
        maximum=1
    )

    # -----------------------------------------------------
    # Inventory Aging
    # -----------------------------------------------------

    results += check_nulls(
        aging,
        "fact_inventory_aging"
    )

    results += check_duplicates(
        aging,
        "fact_inventory_aging",
        "lot_id"
    )

    results += check_negative_values(
        aging,
        "fact_inventory_aging",
        [
            "remaining_units",
            "inventory_value",
        ]
    )

    # -----------------------------------------------------
    # Referential integrity
    # -----------------------------------------------------

    results += check_foreign_key(
        shipments,
        purchase_orders,
        "po_id",
        "po_id",
        "fact_shipments"
    )

    return results


# ---------------------------------------------------------
# SAVE PROCESSED DATA
# ---------------------------------------------------------

def save_processed(
    df,
    filename
):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = (
        PROCESSED_DIR /
        filename
    )

    df.to_csv(
        output,
        index=False
    )

    print(
        f"Saved: {output}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 70)

    print(
        "FMCG PYTHON ETL PIPELINE"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # Extract
    # -----------------------------------------------------

    print(
        "\n[1/4] EXTRACT"
    )

    sales = process_sales()

    inventory = process_inventory()

    purchase_orders = (
        process_purchase_orders()
    )

    shipments = process_shipments()

    aging = (
        process_inventory_aging()
    )

    # -----------------------------------------------------
    # Quality
    # -----------------------------------------------------

    print(
        "\n[2/4] DATA QUALITY"
    )

    quality_results = (
        run_quality_checks(
            sales,
            inventory,
            purchase_orders,
            shipments,
            aging,
        )
    )

    quality_file = (
        save_quality_report(
            quality_results
        )
    )

    print(
        f"Quality report: "
        f"{quality_file}"
    )

    # -----------------------------------------------------
    # Transform
    # -----------------------------------------------------

    print(
        "\n[3/4] TRANSFORM"
    )

    # Sales metrics

    sales["revenue"] = (
        sales["sales_amount"]
    )

    sales["gross_sales"] = (
        sales["quantity_sold"]
        *
        sales["unit_price"]
    )

    # Inventory metrics

    inventory["inventory_value"] = (
        inventory["closing_stock"]
        *
        1.0
    )

    inventory["stockout_rate"] = np_where(
        inventory["demand_units"] > 0,
        inventory["stockout_units"]
        /
        inventory["demand_units"],
        0
    )

    # Shipment metrics

    shipments["damage_rate"] = np_where(
        shipments["quantity_shipped"] > 0,
        shipments["damage_units"]
        /
        shipments["quantity_shipped"],
        0
    )

    shipments["late_shipment_flag"] = (
        shipments["on_time_flag"]
        == 0
    ).astype(int)

    # Aging metrics

    aging["inventory_value"] = (
        aging["remaining_units"]
        *
        aging["unit_cost"]
    )

    aging["expiry_risk_flag"] = (
        aging["expiry_risk"]
        .isin(
            [
                "CRITICAL",
                "HIGH",
                "EXPIRED",
            ]
        )
        .astype(int)
    )

    # -----------------------------------------------------
    # Load processed data
    # -----------------------------------------------------

    print(
        "\n[4/4] LOAD"
    )

    save_processed(
        sales,
        "fact_sales.csv"
    )

    save_processed(
        inventory,
        "fact_inventory.csv"
    )

    save_processed(
        purchase_orders,
        "fact_purchase_orders.csv"
    )

    save_processed(
        shipments,
        "fact_shipments.csv"
    )

    save_processed(
        aging,
        "fact_inventory_aging.csv"
    )

    print(
        "\nETL PIPELINE COMPLETED"
    )


# ---------------------------------------------------------
# Safe replacement for np.where
# ---------------------------------------------------------

def np_where(
    condition,
    value_true,
    value_false
):

    return value_true.where(
        condition,
        value_false
    )


if __name__ == "__main__":
    main()