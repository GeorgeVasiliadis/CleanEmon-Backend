from CleanEmonCore import CONFIG_FILE
from CleanEmonCore.CouchDBAdapter import CouchDBAdapter

from CleanEmonBackend.Disaggregator.service import update


def _disaggregate(date: str, device_id: str):
    print(f"Working on {date}")
    print("Disaggregating...")
    update(date, device_id=device_id)
    print("Done")


def disaggregate(*dates: str, device_id: str, no_prompt=False):
    for date in dates:
        if no_prompt:
            ans = True
        else:
            ans = input(f"Proceed with {date}? (<enter>: no) ")

        if ans:
            _disaggregate(date, device_id)
        else:
            break
