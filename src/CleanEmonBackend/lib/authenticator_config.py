import configparser
from dataclasses import asdict, dataclass

from CleanEmonCore import CONFIG_FILE
from orjson import orjson
from pydantic import BaseModel
from typing import Union

cfg = configparser.ConfigParser(interpolation=None)
cfg.read(CONFIG_FILE)

SECRET_KEY = cfg["DB"]["SECRET_KEY"]
ALGORITHM = cfg["DB"]["ALGORITHM"]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    # email: Union[str, None] = None
    # full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


class RegisteringUser(BaseModel):
    username: str
    password: str


# A hacky way, this is done because the create_document on
# CleanEmonCore.CouchDBAdapter expects an EnergyData dataclass,
# this ain't a EnergyData dataclass, but it's a dataclass
@dataclass
class UserInDBDataClass:
    username: str
    hashed_password: str
    disabled: bool = False

    def as_json(self, *, string):
        as_dict = asdict(self)

        if string:
            return orjson.dumps(as_dict)
        else:
            return as_dict


def is_couchdb_safe_username(username: str) -> bool:
    """Check if a username is safe for use as a CouchDB document ID."""
    # Check length
    if len(username) < 1 or len(username) > 256:
        return False

    # Check character set
    valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_$()+-/')
    if not set(username).issubset(valid_chars):
        return False

    # Check reserved characters at the beginning
    if username[0] == '_':
        return False

    return True
