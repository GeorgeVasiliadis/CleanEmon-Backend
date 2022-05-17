import pytest

from CleanEmonBackend.Disaggregator.inference import disaggregate


@pytest.mark.slow
def test_disaggregate(dataframe):
    files = disaggregate(dataframe)
    assert files
