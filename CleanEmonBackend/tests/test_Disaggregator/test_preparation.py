import pytest

from CleanEmonBackend.Disaggregator.preparation import NILM_INPUT_FILE_PATH
from CleanEmonBackend.Disaggregator.preparation import date_to_input_file


@pytest.mark.projectwise
def test_date_to_input_file():
    import os

    last_modify_time = 0
    if os.path.exists(NILM_INPUT_FILE_PATH):
        last_modify_time = os.path.getmtime(NILM_INPUT_FILE_PATH)

    date_to_input_file("2022-05-01")
    assert os.path.exists(NILM_INPUT_FILE_PATH)
    assert os.path.getmtime(NILM_INPUT_FILE_PATH) != last_modify_time
