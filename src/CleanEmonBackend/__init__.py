import os

from CleanEmonCore.dotfiles import get_dotfile
from CleanEmonCore.dotfiles import DOT_DIR_PATH

DATA_DIR = os.path.join(DOT_DIR_PATH, "data")
RES_DIR = os.path.join(DOT_DIR_PATH, "res")

# Ensure that the data dir exists
if not os.path.isdir(DATA_DIR):
    os.mkdir(DATA_DIR)

CACHE_DIR = os.path.join(DATA_DIR, "cache")
PLOT_DIR = os.path.join(DATA_DIR, "plots")

# --- NILM-Inference-APIs ---
_NILM_CONFIG = "NILM-Inference-APIs.path"
NILM_CONFIG = get_dotfile(_NILM_CONFIG)
with open(NILM_CONFIG, "r") as f_in:
    NILM_INFERENCE_APIS_DIR = f_in.read().strip()

NILM_INPUT_DIR = os.path.join(NILM_INFERENCE_APIS_DIR, "input", "data")
if not os.path.exists(NILM_INPUT_DIR):
    os.makedirs(NILM_INPUT_DIR, exist_ok=True)

NILM_INPUT_FILE_PATH = os.path.join(NILM_INPUT_DIR, "data.csv")
