from datetime import datetime

import pandas as pd

from .. import NILM_INPUT_FILE_PATH
from ..lib.DBConnector import fetch_data


def reformat_timestamp(stamp: float) -> str:
    dt = datetime.fromtimestamp(stamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S+01:00")


def reindex_to_time(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.set_index(pd.DatetimeIndex(df["Time"]))
    del df["Time"]

    return df


def reset_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.reset_index()
    df = df.rename(columns={"index": "Time"})
    return df


def _remove_random_samples(df: pd.DataFrame, ratio: float = 0.3) -> pd.DataFrame:
    df = df.copy()
    count = int(len(df) * ratio)
    random_rows = df.sample(count)
    df = df.drop(random_rows.index)
    return df


def round_time(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.index = df.index.map(lambda date: date.round("5S"))
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows that were rounded to the same timestamp"""

    df = df.copy()
    df = df[~df.index.duplicated(keep="first")]
    return df


def good_df_factory(df: pd.DataFrame) -> pd.DataFrame:
    df.copy()
    today = df.index[0].date()
    tz = df.index[0].tz
    good_times = pd.date_range(today, periods=17280, freq="5S", tz=tz)

    good_df = pd.DataFrame(index=good_times, columns=df.columns)

    intersection = good_df.index.intersection(df.index)
    good_df.loc[intersection] = df.loc[intersection].values

    return good_df


def date_to_input_file(date: str) -> None:
    """
    Args:
        - date :: A string in YYYY-MM-DD format
    """

    data = fetch_data(date, from_cache=True)
    df = pd.DataFrame(data.energy_data)

    # Filter out unneeded columns
    df = df[["power", "timestamp"]]
    df["timestamp"] = df["timestamp"].map(reformat_timestamp)

    # Rename columns as desired
    df.rename(columns={"power": "mains", "timestamp": "Time"}, inplace=True)

    df = reindex_to_time(df)
    df = round_time(df)
    df = drop_duplicates(df)
    df = good_df_factory(df)
    df = reset_index(df)

    mean = df["mains"].mean()
    df["mains"] = df["mains"].fillna(mean).round().astype(int)

    # Create input file
    df.to_csv(NILM_INPUT_FILE_PATH, index=False)


def reformat_output_file(file):
    df = pd.read_csv(file)
