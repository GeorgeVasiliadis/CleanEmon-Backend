from datetime import date
from datetime import timedelta

from CleanEmonCore.Events import Observer
from CleanEmonCore.Events.builtins import DateChange

from CleanEmonBackend.lib.DBConnector import fetch_data
from CleanEmonBackend.lib.DBConnector import send_data

from CleanEmonBackend.Disaggregator import energy_data_to_dataframe
from CleanEmonBackend.Disaggregator import dataframe_to_energy_data
from CleanEmonBackend.Disaggregator import disaggregate

from CleanEmonBackend.Devices.devices import Devices

devices = Devices()


def update(yesterday: str, device_id: str = None):
    # TODO : Maybe add multiprocessing with threads to speed up. Check this:
    # https://stackoverflow.com/questions/15143837/how-to-multi-thread-an-operation-within-a-loop-in-python
    for device in devices.get_devices():  # For every registered device do the disaggregation.
        if device_id is not None and device_id != device:
            continue
        energy_data = fetch_data(yesterday, db=device)
        if len(energy_data.energy_data) == 0:  # If no data is available for this device skip it completely
            continue
        print("run for device", device)
        df = energy_data_to_dataframe(energy_data)
        import CleanEmonBackend.API.API
        meta = CleanEmonBackend.API.API.get_meta(field=None, db=device)
        df = disaggregate(df, meta=meta)
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

    event = DateChange(60 * 5, initial_date=date.today())  # increase interval to reduce execution time to 5 minutes
    Updater(event)

    event.run()
