"""This module contains a set of utilities used to transform and prepare data for torch-nilm inference"""

import os
import json

from CleanEmonCore import CONFIG_FILE
from CleanEmonCore.models import EnergyData
from CleanEmonCore.CouchDBAdapter import CouchDBAdapter

from .. import CACHE_DIR


def fetch_data(date_id, *, from_cache=False) -> EnergyData:

    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    cache_path = os.path.join(CACHE_DIR, date_id)

    fetch_ok = False

    energy_data = EnergyData()

    if from_cache:
        try:
            with open(cache_path, "r") as fin:
                raw_data = json.load(fin)
                energy_data = EnergyData(raw_data["date"], raw_data["energy_data"])

            print("Fetched data from cache")
            fetch_ok = True
        except OSError:
            print("No cached data!")

    if not from_cache or not fetch_ok:
        adapter = CouchDBAdapter(CONFIG_FILE)

        energy_data = adapter.fetch_energy_data_by_date(date_id)

        # Cache data for future use
        with open(cache_path, "w") as fout:
            json.dump(energy_data.as_json(string=False), fout)

    return energy_data


def send_data(date_id):
    pass