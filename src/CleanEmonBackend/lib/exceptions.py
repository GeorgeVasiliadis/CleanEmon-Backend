class BadDateError(ValueError):
    def __init__(self, bad_date: str):
        self.bad_date = bad_date


class BadDateRangeError(ValueError):
    def __init__(self, bad_from_date: str, bad_to_date):
        self.bad_from_date = bad_from_date
        self.bad_to_date = bad_to_date


class BadDeviceNonExistent(ValueError):
    def __init__(self, bad_device_non_existent: str):
        self.bad_device_non_existent = bad_device_non_existent


class MissingEnergyData(ValueError):
    def __init__(self, missing_energy_data: str):
        self.missing_energy_data = missing_energy_data


class MissingMetadataField(ValueError):
    def __init__(self, field_name: str):
        self.field_name = field_name


class SchemaValidationForMetaFailed(ValueError):
    def __init__(self, message: str):
        self.message = message
