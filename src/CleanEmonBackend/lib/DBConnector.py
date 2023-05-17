"""This module contains a set of utilities used to transform and prepare data for torch-nilm inference"""

import os
from typing import Union

import compress_json
from CleanEmonCore import CONFIG_FILE
from CleanEmonCore.CouchDBAdapter import CouchDBAdapter
from CleanEmonCore.models import EnergyData

from .. import CACHE_DIR

adapter = CouchDBAdapter(CONFIG_FILE)


def fetch_document(document: str, db: str):
    return adapter._fetch_document(document=document, db=db)


def create_document(document: str, db: str, data):
    return adapter.create_document(name=document, db=db, initial_data=data)


def fetch_data(date_id: str, *, from_cache=False, db: str = None) -> EnergyData:
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    name = date_id + db

    cache_path = os.path.join(CACHE_DIR, name + '.gz')

    fetch_ok = False
    energy_data = EnergyData()

    if from_cache:
        try:
            raw_data = compress_json.load(cache_path)
            energy_data = EnergyData(raw_data["date"], raw_data["energy_data"])
            print("Fetched data from cache")
            fetch_ok = True
        except OSError:
            print("No cached data!")

    if not from_cache or not fetch_ok:
        energy_data = adapter.fetch_energy_data_by_date(date_id, db=db)

        # Cache data for future use
        compress_json.dump(energy_data.as_json(string=False), cache_path)

    return energy_data


def get_last_value(db: str):
    return adapter.get_last_energy_data_record(db)


def send_data(date_id: str, data: EnergyData, db: str = None):
    return adapter.update_energy_data_by_date(date_id, data, db=db)


def send_meta(field: str, meta: Union[int, float, bool, str, None], db: str = None):
    adapter.update_meta(field, value=meta, db=db)


def get_view_daily_consumption(date: str, db: str):
    return adapter.view_daily_consumption(date=date, db=db)
