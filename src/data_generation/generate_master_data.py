import random
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------
# Locations
# ---------------------------------------------------------

LOCATIONS = [
    ("Pune", "Maharashtra", "West"),
    ("Mumbai", "Maharashtra", "West"),
    ("Nagpur", "Maharashtra", "West"),
    ("Ahmedabad", "Gujarat", "West"),
    ("Delhi", "Delhi", "North"),
    ("Gurugram", "Haryana", "North"),
    ("Bengaluru", "Karnataka", "South"),
    ("Chennai", "Tamil Nadu", "South"),
    ("Hyderabad", "Telangana", "South"),
    ("Kolkata", "West Bengal", "East"),
]


# ---------------------------------------------------------
# Suppliers
# ---------------------------------------------------------

def generate_suppliers():

    supplier_types = [
        "Manufacturer",
        "Distributor",
        "Contract Manufacturer",
    ]

    contract_types = [
        "Annual",
        "Multi-Year",
        "Spot",
    ]

    rows = []

    for i in range(1, 21):

        city, state, region = random.choice(
            LOCATIONS
        )

        rows.append(
            {
                "supplier_id": f"SUP{i:03d}",
                "supplier_name": (
                    f"Supplier {chr(64 + i)}"
                ),
                "supplier_region": region,
                "supplier_type": random.choice(
                    supplier_types
                ),
                "supplier_rating": round(
                    random.uniform(3.0, 5.0),
                    2
                ),
                "contract_type": random.choice(
                    contract_types
                ),
            }
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_DIR / "dim_supplier.csv",
        index=False
    )

    return df


# ---------------------------------------------------------
# Warehouses
# ---------------------------------------------------------

def generate_warehouses():

    warehouse_types = [
        "Regional DC",
        "Central DC",
        "Distribution Hub",
    ]

    rows = []

    selected_locations = LOCATIONS[:8]

    for i, (city, state, region) in enumerate(
        selected_locations,
        start=1
    ):

        capacity = random.choice(
            [
                50000,
                75000,
                100000,
                150000,
                200000,
            ]
        )

        rows.append(
            {
                "warehouse_id": f"WH{i:03d}",
                "warehouse_name": (
                    f"{city} Distribution Center"
                ),
                "city": city,
                "state": state,
                "warehouse_type": random.choice(
                    warehouse_types
                ),
                "capacity_units": capacity,
                "region": region,
            }
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_DIR / "dim_warehouse.csv",
        index=False
    )

    return df


# ---------------------------------------------------------
# Stores
# ---------------------------------------------------------

def generate_stores():

    store_types = [
        "Supermarket",
        "Hypermarket",
        "Convenience Store",
        "General Trade",
        "Modern Trade",
    ]

    rows = []

    for i in range(1, 101):

        city, state, region = random.choice(
            LOCATIONS
        )

        rows.append(
            {
                "store_id": f"STORE{i:04d}",
                "store_name": (
                    f"Retail Store {i:04d}"
                ),
                "city": city,
                "state": state,
                "store_type": random.choice(
                    store_types
                ),
                "region": region,
            }
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_DIR / "dim_store.csv",
        index=False
    )

    return df


# ---------------------------------------------------------
# Date dimension
# ---------------------------------------------------------

def generate_date_dimension():

    dates = pd.date_range(
        start="2025-01-01",
        end="2026-12-31",
        freq="D"
    )

    df = pd.DataFrame(
        {
            "date_id": dates.strftime(
                "%Y%m%d"
            ).astype(int),

            "date": dates,

            "day": dates.day,

            "month": dates.month,

            "month_name": dates.month_name(),

            "quarter": (
                "Q"
                + dates.quarter.astype(str)
            ),

            "year": dates.year,

            "week": (
                dates.isocalendar()
                .week
                .astype(int)
            ),

            "day_of_week": dates.day_name(),
        }
    )

    df.to_csv(
        OUTPUT_DIR / "dim_date.csv",
        index=False
    )

    return df


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("FMCG MASTER DATA GENERATION")
    print("=" * 60)

    suppliers = generate_suppliers()
    warehouses = generate_warehouses()
    stores = generate_stores()
    dates = generate_date_dimension()

    print(
        f"\nSuppliers  : {len(suppliers):,}"
    )

    print(
        f"Warehouses : {len(warehouses):,}"
    )

    print(
        f"Stores     : {len(stores):,}"
    )

    print(
        f"Dates      : {len(dates):,}"
    )

    print("\nMaster data generated successfully.")


if __name__ == "__main__":
    main()