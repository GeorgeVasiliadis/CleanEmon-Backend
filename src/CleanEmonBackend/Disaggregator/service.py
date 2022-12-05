from datetime import date
from datetime import timedelta

from CleanEmonCore.Events import Observer
from CleanEmonCore.Events.builtins import DateChange

from ..lib.DBConnector import fetch_data
from ..lib.DBConnector import send_data

from ..Disaggregator import energy_data_to_dataframe
from ..Disaggregator import dataframe_to_energy_data
from ..Disaggregator import disaggregate


def update(yesterday: str):
    # Right now the disaggregation will occur for only one device, list devices has one element.
    # There should be a list of devices (different databases).
    # Improvements maybe create a parallel processing of each device energy_data.
    # TODO Improvement: Create a class devices, that reads all the devices form either CouchDB or a local file.
    devices = ['emon01']
    for device in devices:
        energy_data = fetch_data(yesterday, db=device)
        df = energy_data_to_dataframe(energy_data)

        df = disaggregate(df)
        dis_energy_data = dataframe_to_energy_data(df)
        send_data(yesterday, dis_energy_data, db=device)


def run():
    class Updater(Observer):
        def on_notify(self, *args, **kwargs):
            if "date" in kwargs:
                yesterday = kwargs["date"]
            else:  # By default, get the previous date
                yesterday = date.today() - timedelta(days=1)
            update(str(yesterday))

    event = DateChange(3, initial_date=date.today())  # todo: increase interval to reduce execution time?
    Updater(event)

    event.run()
