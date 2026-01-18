# This sample tests that FieldKey participates correctly in
# generic constraints and inference.

from dataclasses import dataclass
from typing import Any, Literal, TypeVar, Union
from typing_extensions import FieldKey  # pyright: ignore[reportMissingModuleSource]


@dataclass
class User:
    id: int
    name: str
    age: int = 30


@dataclass
class Product:
    sku: str
    price: float


# 1) Classic TypeVar bound style with concrete FieldKey bound
K1 = TypeVar("K1", bound=FieldKey[User])


def accept_user_key(obj: User, key: K1) -> K1:
    return key


user = User(id=1, name="Alice")

# Valid calls - should infer narrow literal types
r1 = accept_user_key(user, "id")
reveal_type(r1, expected_text="Literal['id']")

r2 = accept_user_key(user, "name")
reveal_type(r2, expected_text="Literal['name']")

r3 = accept_user_key(user, "age")
reveal_type(r3, expected_text="Literal['age']")

# Invalid literal - should generate an error
accept_user_key(user, "nope")  # This should generate an error

# Using a variable with a literal type
literal_key: Literal["id"] = "id"
r4 = accept_user_key(user, literal_key)
reveal_type(r4, expected_text="Literal['id']")


# 2) FieldKey in function parameter - verify union of literals behavior
def func_with_fieldkey_param(key: FieldKey[User]) -> None:
    pass


# These should all pass
func_with_fieldkey_param("id")
func_with_fieldkey_param("name")
func_with_fieldkey_param("age")

# This should error
func_with_fieldkey_param("unknown")  # This should generate an error


# 3) Union target with TypeVar
@dataclass
class A:
    a: int
    common: str


@dataclass
class B:
    b: float
    common: str


K_AB = TypeVar("K_AB", bound=FieldKey[A | B])


def accept_ab_key(key: K_AB) -> K_AB:
    return key


# Only "common" is valid for A | B
r5 = accept_ab_key("common")
reveal_type(r5, expected_text="Literal['common']")

# "a" is not on B, so this should error
accept_ab_key("a")  # This should generate an error

# "b" is not on A, so this should error
accept_ab_key("b")  # This should generate an error


# 4) FieldKey[Any] should be str, verify constraints work
def accept_any_schema(key: FieldKey[Any]) -> None:
    pass


accept_any_schema("anything")  # Should work - FieldKey[Any] is str
accept_any_schema("any_key")  # Should work


# 5) Verify that FieldKey bound works with literal union parameter type
def accept_literal_union(key: Literal["id", "name"]) -> None:
    pass


accept_literal_union("id")
accept_literal_union("name")
# This should error
accept_literal_union("age")  # This should generate an error


# 6) Nested inference - verify inferred return type
def get_key(k: K1) -> K1:
    return k


r6 = get_key("id")
reveal_type(r6, expected_text="Literal['id']")

r7 = get_key("name")
reveal_type(r7, expected_text="Literal['name']")


# 7) Multiple fields in one call
def accept_multi(k1: FieldKey[User], k2: FieldKey[User]) -> None:
    pass


accept_multi("id", "name")  # Should work
accept_multi("id", "invalid")  # This should generate an error
