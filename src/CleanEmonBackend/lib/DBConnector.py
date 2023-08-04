"""This module contains a set of utilities used to transform and prepare data for torch-nilm inference"""

from typing import Union

from CleanEmonCore import CONFIG_FILE
from CleanEmonCore.CouchDBAdapter import CouchDBAdapter
from CleanEmonCore.models import EnergyData

adapter = CouchDBAdapter(CONFIG_FILE)


def fetch_document(document: str, db: str):
    return adapter._fetch_document(document=document, db=db)


def create_document(document: str, db: str, data):
    return adapter.create_document(name=document, db=db, initial_data=data)


def fetch_data(date_id: str, *, db: str = None, down_sampling: bool = False) -> EnergyData:
    energy_data = adapter.fetch_energy_data_by_date(date_id, db=db, down_sampling=down_sampling)

    return energy_data


def get_last_value(db: str):
    return adapter.get_last_energy_data_record(db)


def send_data(date_id: str, data: EnergyData, db: str = None):
    return adapter.update_energy_data_by_date(date_id, data, db=db)


def send_meta(field: str, meta: Union[int, float, bool, str, None], db: str = None):
    adapter.update_meta(field, value=meta, db=db)


def get_view_daily_consumption(date: str, db: str):
    return adapter.view_daily_consumption(date=date, db=db)


def get_devices():
    return adapter.get_devices()
