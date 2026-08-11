import os
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "fmcg_supply_chain")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# ============================================================
# READ CSV
# ============================================================

def read_csv(filename):

    filepath = PROCESSED_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"File not found: {filepath}"
        )

    df = pd.read_csv(filepath)

    print(
        f"{filename:<30} {len(df):>10,} rows"
    )

    return df


# ============================================================
# CLEAN VALUES
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    return value


# ============================================================
# INSERT DATA
# ============================================================

def insert_dataframe(
    connection,
    df,
    table_name,
    columns,
    batch_size=5000
):

    missing = [
        col
        for col in columns
        if col not in df.columns
    ]

    if missing:

        raise ValueError(
            f"{table_name}: missing CSV columns: {missing}"
        )

    cursor = connection.cursor()

    column_sql = ", ".join(
        f"`{col}`"
        for col in columns
    )

    placeholders = ", ".join(
        ["%s"] * len(columns)
    )

    query = f"""
        INSERT INTO `{table_name}`
        ({column_sql})
        VALUES ({placeholders})
    """

    rows = []

    for row in df[columns].itertuples(
        index=False,
        name=None
    ):

        rows.append(
            tuple(
                clean_value(value)
                for value in row
            )
        )

    total = len(rows)

    print(
        f"\nLoading {total:,} rows into {table_name}..."
    )

    for start in range(
        0,
        total,
        batch_size
    ):

        batch = rows[
            start:start + batch_size
        ]

        cursor.executemany(
            query,
            batch
        )

        connection.commit()

        loaded = min(
            start + batch_size,
            total
        )

        print(
            f"  {loaded:,}/{total:,}"
        )

    cursor.close()

    print(
        f"Finished {table_name}"
    )


# ============================================================
# CLEAR FACT TABLES
# ============================================================

def clear_fact_tables(connection):

    cursor = connection.cursor()

    # IMPORTANT:
    # Delete child tables before parent tables
    # because of foreign-key constraints.

    tables = [
        "fact_inventory_aging",
        "fact_shipments",
        "fact_purchase_orders",
        "fact_inventory",
        "fact_sales"
    ]

    print("\nClearing existing fact tables...")

    try:

        for table in tables:

            cursor.execute(
                f"DELETE FROM `{table}`"
            )

            print(
                f"  Cleared {table}: "
                f"{cursor.rowcount:,} rows"
            )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        cursor.close()


# ============================================================
# SALES
# ============================================================

def load_sales(connection):

    df = read_csv(
        "fact_sales.csv"
    )

    # CSV → MySQL
    columns = [
        "sale_id",
        "date_id",
        "product_id",
        "store_id",
        "quantity_sold",
        "unit_price",
        "discount",
        "sales_amount",
        "revenue",
        "gross_sales"
    ]

    insert_dataframe(
        connection,
        df,
        "fact_sales",
        columns
    )


# ============================================================
# INVENTORY
# ============================================================

def load_inventory(connection):

    df = read_csv(
        "fact_inventory.csv"
    )

    # CSV → MySQL
    columns = [
        "inventory_id",
        "date_id",
        "product_id",
        "warehouse_id",
        "opening_stock",
        "demand_units",
        "received_units",
        "sold_units",
        "closing_stock",
        "damaged_units",
        "expired_units",
        "stockout_units",
        "inventory_value",
        "stockout_rate"
    ]

    insert_dataframe(
        connection,
        df,
        "fact_inventory",
        columns
    )


# ============================================================
# PURCHASE ORDERS
# ============================================================

def load_purchase_orders(connection):

    df = read_csv(
        "fact_purchase_orders.csv"
    )

    # CSV → MySQL
    columns = [
        "po_id",
        "date_id",
        "supplier_id",
        "product_id",
        "warehouse_id",
        "ordered_quantity",
        "received_quantity",
        "unit_cost",
        "order_status"
    ]

    insert_dataframe(
        connection,
        df,
        "fact_purchase_orders",
        columns
    )


# ============================================================
# SHIPMENTS
# ============================================================

