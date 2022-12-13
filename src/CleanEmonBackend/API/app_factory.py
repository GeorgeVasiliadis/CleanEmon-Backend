"""This defines the FastAPI boostrap function"""

import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse

from ..Devices.devices import Devices

devices = Devices()


def create_app():
    """Creates the FastAPI app"""

    from .API import get_data
    from .API import get_range_data
    from .API import get_date_consumption
    from .API import get_mean_consumption
    from .API import get_plot
    from .API import get_meta
    from .API import has_meta
    from .API import set_meta_field

    from ..lib.exceptions import BadDateError
    from ..lib.exceptions import BadDateRangeError
    from ..lib.exceptions import BadDeviceNonExistent

    from ..lib.validation import is_valid_date
    from ..lib.validation import is_valid_date_range

    meta_tags = [
        {
            "name": "Views",
            "description": "Essential views"
        },
        {
            "name": "Experimental",
            "description": "Cutting-edge features that may not be stable yet"
        },
        {
            "name": "Metadata",
            "description": "Access, edit metadata"
        }
    ]

    app = FastAPI(openapi_tags=meta_tags, swagger_ui_parameters={"defaultModelsExpandDepth": -1})

    def parse_date(date: str) -> str:
        """Simple date parser. A date can either be in a standard YYYY-MM-DD format or a predefined alias.
        If the given date is invalid, a BadDateError is being raised.
        """

        parsed_date: str

        if date.lower() == "today":
            parsed_date = datetime.date.today().isoformat()
        elif date.lower() == "yesterday":
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            parsed_date = yesterday.isoformat()
        elif is_valid_date(date):
            parsed_date = date
        else:
            raise BadDateError(date)

        return parsed_date

    def check_device_existence(device: str):
        """Simple check if device is registered to the JSON file.
        """
        if not devices.device_exist(device):
            raise BadDeviceNonExistent(device)

    @app.exception_handler(BadDateError)
    def bad_date_exception_handler(request: Request, exception: BadDateError):
        return JSONResponse(
            status_code=400,
            content={"message": f"Bad date ({exception.bad_date}), not in ISO format (YYYY-MM-DD)."}
        )

    @app.exception_handler(BadDateRangeError)
    def bad_date_range_exception_handler(request: Request, exception: BadDateRangeError):
        return JSONResponse(
            status_code=400,
            content={"message": f"Bad date range ({exception.bad_from_date} - {exception.bad_to_date}). Dates must "
                                f"be in ISO format (YYYY-MM-DD) and placed in correct order."}
        )

    @app.exception_handler(BadDeviceNonExistent)
    def bad_date_range_exception_handler(request: Request, exception: BadDeviceNonExistent):
        return JSONResponse(
            status_code=400,
            content={"message": f"Bad device ({exception.bad_device_non_existent}), is not registered."
                                f" Check /devices to verify which devices are registered."}

        )

    @app.get("/dev_id/{dev_id}/json/date/{date}", tags=["Views"])
    def get_json_date(dev_id: str = None, date: str = None, from_cache: bool = False, sensors: Optional[str] = None):
        """Returns the daily data the supplied **{date}** for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database.
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        if sensors:
            sensors = sensors.split(',')

        return get_data(parsed_date, from_cache, sensors, db=dev_id)

    @app.get("/dev_id/{dev_id}/json/range/{from_date}/{to_date}", tags=["Views"])
    def get_json_range(dev_id: str, from_date: str, to_date: str, from_cache: bool = False,
                       sensors: Optional[str] = None):
        """Returns the range data for the supplied range, from **{from_date}** to **{to_date}** for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **{from_date}**: A date in YYYY-MM-DD format
        - **to_date**: A date in YYYY-MM-DD format. It should be chronologically greater or equal to **{from_date}**
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database.
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        if not is_valid_date_range(from_date, to_date):
            raise BadDateRangeError(from_date, to_date)

        if sensors:
            sensors = sensors.split(',')

        return get_range_data(from_date, to_date, from_cache, sensors, db=dev_id)

    @app.get("/devices", tags=["Views"])
    def get_devices():
        """Returns the list of devices that are registered."""
        return devices.get_devices()

    @app.get("/dev_id/{dev_id}/plot/date/{date}", tags=["Experimental"])
    def get_plot_date(dev_id: str = None, date: str = None, from_cache: bool = False, sensors: Optional[str] = None):
        """Returns the plot of the specified data, as a JPEG image, for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database.
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        if sensors:
            sensors = sensors.split(',')

        plot_path = get_plot(parsed_date, from_cache, sensors, db=dev_id)

        return FileResponse(plot_path, media_type="image/jpeg")

    @app.get("/dev_id/{dev_id}/plot/range/{from_date}/{to_date}", tags=["Experimental"])
    def get_plot_range(dev_id: str, from_date: str, to_date: str, from_cache: bool = False,
                       sensors: Optional[str] = None):  # TODO Maybe implemented this feature if is necessary.
        """Under construction :)"""
        return JSONResponse(
            status_code=501,
            content={"message": "This feature is currently not implemented"}
        )

    @app.get("/dev_id/{dev_id}/json/date/{date}/consumption", tags=["Views"])
    def get_json_date_consumption(dev_id: str = None, date: str = None, from_cache: bool = False,
                                  simplify: bool = False):
        """Returns the power consumption for the given date.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        return get_date_consumption(parsed_date, from_cache, simplify, db=dev_id)

    @app.get("/dev_id/{dev_id}/json/date/{date}/mean-consumption", tags=["Experimental"])
    def get_json_date_mean_consumption(dev_id: str = None, date: str = None, from_cache: bool = False):
        """Returns the power consumption over the size of the building for the given date.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        return get_mean_consumption(parsed_date, from_cache, db=dev_id)

    @app.get("/dev_id/{dev_id}/meta/", tags=["Metadata"])
    @app.get("/dev_id/{dev_id}/meta/{field}", tags=["Metadata"])
    def get_json_meta(dev_id: str = None, field: str = None):
        """Returns the metadata for the current house.
        - **{dev_id}**: The dev_id of the device.
        - **{meta}**: Optional endpoint that specifies the field to be returned if it exists in metadata, otherwise an
        empty dict will be returned. If omitted, all meta fields will be returned.
        """
        check_device_existence(dev_id)
        return get_meta(field, db=dev_id)

    @app.get("/dev_id/{dev_id}/has-meta/{field}", tags=["Metadata"])
    def get_has_meta(dev_id: str, field: str):
        """Returns true if given **{field}** exists as metadata field for device with **{field}** , and it is not equal to string "null".
        """
        check_device_existence(dev_id)
        return has_meta(field, db=dev_id)

    @app.get("/dev_id/{dev_id}/set-meta/{field}/", tags=["Metadata"])
    @app.get("/dev_id/{dev_id}/set-meta/{field}/{value}", tags=["Metadata"])
    def set_meta(dev_id: str, field: str, value: str = None):
        """Set meta field. If field exist it is getting update.
        """
        check_device_existence(dev_id)
        set_meta_field(field, value, db=dev_id)

    return app
