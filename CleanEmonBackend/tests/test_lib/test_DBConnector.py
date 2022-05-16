import pytest

from CleanEmonCore.models import EnergyData
from CleanEmonBackend.lib.DBConnector import fetch_data


@pytest.mark.projectwise
def test_fetch_data():
    data = fetch_data("2022-05-01")
    assert data
    assert type(data) is EnergyData
