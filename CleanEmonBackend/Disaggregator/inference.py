from typing import List

import pandas as pd

from ..lib.black_sorcery import nilm_path_fix


def disaggregate(df: pd.DataFrame, timestamp_label: str = "timestamp", target_label: str = "power") -> List[str]:
    with nilm_path_fix():

        # ------------------------------------------------------#
        # Extremely ~spooky~ and error prune piece of code      #
        # Just for the history, this was deprecated since the   #
        # time of writing.                                      #
        #                                                       #
        # Uncle Bob, if you are reading, please forgive me :(   #
        # ------------------------------------------------------#
        from lab.nilm_trainer import nilm_inference
        from constants.enumerates import ElectricalAppliances
        from constants.enumerates import WaterAppliances

        # Consider all known devices
        devices = list(ElectricalAppliances) + list(WaterAppliances)
        devices = [dev.value for dev in devices]

        return nilm_inference(devices=devices, sample_period=5)
