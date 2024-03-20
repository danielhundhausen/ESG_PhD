import datetime
import glob
import os
import re
from typing import Any, Tuple

import matplotlib.pyplot as plt
from matplotlib import cycler

import numpy as np
import pandas as pd
from pypdf import PdfReader


MONTHS = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
fnames = glob.glob("NAF consumption summary*.pdf")


def set_plt_paramters() -> None:
    colors = cycler(
        "color", ["#EE6666", "#3388BB", "#9988DD", "#EECC55", "#88BB44", "#FFBBBB"]
    )
    plt.rc(
        "axes",
        facecolor="#E6E6E6",
        edgecolor="none",
        axisbelow=True,
        grid=True,
        prop_cycle=colors,
    )
    plt.rc("grid", color="w", linestyle="solid")
    plt.rc("xtick", direction="out", color="gray")
    plt.rc("ytick", direction="out", color="gray")
    plt.rc("patch", edgecolor="#E6E6E6")
    plt.rc("lines", linewidth=2)
    plt.rc("font", weight="bold", size=15)
    plt.xticks(fontsize=12, rotation=90)

def plot_cumulative(df: pd.DataFrame, weeks_missing: int, user: str) -> None:
    fig, axs = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

    axs[0].text(df.week[2], np.sum(df.co2) * 0.95, f"Weeks Missing: {weeks_missing}")
    # Upper Plot
    # CO2
    color = "tab:orange"
    axs[0].plot(df.week, np.cumsum(df.co2), label="CO2 kg", color=color)
    axs[0].set_ylabel("kg CO2", color=color)
    # CPU kWh
    ax02 = axs[0].twinx()
    ax02.plot(df.week, np.cumsum(df.kwh), label="CPU hours", color=color)
    ax02.set_ylabel("kWh", color=color)

    # Lower Plot
    # Hours
    color = "tab:blue"
    axs[1].plot(df.week, np.cumsum(df.hours), label="CPU hours", color=color)
    axs[1].set_ylabel("CPU hours", color=color)
    # km
    ax12 = axs[1].twinx()
    ax12.plot(df.week, np.cumsum(df.km), label="VW Golf km", color=color)
    ax12.set_ylabel("VW Golf km", color=color)

    # Plot formatting
    axs[1].xaxis.set_tick_params(labelsize=13, rotation=20)
    axs[1].set_xlabel("Date")
    axs[0].set_title("Cumulative NAF Consumption " + user)
    fig.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0.02)
    plt.savefig("plot.png")
    plt.savefig("plot.pdf")
    plt.show()


def date_to_datetime(date: str) -> datetime.datetime:
    year = int(re.findall(r"\d\d\d+", date)[0])
    month_str = re.findall(r"[A-Z][a-z]+", date)[0]
    month = int(MONTHS.index(month_str))
    day = int(re.findall(r"\d+", date)[0])
    return datetime.datetime(year, month, day)


def get_info(text: str) -> dict[str, Any]:
    info = {}
    date_str = re.findall(r"\d+\. [A-Z][a-z]+ \d+", text)[0]
    info["week"] = date_to_datetime(date_str)
    info["hours"] = float(re.findall(r"(\d+.\d+) hours", text)[0])
    info["co2"] = float(re.findall(r"(\d+.\d+)\s+kg\s+CO2", text)[0])
    info["km"] = float(re.findall(r"(\d+.\d+)\s+km", text)[0])
    info["kwh"] = float(re.findall(r"(\d+.\d+)\s+kWh", text)[0])
    return info


def pad_missing_dates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    n_days = 7
    new_rows = []
    for i, row in df.iterrows():
        if row.week + datetime.timedelta(days=n_days) < df.week[i + 1]:
            _new_row = row.copy()
            while _new_row["week"] + datetime.timedelta(days=n_days) < df.week[i + 1]:
                _new_row["week"] += datetime.timedelta(days=n_days)
                _new_row["hours"] = 0
                _new_row["co2"] = 0
                _new_row["kwh"] = 0
                _new_row["km"] = 0
                new_rows.append(_new_row)
                _new_row = _new_row.copy()
        if i == len(df) - 2:
            break
    weeks_missing = len(new_rows)
    _df = pd.DataFrame(new_rows)
    df = pd.concat([df, _df], ignore_index=True)
    df = df.sort_values("week", ascending=True, ignore_index=True)
    return df, weeks_missing


if __name__ == "__main__":
    data = []
    for f in fnames:
        reader = PdfReader(f)
        page = reader.pages[0]
        text = page.extract_text()
        # extract info
        info = get_info(text)
        data.append(info)

    user = re.findall(r"Dear (.*)For", text)[0]
    df_data = pd.DataFrame(data)
    df_data = df_data.sort_values("week", ascending=True, ignore_index=True)
    df_data, weeks_missing = pad_missing_dates(df_data)
    set_plt_paramters()
    plot_cumulative(df_data, weeks_missing, user)
