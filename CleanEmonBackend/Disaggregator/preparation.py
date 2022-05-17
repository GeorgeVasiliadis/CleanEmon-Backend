from datetime import datetime

import pandas as pd

from CleanEmonCore.models import EnergyData

INTERVAL = 5
INTERVAL_STR = f"{INTERVAL}S"
PERIODS = 60*60*24/INTERVAL


def reformat_timestamp(stamp: float) -> str:
    dt = datetime.fromtimestamp(stamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S+01:00")


def to_continuous_time(df: pd.DataFrame) -> pd.DataFrame:
    df.copy()

    # Copy some datetime details from the original dataframe
    today = df.index[0].date()
    tz = df.index[0].tz

    # Generate a new index consisting of continuous values
    continuous_index = pd.date_range(today, periods=PERIODS, freq=INTERVAL_STR, tz=tz)

    # Create the new dataframe with the continuous index
    new_df = pd.DataFrame(index=continuous_index, columns=df.columns)

    # Specify which columns can be filled using the old values
    intersection = new_df.index.intersection(df.index)

    # Fill the specified time slots with corresponding data from the old dataframe
    new_df.loc[intersection] = df.loc[intersection].values

    return new_df


def energy_data_to_dataframe(data: EnergyData, timestamp_label: str = "timestamp") -> pd.DataFrame:
    # Convert EnergyData to Dataframe
    df = pd.DataFrame(data.energy_data)

    # Reformat timestamp as expected by NILM-Inference-APIs
    df[timestamp_label] = df[timestamp_label].map(reformat_timestamp)

    # Rename columns as expected by NILM-Inference-APIs
    df.rename(columns={timestamp_label: f"original{timestamp_label}"}, inplace=True)

    # Index dataframe by time
    df = df.set_index(pd.DatetimeIndex(df[timestamp_label]))

    # Quantize time. Every timestamp should be mapped into fixed intervals.
    df.index = df.index.map(lambda date: date.round(INTERVAL_STR))

    # If more than one timestamp map into the same time quantum, arbitrarily remove all duplicates but the first
    df = df[~df.index.duplicated(keep="first")]

    # Generate a clean dataframe. All potentially empty time slots are filled
    df = to_continuous_time(df)

    # Reset index as expected by NILM-Inference-APIs
    df = df.reset_index()
    df = df.rename(columns={"index": timestamp_label})

    return df
