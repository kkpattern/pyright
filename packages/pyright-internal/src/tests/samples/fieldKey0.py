# This is a smoke test to ensure FieldKey and FieldType can be imported

from dataclasses import dataclass
from typing import FieldKey, FieldType
from typing_extensions import FieldKey as EFieldKey, FieldType as EFieldType # pyright: ignore[reportMissingModuleSource]

@dataclass
class User:
    id: int

def func1(k: FieldKey[User], t: FieldType[User, str]) -> None:
    pass

def func2(k: EFieldKey[User], t: EFieldType[User, str]) -> None:
    pass