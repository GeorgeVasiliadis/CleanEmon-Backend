"""This defines the FastAPI boostrap function"""

import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
import orjson
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse

from ..Devices.devices import Devices
from ..lib.exceptions import MissingEnergyData

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
    from ..lib.exceptions import MissingMetadataField

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

    app = FastAPI(openapi_tags=meta_tags, swagger_ui_parameters={"defaultModelsExpandDepth": -1,
                                                                 "syntaxHighlight": False})

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

    @app.exception_handler(MissingEnergyData)
    def missing_energy_data_handler(request: Request, exception: MissingEnergyData):
        return JSONResponse(
            status_code=400,
            content={"message": f"Can't find enough Energy Data to do the calculations."
                                f" Make sure the device is turn on, configured correctly and is recording data"}

        )

    @app.exception_handler(MissingMetadataField)
    def missing_metadata_field_handler(request: Request, exception: MissingMetadataField):
        return JSONResponse(
            status_code=400,
            content={"message": f"Can't find the field '{exception.field_name}' for this device."
                                f" Please ensure that the field '{exception.field_name} ' has been specified in the "
                                f"metadata for this device."}
        )

    @app.get("/dev_id/{dev_id}/json/date/{date}", tags=["Views"])
    async def get_json_date(dev_id: str = None, date: str = None, from_cache: bool = False, sensors: Optional[str] = None) -> Response:
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

        return Response(
            content=orjson.dumps(get_data(parsed_date, from_cache, sensors, db=dev_id)),
            media_type="application/json"
        )

        # return get_data(parsed_date, from_cache, sensors, db=dev_id)

        # return get_data(parsed_date, from_cache, sensors, db=dev_id)

    # a)
    @app.get("/dev_id/{dev_id}/json/last_value", tags=["Views"])
    def get_json_last_value(dev_id: str = None, sensors: Optional[str] = None):
        """Returns the last value from today for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date("today")

        if sensors:
            sensors = sensors.split(',')

        return get_data(parsed_date, False, sensors, db=dev_id, keep_last_only=True)

    @app.get("/dev_id/{dev_id}/json/range/{from_date}/{to_date}", tags=["Views"])
    def get_json_range(dev_id: str, from_date: str, to_date: str, from_cache: bool = False,
                       sensors: Optional[str] = None):
        """Returns the range data for the supplied range, from **{from_date}** to **{to_date}** for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
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

        return Response(
            content=orjson.dumps(get_range_data(from_date, to_date, from_cache, sensors, db=dev_id)),
            media_type="application/json"
        )
        #return get_range_data(from_date, to_date, from_cache, sensors, db=dev_id)

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

    # b)
    @app.get("/dev_id/{dev_id}/json/yesterday/consumption", tags=["Views"])
    def get_json_yesterday_consumption(dev_id: str = None, from_cache: bool = False, simplify: bool = False):
        """Returns the power consumption of yesterday.
        - **{dev_id}**: The dev_id of the device.
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date("yesterday")

        return get_date_consumption(parsed_date, from_cache, simplify, db=dev_id)

    # g
    @app.get("/dev_id/{dev_id}/json/last_month/consumption", tags=["Views"])
    def get_json_last_month_consumption(dev_id: str = None, from_cache: bool = False, simplify: bool = False):
        """Returns the power consumption from the first day until the last day of last month.
        - **{dev_id}**: The dev_id of the device.
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)

        days = get_last_month_days()
        consumptions = [get_date_consumption(_.strftime('%Y-%m-%d'), from_cache, True, db=dev_id) for _ in days]
        number_of_empty_days = consumptions.count(0)
        missing_data = True if number_of_empty_days != 0 else False

        number_of_non_empty_days = len(consumptions) - number_of_empty_days
        if missing_data:
            if number_of_non_empty_days == 0:
                result = 0
            else:
                result = (sum(consumptions) / number_of_non_empty_days) * len(consumptions)  # Trying to estimate
        else:
            result = sum(consumptions)

        if simplify:
            return result
        return {"consumption": result,
                "unit": "kwh",
                "month": days[0].strftime('%B'),
                "missing_data": missing_data,
                "number_of_days_that_energy_data_exist": number_of_non_empty_days,
                "number_of_days_that_energy_data_dont_exist": number_of_empty_days if missing_data else ""
                }

    @app.get("/dev_id/{dev_id}/json/30days/average_consumption", tags=["Views"])
    def get_json_30days_average_consumption(dev_id: str = None, from_cache: bool = False, simplify: bool = False):
        """Returns the average daily consumption in the last 30 days.
        - **{dev_id}**: The dev_id of the device.
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)

        days = [datetime.date.today() - datetime.timedelta(days=i) for i in range(29, -1, -1)]  # last 30 days
        consumptions = [get_date_consumption(_.strftime('%Y-%m-%d'), from_cache, True, db=dev_id) for _ in days]
        # If missing date exist make the window smaller
        window_start_pos = 0
        window_end_pos = len(consumptions) - 1

        while consumptions[window_end_pos] == 0 and window_end_pos - window_start_pos > 3:
            window_end_pos -= 1

        while consumptions[window_start_pos] == 0 and window_end_pos - window_start_pos > 3:
            window_start_pos += 1

        if window_end_pos - window_start_pos <= 3:
            raise MissingEnergyData("")

        missing_data_within_the_window = False if consumptions[window_start_pos:window_end_pos + 1].count(
            0) == 0 else True

        result = sum(consumptions[window_start_pos:window_end_pos + 1]) / len(
            consumptions[window_start_pos:window_end_pos + 1])

        if simplify:
            return result
        return {"consumption": result,
                "unit": "kwh",
                "window_start_day": days[window_start_pos].strftime('%Y-%m-%d'),
                "window_end_day": days[window_end_pos].strftime('%Y-%m-%d'),
                "window_size": window_end_pos - window_start_pos,
                "missing_data_within_window": missing_data_within_the_window,
                "start": window_start_pos,
                "end": window_end_pos
                }

    @app.get("/dev_id/{dev_id}/json/30days/average_consumption_div_home_size", tags=["Views"])
    def get_json_30days_average_consumption_div_home_size(dev_id: str = None, from_cache: bool = False):
        """Returns the average daily consumption in the last 30 days divided by the size of the home
        - **{dev_id}**: The dev_id of the device.
        - **from_cache**: If set to False, forces data to be fetched again from the central database. If set to True,
        data will be looked up in cache and then, if they are not found, fetched from the central database
        """
        if has_meta("size", dev_id):
            home_size = float(get_meta("size", dev_id))
        else:
            raise MissingMetadataField('size')
        return float(get_json_30days_average_consumption(dev_id, from_cache, simplify=True)) / home_size

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
        res = get_mean_consumption(parsed_date, from_cache, db=dev_id)
        if res == -1:
            raise MissingMetadataField('size')
        return res

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


def get_last_month_days():
    end_last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    start_last_month = end_last_month.replace(day=1)  # first day of the last month
    delta = end_last_month - start_last_month

    days = [start_last_month + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    return days


