import os
from typing import List, Tuple, Any

import numpy as np
import pandas as pd

from CleanEmonBackend import NILM_INPUT_FILE_PATH
from CleanEmonBackend import NILM_INPUT_DIR
from CleanEmonBackend.lib.black_sorcery import nilm_path_fix


def _set_inference_input(df: pd.DataFrame) -> bool:
    df = df.copy()

    # Reformat as expected by NILM-Inference-APIs like "2022-05-16 00:00:17+01:00"
    df["Time"] = pd.to_datetime(df["Time"], unit='s')
    if not os.path.exists(NILM_INPUT_DIR):
        os.makedirs(NILM_INPUT_DIR, exist_ok=True)

    df.to_csv(NILM_INPUT_FILE_PATH, index=False)
    return True


def _disaggregate_to_files(meta) -> List[Tuple[str, str]]:
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

        # Consider all known appliances
        appliances = list(ElectricalAppliances)  # Here appliances should not be confused with Device class (EmonPi) but
        # rather the Electrical Appliances.
        appliances = [dev.value for dev in appliances]

        appliances_in_household = []

        for _ in appliances:
            underscore_name = _.replace(" ", "_").lower()
            if underscore_name in meta and meta[underscore_name]:
                appliances_in_household.append(_)

        return nilm_inference(devices=appliances_in_household, sample_period=5, inference_cpu=True)


def disaggregate(df: pd.DataFrame, timestamp_label: str = "timestamp", target_label: str = "power",
                 meta=None) -> pd.DataFrame:
    df = df.copy()

    # Filter unneeded columns
    df_filtered = df.loc[:, [timestamp_label, target_label]]
    df_filtered[target_label] = df_filtered[target_label].fillna(df_filtered[target_label].mean().round())
    df_filtered = df_filtered.rename(columns={timestamp_label: "Time", target_label: "mains"})

    # Write dataframe to input file
    _set_inference_input(df_filtered)

    # Inference
    devices_files = _disaggregate_to_files(meta)

    # Read data back into memory
    appliances_names_to_sum = []
    for device, file in devices_files:
        temp_df = pd.read_csv(file)
        first_n_missing = df.shape[0] - temp_df.shape[0]

        col_name = device.lower().replace(" ", "_")
        col_name = f"pred_{col_name}"

        preds = pd.concat([pd.Series(np.zeros(first_n_missing)), temp_df["preds"]])

        preds[preds < 0] = 0  # replace all negatives with 0; pred_XXX = max (0,pred_XXX)
        max_pred = preds.max()  # find max

        max_scale = meta["max_scale_" + device.lower().replace(" ", "_")]
        preds = preds.apply(lambda x: x * max_scale / max_pred)
        df[col_name] = preds.values
        appliances_names_to_sum.append(col_name)

    sum_ab = df[appliances_names_to_sum].sum(axis=1)
    df['noise'] = df['power'] - sum_ab
    # Clear rows that originally had NaN as target value, but keep timestamps
    df.loc[df[target_label].isna(), df.columns != timestamp_label] = np.NaN

    return df
