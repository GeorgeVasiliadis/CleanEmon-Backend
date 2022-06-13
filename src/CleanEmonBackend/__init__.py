import os

from CleanEmonCore.dotfiles import get_dotfile

from .setup import generate_nilm_inference_apis_config

PACKAGE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(PACKAGE_DIR, "data")
RES_DIR = os.path.join(PACKAGE_DIR, "res")

# Ensure that the `$PACKAGE/data` dir exists
if not os.path.isdir(DATA_DIR):
    os.mkdir(DATA_DIR)

CACHE_DIR = os.path.join(DATA_DIR, "cache")
PLOT_DIR = os.path.join(DATA_DIR, "plots")

# --- NILM-Inference-APIs ---
_NILM_CONFIG = "NILM-Inference-APIs.path"
NILM_CONFIG = get_dotfile(_NILM_CONFIG, generate_nilm_inference_apis_config)
with open(NILM_CONFIG, "r") as f_in:
    NILM_INFERENCE_APIS_DIR = f_in.read().strip()

NILM_INPUT_DIR = os.path.join(NILM_INFERENCE_APIS_DIR, "input", "data")
if not os.path.exists(NILM_INPUT_DIR):
    os.makedirs(NILM_INPUT_DIR, exist_ok=True)

NILM_INPUT_FILE_PATH = os.path.join(NILM_INPUT_DIR, "data.csv")
