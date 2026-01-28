# This sample tests FieldType with TypedDict extra_items (PEP Version 2).

from typing import Literal, TypedDict, TypeVar
from typing_extensions import FieldKey, FieldType  # pyright: ignore[reportMissingModuleSource]


# 1) TypedDict with extra_items - strict access via FieldKey
class Data(TypedDict, extra_items=int):
    name: str


# Strict access: FieldKey restricts to explicitly declared keys only
def safe_get[K: FieldKey[Data]](d: Data, k: K) -> FieldType[Data, K]:
    return d[k]


d: Data = {"name": "Alice"}

# Valid: "name" is in FieldKey[Data]
result1 = safe_get(d, "name")
reveal_type(result1, expected_text="str")

# Error: "naem" is not in FieldKey[Data] (catches typos)
safe_get(d, "naem")  # Error


# 2) TypedDict with extra_items - direct FieldType usage with unknown key
# For keys not in declared fields, resolves to extra_items type
reveal_type(FieldType[Data, Literal["unknown_key"]], expected_text="type[int]")


# 3) TypedDict with extra_items - union of known and unknown keys
# When mixing known and unknown keys, result is union of field type and extra_items type
reveal_type(
    FieldType[Data, Literal["name", "other"]], expected_text="type[str] | type[int]"
)


# 4) TypedDict without extra_items (closed) - should not allow unknown keys
class ClosedData(TypedDict):
    value: str


# Error: "unknown" is not a valid key for closed TypedDict
x1: FieldType[ClosedData, Literal["unknown"]]  # Error


# 5) TypedDict with extra_items - inheritance
# Note: When a parent has extra_items, child can inherit it
class BaseData(TypedDict, extra_items=float):
    id: int


class ExtendedData(BaseData, extra_items=float):
    label: str


# FieldKey should only include declared keys (id, label), not arbitrary keys
reveal_type(FieldKey[ExtendedData], expected_text="type[Literal['id', 'label']]")

# FieldType for declared keys
reveal_type(FieldType[ExtendedData, Literal["id"]], expected_text="type[int]")
reveal_type(FieldType[ExtendedData, Literal["label"]], expected_text="type[str]")

# FieldType for unknown keys resolves to extra_items type from parent
reveal_type(FieldType[ExtendedData, Literal["unknown"]], expected_text="type[float]")


# 6) Mixed - FieldKey stays strict even with extra_items
def strict_func[K: FieldKey[Data]](d: Data, k: K) -> FieldType[Data, K]:
    return d[k]


# This should work - "name" is declared
strict_func(d, "name")

# This should error - "undeclared" is not in FieldKey[Data]
strict_func(d, "undeclared")  # Error
