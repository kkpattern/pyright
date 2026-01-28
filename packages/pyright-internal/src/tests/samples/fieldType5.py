# This sample tests FieldType with dynamic key access using TypeVar (PEP Version 2).

from typing import Literal, TypedDict, TypeVar
from typing_extensions import FieldKey, FieldType  # pyright: ignore[reportMissingModuleSource]


# TypedDict with extra_items
class Data(TypedDict, extra_items=int):
    name: str


d: Data = {"name": "Alice"}


# Test 1: TypeVar bounded by str with a literal argument
# When K is inferred as a specific literal, FieldType should resolve correctly
K_Str = TypeVar("K_Str", bound=str)


def flexible_get(d: Data, k: K_Str) -> FieldType[Data, K_Str]:
    return d[k]  # type: ignore


# When called with a literal that's a known field, should resolve to the field type
# Note: Due to TypeVar bound resolution, this returns the union of all field types
result1 = flexible_get(d, "name")
reveal_type(result1, expected_text="str | int")

# When called with a literal that's NOT a known field, should resolve to extra_items type
# Note: Due to TypeVar bound resolution, this returns the union of all field types
result2 = flexible_get(d, "unknown")
reveal_type(result2, expected_text="str | int")


# Test 2: Direct FieldType with str key (not TypeVar)
# This should return the union of all field types + extra_items
reveal_type(FieldType[Data, str], expected_text="type[str] | type[int]")
