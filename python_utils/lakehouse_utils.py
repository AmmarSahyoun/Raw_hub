"""Functions that save DataFrame/JSON to /lakehouse/default/Files/landing/... with metadata."""


import os, json
import pandas as pd
from typing import Any, Dict
from datetime import datetime

__all__ = ["save_df_to_lakehouse", "save_json_to_lakehouse"]


def save_df_to_lakehouse(
    df: pd.DataFrame,
    extract_metadata: Dict,
    source_system: str,
    source_table: str,
    execution_date_str: str,
    sub_source_system: str | None = None,
) -> None:
    """Args:
        df: Tabular data to persist as a parquet file.
        extract_metadata: Additional run context written as JSON alongside the data file.
        source_system: Logical system name used to build the Lakehouse folder path.
        source_table: Logical table or entity name used to build the Lakehouse folder path.
        execution_date_str: Execution date in ``YYYY-MM-DD`` format used to partition the output.
        sub_source_system: Optional sub-source identifier (e.g. endpoint name or database name)
            inserted between source_system and source_table in the path. When provided the path
            becomes ``landing/{source_system}/{sub_source_system}/{source_table}/...``.
    """

    execution_date = datetime.strptime(execution_date_str, "%Y-%m-%d")
    year = execution_date.year
    month = execution_date.month
    day = execution_date.day

    if sub_source_system:
        lakehouse_path = f"/lakehouse/default/Files/landing/{source_system}/{sub_source_system}/{source_table}/{year}/{month:02d}/{day:02d}/"
    else:
        lakehouse_path = f"/lakehouse/default/Files/landing/{source_system}/{source_table}/{year}/{month:02d}/{day:02d}/"

    os.makedirs(lakehouse_path, exist_ok=True)

    data_file = f"{lakehouse_path}{source_system}_{source_table}_{year}{month:02d}{day:02d}_data.parquet"
    metadata_file = f"{lakehouse_path}{source_system}_{source_table}_{year}{month:02d}{day:02d}_metadata.json"

    df.to_parquet(data_file, index=False)

    with open(metadata_file, "w") as f:
        json.dump(extract_metadata, f, indent=2)


def save_json_to_lakehouse(
    data: Any,
    extract_metadata: Dict,
    source_system: str,
    source_table: str,
    execution_date_str: str,
    sub_source_system: str | None = None,
) -> None:
    """Args:
        data: JSON-serialisable object captured for the execution.
        extract_metadata: Additional run context written as JSON alongside the data file.
        source_system: Logical system name used to build the Lakehouse folder path.
        source_table: Logical table or entity name used to build the Lakehouse folder path.
        execution_date_str: Execution date in ``YYYY-MM-DD`` format used to partition the output.
        sub_source_system: Optional sub-source identifier (e.g. endpoint name or database name)
            inserted between source_system and source_table in the path. When provided the path
            becomes ``landing/{source_system}/{sub_source_system}/{source_table}/...``.
    """

    execution_date = datetime.strptime(execution_date_str, "%Y-%m-%d")
    year = execution_date.year
    month = execution_date.month
    day = execution_date.day

    if sub_source_system:
        lakehouse_path = f"/lakehouse/default/Files/landing/{source_system}/{sub_source_system}/{source_table}/{year}/{month:02d}/{day:02d}/"
    else:
        lakehouse_path = f"/lakehouse/default/Files/landing/{source_system}/{source_table}/{year}/{month:02d}/{day:02d}/"

    os.makedirs(lakehouse_path, exist_ok=True)

    data_file = f"{lakehouse_path}{source_system}_{source_table}_{year}{month:02d}{day:02d}_data.json"
    metadata_file = f"{lakehouse_path}{source_system}_{source_table}_{year}{month:02d}{day:02d}_metadata.json"

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(extract_metadata, f, indent=2)
