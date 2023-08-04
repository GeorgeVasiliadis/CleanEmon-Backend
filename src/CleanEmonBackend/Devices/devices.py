"""This module defines the devices"""

from CleanEmonBackend.lib.DBConnector import get_devices


class Devices:
    """Devices class used to just to check to parse the JSON file under the .CleanEmon directory."""

    def __init__(self):
        self.devices_set = set(get_devices())

    def get_devices(self):
        return self.devices_set

    def device_exist(self, device):
        if device in self.devices_set:
            return True
        else:
            return False
