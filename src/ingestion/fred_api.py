import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

FRED_API_KEY = os.getenv("FRED_API_KEY")


SERIES = {
    "A11SFI": "Food Products Finished Goods Inventories",
    "A11SMI": "Food Products Materials and Supplies Inventories",
    "AMNMFI": "Nondurable Goods Finished Goods Inventories",
    "ACOGTI": "Consumer Goods Total Inventories",
}


def fetch_fred_series(
    series_id: str,
    observation_start: str = "2020-01-01"
) -> pd.DataFrame:

    if not FRED_API_KEY:
        raise ValueError(
            "FRED_API_KEY is missing. "
            "Add it to your .env file."
        )

    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "series_id": series_id,
        "observation_start": observation_start,
        "sort_order": "asc"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    observations = data.get("observations", [])

    df = pd.DataFrame(observations)

    if df.empty:
        return df

    df = df[
        [
            "date",
            "value"
        ]
    ]

    df["date"] = pd.to_datetime(df["date"])

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    df["series_id"] = series_id

    df["series_name"] = SERIES.get(
        series_id,
        series_id
    )

    return df


def save_fred_data(df: pd.DataFrame, series_id: str):

    output_dir = Path("data/raw/fred")
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        f"{series_id}.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    return output_file


def main():

    print("Starting FRED ingestion...")

    all_data = []

    for series_id in SERIES:

        print(
            f"Fetching FRED series: "
            f"{series_id}"
        )

        df = fetch_fred_series(
            series_id
        )

        if df.empty:
            print(
                f"No observations found "
                f"for {series_id}"
            )
            continue

        save_fred_data(
            df,
            series_id
        )

        all_data.append(df)

        print(
            f"Downloaded "
            f"{len(df):,} observations."
        )

    if all_data:

        combined = pd.concat(
            all_data,
            ignore_index=True
        )

        output_file = (
            Path("data/raw/fred")
            / "fred_combined.csv"
        )

        combined.to_csv(
            output_file,
            index=False
        )

        print("\nFRED ingestion completed.")
        print(
            f"Combined file: "
            f"{output_file}"
        )


if __name__ == "__main__":
    main()