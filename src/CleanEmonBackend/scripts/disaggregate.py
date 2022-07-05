from CleanEmonCore import CONFIG_FILE
from CleanEmonCore.CouchDBAdapter import CouchDBAdapter

from CleanEmonBackend.Disaggregator.service import update

adapter = CouchDBAdapter(CONFIG_FILE)
print(f"You are working on database: {adapter.db}")


def _disaggregate(date: str):
    print(f"Working on {date}")
    print("Disaggregating...")
    update(date)
    print("Done")


def disaggregate(*dates: str, no_prompt=False):
    for date in dates:
        if no_prompt:
            ans = True
        else:
            ans = input(f"Proceed with {date}? (<enter>: no) ")

        if ans:
            _disaggregate(date)
        else:
            break
