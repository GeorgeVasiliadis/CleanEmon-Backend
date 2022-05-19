from datetime import date

from CleanEmonCore.Events import Observer
from CleanEmonCore.Events.builtins import DateChange

from ..lib.DBConnector import fetch_data
from ..lib.DBConnector import send_data

from ..Disaggregator import energy_data_to_dataframe
from ..Disaggregator import dataframe_to_energy_data
from ..Disaggregator import disaggregate


def update(new_date: str):
    energy_data = fetch_data(new_date, from_clean_db=False)  # todo: begone from_clean_db
    df = energy_data_to_dataframe(energy_data)

    df = disaggregate(df)
    dis_energy_data = dataframe_to_energy_data(df)
    # send_data(new_date, dis_energy_data, to_clean_db=False)  # todo: begone to_clean_db


def run():
    class Updater(Observer):
        def on_notify(self, *args, **kwargs):
            if "date" in kwargs:
                new_date = str(kwargs["date"])
            else:
                new_date = str(date.today())  # todo: make it send the previous date (aka yesterday)
            update(new_date)

    event = DateChange(3, initial_date=date.today())  # todo: increase interval to reduce execution time?
    Updater(event)

    event.run()
