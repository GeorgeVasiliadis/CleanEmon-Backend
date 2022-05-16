import pytest

from CleanEmonCore.models import EnergyData
from CleanEmonBackend.lib.DBConnector import fetch_data
from CleanEmonBackend.lib.DBConnector import send_data

DUMMY_DATE = "2000-01-01"


@pytest.fixture
def energy_data():
    return EnergyData(DUMMY_DATE, [
        {"timestamp": 1, "power": 1, "temp": 1},
        {"timestamp": 2, "power": 2, "temp": 2},
        {"timestamp": 3, "power": 3, "temp": 3}
    ])


@pytest.mark.projectwise
def test_fetch_data():
    data = fetch_data("2022-05-01")
    assert data
    assert type(data) is EnergyData

    data = fetch_data("2022-05-01", from_clean_db=True)
    assert not data.energy_data


@pytest.mark.projectwise
def test_send_data(energy_data):
    assert send_data(DUMMY_DATE, energy_data)
