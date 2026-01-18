from dataclasses import dataclass
from typing import Literal, TypeVar, Any, Union
from typing_extensions import FieldKey, FieldType, dataclass_transform  # pyright: ignore[reportMissingModuleSource]


# 1) Generic substitution
@dataclass
class Box[T]:
    value: T


reveal_type(FieldType[Box[int], Literal["value"]], expected_text="type[int]")
reveal_type(FieldType[Box[str], Literal["value"]], expected_text="type[str]")


# 2) Non-reducible key type var returns union of all field types
@dataclass
class User:
    id: int
    name: str


K_User = TypeVar("K_User", bound=FieldKey[User])


def get_val(key: K_User) -> FieldType[User, K_User]:
    # At this point, key is K_User. We don't know which specific key it is.
    # So the return type should be the union of all field types (int | str).
    return getattr(User(1, "a"), key)


def test_type_var_resolution(k: K_User) -> K_User:
    val = get_val(k)
    reveal_type(val, expected_text="int | str")
    return k


# 3) Override in subclass
@dataclass
class Base:
    x: int


@dataclass
class Sub(Base):
    x: str  # pyright: ignore[reportIncompatibleVariableOverride]


reveal_type(FieldType[Sub, Literal["x"]], expected_text="type[str]")
reveal_type(FieldType[Base, Literal["x"]], expected_text="type[int]")


# 4) dataclass_transform
@dataclass_transform()
class ModelBase:
    def __init_subclass__(cls, **kwargs):
        pass


class Customer(ModelBase):
    id: int
    name: str


reveal_type(FieldType[Customer, Literal["id"]], expected_text="type[int]")
reveal_type(FieldType[Customer, Literal["name"]], expected_text="type[str]")
