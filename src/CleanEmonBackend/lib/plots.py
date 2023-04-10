import os
from datetime import datetime

from typing import List

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

from CleanEmonCore.models import EnergyData

from .. import PLOT_DIR

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR, exist_ok=True)


def timestamp_to_label(stamp):
    """Converts `stamp` into a datetime object and returns its reformatted string representation"""

    dt = datetime.fromtimestamp(stamp)

    return dt.strftime("%H:%M:%S")


def plot_data(energy_data: EnergyData, *, columns: List[str] = None, name="plot"):
    """Visualization the given dataframe"""

    df = pd.DataFrame(energy_data.energy_data)

    if not columns:
        columns = []
    else:
        columns = [col.lower() for col in columns]

    timestamp_label = "timestamp"

    if timestamp_label in df:
        time = df[timestamp_label]
        df = df.drop([timestamp_label], axis=1)
    else:
        time = df.index

    fig: plt.figure
    ax1: plt.subplot
    ax2: plt.subplot
    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True, subplot_kw=dict(frameon=False))  # frameon=False removes frames
    ax1.grid()
    ax2.grid()
    for col, data in df.items():
        # Skip any timestamp-like label
        if "timestamp" in str(col).lower():
            continue
        # Filter only selected columns
        if col == 'power':
            mask = np.isfinite(data)
            ax1.plot(time[mask], data[mask], label=col)

    for col, data in df.items():
        # Skip any timestamp-like label
        if "timestamp" in str(col).lower():
            continue
        # Filter only selected columns
        if (columns and str(col).lower() in columns) or (not columns):
            mask = np.isfinite(data)
            ax2.plot(time[mask], data[mask], label=col)
    skip = len(time) // 12

    plt.xticks(time[0:-1:skip], time[0:-1:skip].map(timestamp_to_label), rotation=90, fontsize=8)
    # plt.legend()
    fig.suptitle(energy_data.date)
    plt.xlabel("Time")
    #ax1.set_title("Power")
    lines_labels = [ax2.get_legend_handles_labels()]  # [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    fig.legend(lines, labels, loc=7, fontsize="x-small")
    fig.tight_layout()
    fig.subplots_adjust(right=0.76)

    fout_name = os.path.join(PLOT_DIR, f"{name}.png")
    plt.savefig(fout_name, dpi=1000)
    plt.cla()
    plt.clf()
    return fout_name


def plot_data2(energy_data: EnergyData, *, columns: List[str] = None, name="plot"):
    pass
