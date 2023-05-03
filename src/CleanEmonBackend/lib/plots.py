import os
from datetime import datetime
from io import BytesIO

from typing import List
import matplotlib

matplotlib.use('svg')
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


def plot_data(energy_data: EnergyData, *, columns: List[str] = None, name="plot") -> BytesIO:
    """Visualization the given dataframe"""

    if len(energy_data.energy_data) == 0:
        fig = plt.figure()
        ax = fig.add_subplot(111)

        txt = ax.text(0.1, 0.85, f'{energy_data.date} no energy data',
                      horizontalalignment='left',
                      verticalalignment='center',
                      transform=ax.transAxes,
                      fontsize='xx-large')
        plt.axis('off')
        txt.set_clip_on(False)  # I added this due to the answer from tcaswell

        buf = BytesIO()
        plt.savefig(buf, format="svg", dpi=1000)
        buf.seek(0)

        plt.cla()
        plt.clf()
        plt.close(fig)

        return buf

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
    # ax1.set_title("Power")
    lines_labels = [ax2.get_legend_handles_labels()]  # [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    fig.legend(lines, labels, loc=7, fontsize="x-small")
    fig.tight_layout()
    fig.subplots_adjust(right=0.76)

    buf = BytesIO()
    plt.savefig(buf, format="svg", dpi=1000)
    buf.seek(0)

    plt.cla()
    plt.clf()
    plt.close(fig)

    return buf


def plot_data2(energy_data: EnergyData, *, columns: List[str] = None, name="plot"):
    pass
