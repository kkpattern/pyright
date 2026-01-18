from dataclasses import dataclass
from typing import (
    Literal,
    TypedDict,
    NamedTuple,
    Any,
    NotRequired,
    ReadOnly,
    FieldKey,
    FieldType,
    Never,
)


@dataclass
class User:
    id: int
    name: str


# 1) Dataclass single key
reveal_type(FieldType[User, Literal["id"]], expected_text="type[int]")

# 2) Dataclass union of keys
reveal_type(
    FieldType[User, Literal["id", "name"]], expected_text="type[int] | type[str]"
)

# 3) Key constraint errors
# Error 1: Key 'nope' is not in FieldKey[User]
x1: FieldType[User, Literal["nope"]]

# 4) Any/Never special cases
reveal_type(FieldType[Any, Literal["x"]], expected_text="Any")
reveal_type(FieldType[User, Any], expected_text="Any")
reveal_type(FieldType[User, Never], expected_text="Never")


# 5) TypedDict wrapper stripping
class TD(TypedDict):
    a: int
    b: NotRequired[str]
    c: ReadOnly[float]


reveal_type(FieldType[TD, Literal["b"]], expected_text="type[str]")
reveal_type(FieldType[TD, Literal["c"]], expected_text="type[float]")


# 6) NamedTuple
class NT(NamedTuple):
    a: int
    b: str


reveal_type(FieldType[NT, Literal["a"]], expected_text="type[int]")


# 7) Union target
@dataclass
class A:
    common: int
    a_only: str


@dataclass
class B:
    common: float
    b_only: str


reveal_type(
    FieldType[A | B, Literal["common"]], expected_text="type[int] | type[float]"
)

# Error 2: 'a_only' is not in FieldKey[A | B] (intersection is {'common'})
x2: FieldType[A | B, Literal["a_only"]]

# Error 3: 'int' is not a schema class
x3: FieldType[int, Literal["numerator"]]


class NotSchema:
    x: int


# Error 4: 'NotSchema' is not a schema class (normal class)
x4: FieldType[NotSchema, Literal["x"]]


def get_user_attr[K: FieldKey[User]](obj: User, key: K) -> FieldType[User, K]:
    return getattr(obj, key)


user = User(id=1, name="Alice")

val1 = get_user_attr(user, "id")
reveal_type(val1, expected_text="int")

val2 = get_user_attr(user, "name")
reveal_type(val2, expected_text="str")

# Error 5: "foo" is not assignable to FieldKey[User]
val3 = get_user_attr(user, "foo")
