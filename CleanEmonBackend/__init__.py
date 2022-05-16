import os

PACKAGE_DIR = os.path.dirname(__file__)

CACHE_DIR = os.path.join(PACKAGE_DIR, "cache")
PLOT_DIR = os.path.join(PACKAGE_DIR, "plots")

NILM_INFERENCE_APIS_DIR = "/home/george/PycharmProjects/CleanEmon/NILM-Inference-APIs"  # todo: Procedural definition
assert os.path.exists(NILM_INFERENCE_APIS_DIR), (
    f"Please specify the directory of NILM-Inference-APIs at `NILM_INFERENCE_APIS_DIR` in {__file__} and re-run"
)
NILM_INFERENCE_APIS_DIR = os.path.abspath(NILM_INFERENCE_APIS_DIR)

NILM_INPUT_DIR = os.path.join(NILM_INFERENCE_APIS_DIR, "input", "data")
if not os.path.exists(NILM_INPUT_DIR):
    os.makedirs(NILM_INPUT_DIR, exist_ok=True)

NILM_INPUT_FILE_PATH = os.path.join(NILM_INPUT_DIR, "data.csv")