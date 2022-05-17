import os
import json

import pandas as pd
import pytest

from CleanEmonCore.models import EnergyData

from CleanEmonBackend.Disaggregator.preparation import energy_data_to_dataframe


@pytest.fixture
def energy_data() -> EnergyData:
    directory = os.path.dirname(__file__)
    file = os.path.join(directory, "energy_data.json")

    with open(file, "r") as fp:
        data_dict = json.load(fp)

    return EnergyData(data_dict["date"], data_dict["energy_data"])


def test_energy_data_to_dataframe(energy_data):
    old_cols = energy_data.energy_data[0].keys()
    df = energy_data_to_dataframe(energy_data)

    assert len(df.columns) == len(old_cols) + 1
    assert df.shape[0] == 17280
    assert any([("original" in col) for col in df.columns])
