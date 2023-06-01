import os

from CleanEmonCore.dotfiles import get_dotfile

# --- NILM-Inference-APIs ---
_NILM_CONFIG = "NILM-Inference-APIs.path"
NILM_CONFIG = get_dotfile(_NILM_CONFIG)
with open(NILM_CONFIG, "r") as f_in:
    NILM_INFERENCE_APIS_DIR = f_in.read().strip()

NILM_INPUT_DIR = os.path.join(NILM_INFERENCE_APIS_DIR, "input", "data")
if not os.path.exists(NILM_INPUT_DIR):
    os.makedirs(NILM_INPUT_DIR, exist_ok=True)

NILM_INPUT_FILE_PATH = os.path.join(NILM_INPUT_DIR, "data.csv")