def load_shipments(connection):

    df = read_csv(
        "fact_shipments.csv"
    )

    # CSV → MySQL
    columns = [
        "shipment_id",
        "po_id",
        "warehouse_id",
        "store_id",
        "shipment_date",
        "expected_delivery_date",
        "actual_delivery_date",
        "ordered_quantity",
        "quantity_shipped",
        "quantity_delivered",
        "damage_units",
        "delivery_delay_days",
        "fill_rate",
        "on_time_flag",
        "shipping_cost",
        "damage_rate",
        "late_shipment_flag"
    ]

    insert_dataframe(
        connection,
        df,
        "fact_shipments",
        columns
    )


# ============================================================
# INVENTORY AGING
# ============================================================

def load_inventory_aging(connection):

    df = read_csv(
        "fact_inventory_aging.csv"
    )

    columns = [
        "lot_id",
        "shipment_id",
        "po_id",
        "product_id",
        "warehouse_id",
        "receipt_date",
        "expiry_date",
        "received_units",
        "remaining_units",
        "unit_cost",
        "shelf_life_days",
        "analysis_date",
        "age_days",
        "remaining_shelf_life_days",
        "age_bucket",
        "expiry_risk",
        "inventory_value",
        "expiry_risk_value",
        "expiry_risk_flag"
    ]

    insert_dataframe(
        connection,
        df,
        "fact_inventory_aging",
        columns
    )


# ============================================================
# DATABASE COUNTS
# ============================================================

def get_count(connection, table):

    cursor = connection.cursor()

    cursor.execute(
        f"SELECT COUNT(*) FROM `{table}`"
    )

    result = cursor.fetchone()[0]

    cursor.close()

    return result


# ============================================================
# VALIDATION
# ============================================================

def validate_database(connection):

    print("\n")
    print("=" * 70)
    print("DATABASE VALIDATION")
    print("=" * 70)

    tables = [
        "dim_product",
        "dim_supplier",
        "dim_warehouse",
        "dim_store",
        "dim_date",
        "fact_sales",
        "fact_inventory",
        "fact_purchase_orders",
        "fact_shipments",
        "fact_inventory_aging"
    ]

    counts = {}

    for table in tables:

        count = get_count(
            connection,
            table
        )

        counts[table] = count

        print(
            f"{table:<30} {count:>12,}"
        )

    print("=" * 70)

    return counts


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("FMCG SUPPLY CHAIN - MYSQL LOADER")
    print("=" * 70)

    connection = None

    try:

        connection = get_connection()

        print(
            "\nMySQL connection successful."
        )

        # ----------------------------------------------------
        # CHECK DIMENSIONS
        # ----------------------------------------------------

        print(
            "\nChecking dimension tables..."
        )

        dimension_tables = [
            "dim_product",
            "dim_supplier",
            "dim_warehouse",
            "dim_store",
            "dim_date"
        ]

        for table in dimension_tables:

            count = get_count(
                connection,
                table
            )

            print(
                f"{table:<30} {count:>12,}"
            )

            if count == 0:

                raise RuntimeError(
                    f"{table} is empty."
                )

        # ----------------------------------------------------
        # CLEAR FACT TABLES
        # ----------------------------------------------------

        clear_fact_tables(
            connection
        )

        # ----------------------------------------------------
        # LOAD FACT TABLES
        # ----------------------------------------------------

        load_sales(
            connection
        )

        load_inventory(
            connection
        )

        load_purchase_orders(
            connection
        )

        load_shipments(
            connection
        )

        load_inventory_aging(
            connection
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        counts = validate_database(
            connection
        )

        # ----------------------------------------------------
        # FINAL CHECK
        # ----------------------------------------------------

        required = [
            "fact_sales",
            "fact_inventory",
            "fact_purchase_orders"
        ]

        for table in required:

            if counts[table] == 0:

                raise RuntimeError(
                    f"{table} is still empty."
                )

        print(
            "\nSUCCESS!"
        )

        print(
            "Fact tables loaded successfully."
        )

    except Exception as error:

        print(
            "\nERROR:"
        )

        print(error)

        if connection:
            connection.rollback()

        raise

    finally:

        if connection:

            connection.close()

            print(
                "\nMySQL connection closed."
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()