"""This module defines the core functionality of the API"""

import os
from datetime import datetime
from datetime import timedelta

from typing import List
from typing import Dict
from typing import Union
from typing import Any

from CleanEmonCore.models import EnergyData

from .. import RES_DIR
from ..lib.DBConnector import fetch_data
from ..lib.DBConnector import adapter
from ..lib.plots import plot_data


def get_data(date: str, from_cache: bool, sensors: List[str] = None) -> EnergyData:
    """Fetches and prepares the daily data that will be returned, filtering in the provided `sensors`.
    Note that there is no need to explicitly specify the "timestamp sensor", as it will always be included.

    date -- a valid date string in `YYYY-MM-DD` format
    from_cache -- specifies whether the data should be searched in cache first. This may speed up the response time
    sensors -- an inclusive list containing the values of interest
    """

    raw_data = fetch_data(date, from_cache=from_cache).energy_data

    if sensors:
        if "timestamp" not in sensors:
            sensors.append("timestamp")

        filtered_data = []
        for record in raw_data:
            filtered_record = {sensor: value for sensor, value in record.items() if sensor in sensors}
            filtered_data.append(filtered_record)
        data = filtered_data
    else:
        data = raw_data

    return EnergyData(date, data)


def get_range_data(from_date: str, to_date: str, use_cache: bool, sensors: List[str] = None) -> Dict:
    """Fetches and prepares the range data that will be returned.

    from_date -- a valid date string in `YYYY-MM-DD` format
    to_date -- a valid date string in `YYYY-MM-DD` format. It MUST be chronologically greater or equal to `from_date`
    from_cache -- specifies whether the data should be searched in cache first. This may speed up the response time
    sensors -- an inclusive list containing the values of interest
    """

    # Define the range data schema
    # todo: maybe define a an appropriate solid dataclass?
    data = {
        "from_date": from_date,
        "to_date": to_date,
        "range_data": []
    }

    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")
    one_day = timedelta(days=1)

    # Concatenate energy data from multiple dates into a single list
    now = from_dt
    while now <= to_dt:
        now_str = now.strftime("%Y-%m-%d")
        daily_data = get_data(now_str, use_cache, sensors)
        data["range_data"].append(daily_data)
        now += one_day

    return data


def get_plot(date: str, from_cache: bool, sensors: List[str] = None) -> str:
    """Fetches and plots the desired data. Returns the path of the resulting plot.

    date -- a valid date string in `YYYY-MM-DD` format
    from_cache -- specifies whether the data should be searched in cache first. This may speed up the response time
    sensors -- an inclusive list containing the values of interest
    """

    energy_data = get_data(date, from_cache, sensors)
    f_out = plot_data(energy_data, columns=sensors)

    return os.path.join(RES_DIR, f_out)


def get_date_consumption(date: str, from_cache: bool, simplify: bool):
    """Hardcoded fetch-prepare accumulator function that handles the daily KwH. Returns the daily consumption in kwh.

    Acts as an under-the-curve measurement by subtracting the lowest power measurement from the highest one.
    It's not given that the first record of the energy data will always contain valid power values and thus, the "first
    value" is actually searched and cherry-picked. Same goes for the "last valid value".

    date -- a valid date string in `YYYY-MM-DD` format
    from_cache -- specifies whether the data should be searched in cache first. This may speed up the response time
    simplify -- if true, returns a single value, not a JSON object
    """

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

    consumption = last_valid - first_valid
    if simplify:
        data = consumption
    else:
        data = {
            "consumption": consumption,
            "unit": "kwh"
        }

    return data


def get_mean_consumption(date: str, from_cache: bool) -> float:
    """Hardcoded fetch-prepare function that returns the daily consumption over the size of the building.
    If the given building has no appropriate information (e.g. no "size" meta-data) -1 is being returned.

    Mean Consumption is calculated as:  daily_consumption_of_date  /  size_of_building

    date -- a valid date string in `YYYY-MM-DD` format
    from_cache -- specifies whether the data should be searched in cache first. This may speed up the response time
    """
    _size_field = "size"  # Hardcoded field - get_meta is not intended to be used in this way

    consumption: float = get_date_consumption(date, from_cache, simplify=True)

    if has_meta(_size_field):
        size = float(get_meta(_size_field))
        if size:
            return consumption / size
    return -1


def get_meta(field: str = None) -> Union[Dict, Any]:
    meta = adapter.fetch_meta()
    if not field:
        return meta
    else:
        if field in meta:
            return meta[field]
    return {}


def has_meta(field: str) -> bool:
    meta = get_meta()

    if field not in meta:
        return False

    value = meta[field]
    return value != "null"
