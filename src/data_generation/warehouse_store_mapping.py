import random
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")

SEED = 42
random.seed(SEED)


def generate_mapping():

    warehouses = pd.read_csv(
        PROCESSED_DIR / "dim_warehouse.csv"
    )

    stores = pd.read_csv(
        PROCESSED_DIR / "dim_store.csv"
    )

    records = []

    for _, store in stores.iterrows():

        # Prefer assigning stores to warehouses
        # within the same region.

        regional_warehouses = warehouses[
            warehouses["region"] == store["region"]
        ]

        if regional_warehouses.empty:
            regional_warehouses = warehouses

        warehouse = regional_warehouses.sample(
            n=1,
            random_state=random.randint(1, 100000)
        ).iloc[0]

        records.append(
            {
                "store_id": store["store_id"],
                "warehouse_id": warehouse["warehouse_id"],
            }
        )

    df = pd.DataFrame(records)

    output_file = (
        PROCESSED_DIR /
        "store_warehouse_mapping.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"Created {len(df):,} "
        f"store-warehouse mappings."
    )

    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    generate_mapping()