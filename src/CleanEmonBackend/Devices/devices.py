"""This module defines the devices"""

from CleanEmonCore import DEVICES_FILE
from CleanEmonCore.json_utils.json_utils import verify_json, read_json_file
from CleanEmonCore.json_utils.schemas import schema_devices


class Devices:
    """Devices class used to just to check to parse the JSON file under the .CleanEmon directory."""

    def __init__(self):
        self.devices = verify_json(read_json_file(DEVICES_FILE), schema_devices)['devices']
        self.devices_set = dict(self.devices)

    def get_devices(self):
        return self.devices

    def device_exist(self, device):
        if device in self.devices_set:
            return True
        else:
            return False