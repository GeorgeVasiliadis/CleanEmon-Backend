from datetime import datetime
from datetime import timedelta

from typing import List

from CleanEmonCore.models import EnergyData

from ..lib.DBConnector import fetch_data
from .. import RES_DIR


def get_data(date: str, from_cache: bool, sensors: List[str] = None) -> EnergyData:
    raw_data = fetch_data(date, from_cache=from_cache).energy_data

    if sensors:
        filtered_data = []
        for record in raw_data:
            filtered_record = {sensor: value for sensor, value in record.items() if sensor in sensors}
            filtered_data.append(filtered_record)
        data = filtered_data
    else:
        data = raw_data

    return EnergyData(date, data)


def get_range_data(from_date: str, to_date: str, use_cache: bool, sensors: List[str] = None):
    data = {
        "from_date": from_date,
        "to_date": to_date,
        "range_data": []
    }

    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
    one_day = timedelta(days=1)

    now = from_dt
    while now <= to_dt:
        now_str = now.strftime("%Y-%m-%d")
        daily_data = get_data(now_str, use_cache, sensors)
        data["range_data"].append(daily_data)
        now += one_day

    return data


def get_plot(date: str, from_cache: bool, sensors: List[str] = None) -> str:
    # energy_data = get_data(from_cache, sensors)

    return f"{RES_DIR}/donut.jpg"


def get_processed_kwh(date: str, from_cache: bool) -> float:
    data = get_data(date, from_cache)

    kwh_list = [record["kwh"] for record in data.energy_data]

    # Find the first valid kwh measurement
    first_valid = 0
    for kwh in kwh_list:
        if kwh:
            first_valid = kwh
            break

    # Find the last valid kwh measurement
    last_valid = 0
    for kwh in reversed(kwh_list):
        if kwh:
            last_valid = kwh
            break

    return last_valid - first_valid
