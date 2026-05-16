"""Functions that clean HTML tags from text column by adding new cleaned column with prefix cln_"""


import html, re
from typing import Any
import pandas as pd
from bs4 import BeautifulSoup


__all__ = ["clean_html_text", "clean_text_columns", "clean_text_columns_df"]


def clean_html_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None

    text = html.unescape(str(value))
    soup = BeautifulSoup(text, "html.parser")

    for tag in soup(["script", "style", "meta", "head", "img"]):
        tag.decompose()

    text = soup.get_text(" ")
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_text_columns(
    rows: list[dict],
    columns: list[str],
    prefix: str = "cln_",
) -> list[dict]:
    result = []

    for row in rows:
        new_row = dict(row)

        for col in columns:
            if col not in new_row:
                raise ValueError(f"Missing column: {col}")

            new_row[f"{prefix}{col}"] = clean_html_text(new_row.get(col))

        result.append(new_row)

    return result


def clean_text_columns_df(
    df: pd.DataFrame,
    columns: list[str],
    prefix: str = "cln_",
) -> pd.DataFrame:
    result = df.copy()

    for col in columns:
        if col not in result.columns:
            raise ValueError(f"Missing column in DataFrame: {col}")

        result[f"{prefix}{col}"] = result[col].apply(clean_html_text)

    return result