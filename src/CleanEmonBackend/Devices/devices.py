"""This module defines the devices"""
import json

from CleanEmonCore import DEVICES_FILE


def read_json_file(path):
    with open(path) as json_file:
        data = json.load(json_file)
    return data


class Devices:
    def __init__(self):
        try:
            self.devices = read_json_file(DEVICES_FILE)['devices']

            self.devices_set = set(self.devices)
            self.__validate_input()
        except KeyError:
            print("ERROR!\nThe provided Devices JSON is in wrong form.\nCheck the schema")
        except json.JSONDecodeError:
            print("ERROR!\nThe provided JSON file is not a valid JSON!\nCheck the schema")

    def get_devices(self):
        return self.devices

    def device_exist(self, device):
        if device in self.devices_set:
            return True
        else:
            return False

    def __validate_input(self):
        if not self.__is_unique():
            print("Found duplicate device names")

    def __is_unique(self) -> bool:
        # Check if duplicate name for devices exist
        if len(self.devices) == len(self.devices_set):
            return True
        else:
            return False


# if __name__ == '__main__':
#     x = Devices()
#     z = x.get_devices()
#     print(z)

