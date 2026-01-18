# Tests for practical FieldType usage patterns from the PEP examples

from dataclasses import dataclass
from typing import Literal, TypedDict, NamedTuple
from typing_extensions import FieldKey, FieldType  # pyright: ignore[reportMissingModuleSource]


# 1) TypedDict example from PEP
class Config(TypedDict):
    host: str
    port: int


def get_config_value[K: FieldKey[Config]](
    config: Config, key: K
) -> FieldType[Config, K]:
    return config[key]


config: Config = {"host": "localhost", "port": 8080}

host = get_config_value(config, "host")
reveal_type(host, expected_text="str")

port = get_config_value(config, "port")
reveal_type(port, expected_text="int")

# Error: "invalid" is not a valid key
get_config_value(config, "invalid")  # Error


# 2) NamedTuple example from PEP
class Result(NamedTuple):
    returncode: int
    reason: str | None


def get_reason(result: Result) -> FieldType[Result, Literal["reason"]]:
    return result.reason


r = Result(returncode=0, reason="success")
reason = get_reason(r)
reveal_type(reason, expected_text="str | None")


# 3) Dataclass with specific field getter
@dataclass
class User:
    id: int
    name: str


def get_user_attr[K: FieldKey[User]](obj: User, key: K) -> FieldType[User, K]:
    return getattr(obj, key)


user = User(id=1, name="Alice")

user_id = get_user_attr(user, "id")
reveal_type(user_id, expected_text="int")

user_name = get_user_attr(user, "name")
reveal_type(user_name, expected_text="str")

# Error: "foo" is not a valid key for User
get_user_attr(user, "foo")  # Error


# 4) Class with FieldKey-bounded type parameter
class UserFieldGetter[K: FieldKey[User]]:
    def __init__(self, field_name: K):
        self._field_name = field_name

    def __call__(self, user: User) -> FieldType[User, K]:
        return getattr(user, self._field_name)


name_getter = UserFieldGetter("name")
id_getter = UserFieldGetter("id")

reveal_type(name_getter(user), expected_text="str")
reveal_type(id_getter(user), expected_text="int")

# Error: "invalid" is not a valid key
invalid_getter = UserFieldGetter("invalid")  # Error
