from pathlib import Path

import pandas as pd


QUALITY_DIR = Path("data/quality")


# ---------------------------------------------------------
# CHECK NULL VALUES
# ---------------------------------------------------------

def check_nulls(
    df,
    table_name
):

    results = []

    for column in df.columns:

        null_count = int(
            df[column].isna().sum()
        )

        total = len(df)

        null_percentage = (
            null_count / total * 100
            if total > 0
            else 0
        )

        results.append(
            {
                "table_name": table_name,
                "check": "NULL_CHECK",
                "column": column,
                "value": null_count,
                "percentage": round(
                    null_percentage,
                    2
                ),
                "status": (
                    "PASS"
                    if null_count == 0
                    else "WARNING"
                ),
            }
        )

    return results


# ---------------------------------------------------------
# CHECK DUPLICATES
# ---------------------------------------------------------

def check_duplicates(
    df,
    table_name,
    key_column
):

    if key_column not in df.columns:

        return [
            {
                "table_name": table_name,
                "check": "DUPLICATE_CHECK",
                "column": key_column,
                "value": "COLUMN_NOT_FOUND",
                "percentage": 0,
                "status": "FAIL",
            }
        ]

    duplicate_count = int(
        df[key_column]
        .duplicated()
        .sum()
    )

    return [
        {
            "table_name": table_name,
            "check": "DUPLICATE_CHECK",
            "column": key_column,
            "value": duplicate_count,
            "percentage": round(
                duplicate_count
                /
                max(len(df), 1)
                * 100,
                2
            ),
            "status": (
                "PASS"
                if duplicate_count == 0
                else "FAIL"
            ),
        }
    ]


# ---------------------------------------------------------
# CHECK NEGATIVE VALUES
# ---------------------------------------------------------

def check_negative_values(
    df,
    table_name,
    columns
):

    results = []

    for column in columns:

        if column not in df.columns:
            continue

        negative_count = int(
            (df[column] < 0).sum()
        )

        results.append(
            {
                "table_name": table_name,
                "check": "NEGATIVE_VALUE_CHECK",
                "column": column,
                "value": negative_count,
                "percentage": round(
                    negative_count
                    /
                    max(len(df), 1)
                    * 100,
                    2
                ),
                "status": (
                    "PASS"
                    if negative_count == 0
                    else "FAIL"
                ),
            }
        )

    return results


# ---------------------------------------------------------
# CHECK VALUE RANGE
# ---------------------------------------------------------

def check_range(
    df,
    table_name,
    column,
    minimum=None,
    maximum=None
):

    if column not in df.columns:

        return []

    series = df[column]

    invalid = pd.Series(
        False,
        index=df.index
    )

    if minimum is not None:

        invalid |= (
            series < minimum
        )

    if maximum is not None:

        invalid |= (
            series > maximum
        )

    invalid_count = int(
        invalid.sum()
    )

    return [
        {
            "table_name": table_name,
            "check": "RANGE_CHECK",
            "column": column,
            "value": invalid_count,
            "percentage": round(
                invalid_count
                /
                max(len(df), 1)
                * 100,
                2
            ),
            "status": (
                "PASS"
                if invalid_count == 0
                else "FAIL"
            ),
        }
    ]


# ---------------------------------------------------------
# REFERENTIAL INTEGRITY
# ---------------------------------------------------------

def check_foreign_key(
    child_df,
    parent_df,
    child_column,
    parent_column,
    child_table
):

    if (
        child_column not in child_df.columns
        or
        parent_column not in parent_df.columns
    ):

        return [
            {
                "table_name": child_table,
                "check": "FOREIGN_KEY_CHECK",
                "column": child_column,
                "value": "COLUMN_NOT_FOUND",
                "percentage": 0,
                "status": "FAIL",
            }
        ]

    invalid = (
        ~child_df[child_column]
        .isin(
            parent_df[parent_column]
        )
    )

    invalid_count = int(
        invalid.sum()
    )

    return [
        {
            "table_name": child_table,
            "check": "FOREIGN_KEY_CHECK",
            "column": child_column,
            "value": invalid_count,
            "percentage": round(
                invalid_count
                /
                max(len(child_df), 1)
                * 100,
                2
            ),
            "status": (
                "PASS"
                if invalid_count == 0
                else "FAIL"
            ),
        }
    ]


# ---------------------------------------------------------
# SAVE QUALITY REPORT
# ---------------------------------------------------------

def save_quality_report(
    results
):

    QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = pd.DataFrame(
        results
    )

    output_file = (
        QUALITY_DIR /
        "data_quality_report.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    return output_file