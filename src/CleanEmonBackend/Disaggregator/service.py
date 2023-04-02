from datetime import date
import time
from datetime import timedelta

from CleanEmonCore.Events import Observer
from CleanEmonCore.Events.builtins import DateChange

from ..lib.DBConnector import fetch_data
from ..lib.DBConnector import send_data

from ..Disaggregator import energy_data_to_dataframe
from ..Disaggregator import dataframe_to_energy_data
from ..Disaggregator import disaggregate

from ..Devices.devices import Devices

devices = Devices()


def update(yesterday: str):
    # TODO : Maybe add multiprocessing with threads to speed up. Check this:
    # https://stackoverflow.com/questions/15143837/how-to-multi-thread-an-operation-within-a-loop-in-python
    time.sleep(60 * 10)  # wait for 10 minutes before starting the disaggregation process.
    # The disaggregation process begins precisely at 00:00. However, since each device sends a burst of sensor values
    # every 5 minutes, it's possible for the disaggregation process to start before all the data for the day has been
    # saved to the database.

    for _ in devices.get_devices():  # For every registered device do the disaggregation.
        energy_data = fetch_data(yesterday, db=_)
        if len(energy_data.energy_data) == 0:  # If no data is available for this device skip it completely
            continue
        df = energy_data_to_dataframe(energy_data)

        df = disaggregate(df)
        dis_energy_data = dataframe_to_energy_data(df)
        send_data(yesterday, dis_energy_data, db=_)


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
