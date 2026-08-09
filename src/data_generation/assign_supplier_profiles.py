import random
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")

SEED = 42
random.seed(SEED)


def assign_profiles():

    input_file = (
        PROCESSED_DIR /
        "dim_supplier.csv"
    )

    df = pd.read_csv(input_file)

    profiles = []

    for i in range(len(df)):

        if i < int(len(df) * 0.20):
            profile = "Excellent"

        elif i < int(len(df) * 0.50):
            profile = "Good"

        elif i < int(len(df) * 0.85):
            profile = "Average"

        else:
            profile = "Poor"

        profiles.append(profile)

    random.shuffle(profiles)

    df["performance_tier"] = profiles

    output_file = (
        PROCESSED_DIR /
        "dim_supplier.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print(
        "Supplier profiles assigned."
    )

    print(
        df[
            [
                "supplier_id",
                "supplier_name",
                "performance_tier",
            ]
        ]
    )


if __name__ == "__main__":
    assign_profiles()