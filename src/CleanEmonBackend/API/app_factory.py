"""This defines the FastAPI boostrap function"""

import datetime
from typing import Optional
from typing import Union

import CleanEmonCore.json_utils.schemas
import orjson
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi import Request, Form
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.responses import StreamingResponse
from typing_extensions import Annotated

from CleanEmonBackend.API.API import fetch_account_info, create_account, get_preds_consumption, get_dates_consumptions
from CleanEmonBackend.Devices.devices import Devices
from CleanEmonBackend.lib.authenticator_config import SECRET_KEY, ALGORITHM, Token, TokenData, UserInDB, User, \
    is_couchdb_safe_username
from CleanEmonBackend.lib.exceptions import MissingEnergyData

devices = Devices()

ACCESS_TOKEN_EXPIRE_WEEKS = 52  # 1 year

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(fake_db, username: str):
    if user_exists(fake_db, username):
        return UserInDB(**fake_db)
    return None


def user_exists(fake_db, username: str):
    if 'username' in fake_db and fake_db['username'] == username:
        return True
    return False


def authenticate_user(account_info, username: str, password: str):
    user = get_user(account_info, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})  # Add expiration date to token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fetch_account_info(token_data.username), username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Inactive user, please kindly ask the system admin to activate your account")
    return current_user


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
    from ..lib.exceptions import SchemaValidationForMetaFailed

    from ..lib.validation import is_valid_date
    from ..lib.validation import is_valid_date_range

    meta_tags = [
        {
            "name": "Authorization",
            "description": "Authenticate using a bearer token"
        },
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

    from fastapi.middleware.cors import CORSMiddleware
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


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

    @app.exception_handler(SchemaValidationForMetaFailed)
    def schema_validation_for_meta_failed_handler(request: Request, exception: SchemaValidationForMetaFailed):
        return JSONResponse(
            status_code=400,
            content={"message": f"Can't change meta field because : {exception.message}"}
        )

    @app.post("/token", response_model=Token, tags=["Authorization"])
    async def login_for_access_token(username: str = Form(...),
                                     password: str = Form(...)):
        username = username.lower()
        if not (is_couchdb_safe_username(username)):
            raise HTTPException(
                status_code=400, detail="The username contains invalid characters. Only lowercase letters, numbers, "
                                        "and the characters '_', '$', '(', ')', and '/' are allowed."
            )
        user = authenticate_user(fetch_account_info(username), username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if user.disabled:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Inactive user, please kindly ask the system admin to activate your account")
        access_token_expires = datetime.timedelta(weeks=15)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}

    @app.post("/register", tags=["Authorization"])
    async def register(username: str = Form(...),
                       password: str = Form(...)):
        username = username.lower()
        if not (is_couchdb_safe_username(username)):
            raise HTTPException(
                status_code=400, detail="The username contains invalid characters. Only lowercase letters, numbers, "
                                        "and the characters '_', '$', '(', ')', and '/' are allowed."
            )
        # Check if the username is already taken
        if user_exists(fetch_account_info(username), username):
            raise HTTPException(
                status_code=400, detail="Username already taken"
            )

        # Hash the password using a secure hash function

        new_user = UserInDB(username=username,
                            hashed_password=get_password_hash(password),
                            disabled=True)

        # Create the new user account
        if create_account(new_user):
            return {"message": "User created successfully, kindly ask you administrator to activate your account"}
        else:
            raise HTTPException(
                status_code=400, detail="Unknown error"
            )

    @app.get("/dev_id/{dev_id}/json/date/{date}", tags=["Views"])
    def get_json_date(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str = None,
                      date: str = None, downsampling: bool = False,
                      sensors: Optional[str] = None) -> Response:
        """Returns the daily data the supplied **{date}** for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **downsampling** : If set to True the returned signals interval has been increased thus return less data.
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        if sensors:
            sensors = sensors.split(',')

        return Response(
            content=orjson.dumps(get_data(parsed_date, sensors, db=dev_id, down_sampling=downsampling)),
            media_type="application/json"
        )

        # return get_data(parsed_date, from_cache, sensors, db=dev_id)

        # return get_data(parsed_date, from_cache, sensors, db=dev_id)

    # a)
    @app.get("/dev_id/{dev_id}/json/last_value", tags=["Views"])
    def get_json_last_value(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str = None,
                            sensors: Optional[str] = None):
        """Returns the last value from today for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)

        if sensors:
            sensors = sensors.split(',')

        return get_data(date=None, sensors=sensors, db=dev_id, keep_last_only=True)

    @app.get("/dev_id/{dev_id}/json/range/{from_date}/{to_date}", tags=["Views"])
    def get_json_range(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str, from_date: str,
                       to_date: str,
                       downsampling: bool = False,
                       sensors: Optional[str] = None):
        """Returns the range data for the supplied range, from **{from_date}** to **{to_date}** for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **to_date**: A date in YYYY-MM-DD format. It should be chronologically greater or equal to **{from_date}**
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        if not is_valid_date_range(from_date, to_date):
            raise BadDateRangeError(from_date, to_date)

        if sensors:
            sensors = sensors.split(',')

        return Response(
            content=orjson.dumps(get_range_data(from_date, to_date, sensors, db=dev_id, down_sampling=downsampling)),
            media_type="application/json"
        )
        # return get_range_data(from_date, to_date, from_cache, sensors, db=dev_id)

    @app.get("/dev_id/{dev_id}/days_consumptions/range/{from_date}/{to_date}", tags=["Views"])
    def get_days_consumption_range(current_user: Annotated[User, Depends(get_current_active_user)],
                                   dev_id: str, from_date: str, to_date: str, summarize: bool):
        """Returns the power consumption for the given dates in range from **{from_date}** to **{to_date}** for the
        device with **{dev_id}**. - **{dev_id}**: The dev_id of the device. - **to_date**: A date in YYYY-MM-DD
        format. It should be chronologically greater or equal to **{from_date}** -
        """
        check_device_existence(dev_id)
        if not is_valid_date_range(from_date, to_date):
            raise BadDateRangeError(from_date, to_date)

        return get_dates_consumptions(from_date, to_date, dev_id, summarize)

    @app.get("/dev_id/{dev_id}/pred_consumption/range/{from_date}/{to_date}", tags=["Views"])
    def get_pred_consumption_range(current_user: Annotated[User, Depends(get_current_active_user)],
                                   dev_id: str, from_date: str, to_date: str, summarize: bool):
        """Returns consumption of each pred, from **{from_date}** to **{to_date}** for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **to_date**: A date in YYYY-MM-DD format. It should be chronologically greater or equal to **{from_date}**
        """
        check_device_existence(dev_id)
        if not is_valid_date_range(from_date, to_date):
            raise BadDateRangeError(from_date, to_date)

        return get_preds_consumption(from_date, to_date, dev_id, summarize)

    @app.get("/devices", tags=["Views"])
    def get_devices(current_user: Annotated[User, Depends(get_current_active_user)]):
        """Returns the list of devices that are registered."""
        return devices.get_devices()

    @app.get("/dev_id/{dev_id}/plot/date/{date}", tags=["Experimental"])
    def get_plot_date(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str = None,
                      date: str = None, sensors: Optional[str] = None):
        """Returns the plot of the specified data, as an SVG vector image, for the device with **{dev_id}**.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **sensors**: A comma (,) separated list of sensors to be returned. If present, only sensors defined in that
        list will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        if sensors:
            sensors = sensors.split(',')

        return StreamingResponse(get_plot(parsed_date, sensors, db=dev_id), media_type="image/svg+xml")

    # @app.get("/dev_id/{dev_id}/plot/range/{from_date}/{to_date}", tags=["Experimental"])
    # def get_plot_range(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str, from_date: str,
    #                    to_date: str, from_cache: bool = False,
    #                    sensors: Optional[str] = None):  # TODO Maybe implemented this feature if is necessary.
    #     """Under construction :)"""
    #     return JSONResponse(
    #         status_code=501,
    #         content={"message": "This feature is currently not implemented"}
    #     )

    @app.get("/dev_id/{dev_id}/json/date/{date}/consumption", tags=["Views"])
    def get_json_date_consumption(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str = None,
                                  date: str = None,
                                  simplify: bool = False):
        """Returns the power consumption for the given date.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)

        return get_date_consumption(parsed_date, simplify, db=dev_id)

    # b)
    @app.get("/dev_id/{dev_id}/json/yesterday/consumption", tags=["Views"])
    def get_json_yesterday_consumption(current_user: Annotated[User, Depends(get_current_active_user)],
                                       dev_id: str = None, simplify: bool = False):
        """Returns the power consumption of yesterday.
        - **{dev_id}**: The dev_id of the device.
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)
        parsed_date = parse_date("yesterday")

        return get_date_consumption(parsed_date, simplify, db=dev_id)

    # g
    @app.get("/dev_id/{dev_id}/json/last_month/consumption", tags=["Views"])
    def get_json_last_month_consumption(current_user: Annotated[User, Depends(get_current_active_user)],
                                        dev_id: str = None, simplify: bool = False):
        """Returns the power consumption from the first day until the last day of last month.
        - **{dev_id}**: The dev_id of the device.
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)

        days = get_last_month_days()
        consumptions = [get_date_consumption(_.strftime('%Y-%m-%d'), True, db=dev_id) for _ in days]
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
    def get_json_30days_average_consumption(current_user: Annotated[User, Depends(get_current_active_user)],
                                            dev_id: str = None, simplify: bool = False):
        """Returns the average daily consumption in the last 30 days.
        - **{dev_id}**: The dev_id of the device.
        - **simplify**: If set to True, only the pure numerical value will be returned
        """
        check_device_existence(dev_id)

        days = [datetime.date.today() - datetime.timedelta(days=i) for i in range(29, -1, -1)]  # last 30 days
        consumptions = [get_date_consumption(_.strftime('%Y-%m-%d'), True, db=dev_id) for _ in days]
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
    def get_json_30days_average_consumption_div_home_size(
            current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str = None):
        """Returns the average daily consumption in the last 30 days divided by the size of the home
        - **{dev_id}**: The dev_id of the device.
        """
        if has_meta("Household m2", dev_id):
            home_size = float(get_meta("Household m2", dev_id))
        else:
            raise MissingMetadataField('Household m2')
        return float(get_json_30days_average_consumption(current_user, dev_id, simplify=True)) / home_size

    @app.get("/dev_id/{dev_id}/json/date/{date}/mean-consumption", tags=["Experimental"])
    def get_json_date_mean_consumption(current_user: Annotated[User, Depends(get_current_active_user)],
                                       dev_id: str = None, date: str = None):
        """Returns the power consumption over the size of the building for the given date.
        - **{dev_id}**: The dev_id of the device.
        - **{date}**: A date in YYYY-MM-DD format
        data will be looked up in cache and then, if they are not found, fetched from the central database
        """
        check_device_existence(dev_id)
        parsed_date = parse_date(date)
        res = get_mean_consumption(parsed_date, db=dev_id)
        if res == -1:
            raise MissingMetadataField('Household m2')
        return res

    @app.get("/dev_id/{dev_id}/meta", tags=["Metadata"])
    @app.get("/dev_id/{dev_id}/meta/{field}", tags=["Metadata"])
    def get_json_meta(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str = None,
                      field: str = None):
        """Returns the metadata for the current house.
        - **{dev_id}**: The dev_id of the device.
        - **{meta}**: Optional endpoint that specifies the field to be returned if it exists in metadata, otherwise an
        empty dict will be returned. If omitted, all meta fields will be returned.
        """
        check_device_existence(dev_id)
        return get_meta(field, db=dev_id)

    @app.get("/dev_id/{dev_id}/has-meta/{field}", tags=["Metadata"])
    def get_has_meta(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str, field: str):
        """Returns true if given **{field}** exists as metadata field for device with **{field}** , and it is not equal to string "null".
        """
        check_device_existence(dev_id)
        return has_meta(field, db=dev_id)

    # @app.get("/dev_id/{dev_id}/set-meta/{field}/", tags=["Metadata"])
    @app.get("/dev_id/{dev_id}/set-meta/{field}/{value}", tags=["Metadata"])
    def set_meta(current_user: Annotated[User, Depends(get_current_active_user)], dev_id: str, field: str,
                 value: Union[int, float, bool, str, None] = None):
        """Set meta field. If field exist it is getting update.
        """
        check_device_existence(dev_id)

        import jsonschema
        try:
            set_meta_field(field, value, db=dev_id)
            return "OK"
        except jsonschema.exceptions.ValidationError as e:
            raise SchemaValidationForMetaFailed(e.message)

    @app.get("/meta/schema", tags=["Metadata"])
    def meta_schema(current_user: Annotated[User, Depends(get_current_active_user)], ):
        """Returns the meta schema
        """
        return CleanEmonCore.json_utils.schemas.schema_meta

    return app


def get_last_month_days():
    end_last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    start_last_month = end_last_month.replace(day=1)  # first day of the last month
    delta = end_last_month - start_last_month

    days = [start_last_month + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    return days


