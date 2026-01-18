# This sample tests the FieldKey special form.

from dataclasses import dataclass, field, InitVar, KW_ONLY
from typing import Any, ClassVar, Literal, NamedTuple, TypedDict, Union, TypeVar
from typing_extensions import FieldKey, dataclass_transform # pyright: ignore[reportMissingModuleSource]

@dataclass
class User:
    id: int
    name: str
    age: int = 30
    _private: int = 1
    class_var: ClassVar[int] = 1
    init_var: InitVar[int] = 1
    _: KW_ONLY
    after_kw_only: str = "yes"

# 1) Dataclass basic
reveal_type(FieldKey[User], expected_text="type[Literal['id', 'name', 'age', '_private', 'after_kw_only']]")

# 2) Dataclass exclusions
def func1(k: FieldKey[User]) -> None:
    pass

func1("id")
func1("name")
func1("age")
func1("_private")
func1("after_kw_only")
# This should generate an error because class_var is excluded
func1("class_var")
# This should generate an error because init_var is excluded
func1("init_var")
# This should generate an error because kw_only is excluded
func1("kw_only")

# 3) Dataclass inheritance and override
@dataclass
class Base:
    x: int

@dataclass
class Sub(Base):
    x: str # override # pyright: ignore[reportGeneralTypeIssues]
    y: float

reveal_type(FieldKey[Sub], expected_text="type[Literal['x', 'y']]")

# 4) Dataclass field(init=False)
@dataclass
class InitFalse:
    z: int = field(init=False)

reveal_type(FieldKey[InitFalse], expected_text="type[Literal['z']]")

# 5) dataclass_transform class
@dataclass_transform()
class TransformBase:
    def __init_subclass__(cls, **kwargs):
        pass

class Customer1(TransformBase):
    id: int
    name: str

reveal_type(FieldKey[Customer1], expected_text="type[Literal['id', 'name']]")

# 6) TypedDict
class TD(TypedDict):
    a: int
    b: str

reveal_type(FieldKey[TD], expected_text="type[Literal['a', 'b']]")

# 7) NamedTuple
class NT(NamedTuple):
    a: int
    b: str

reveal_type(FieldKey[NT], expected_text="type[Literal['a', 'b']]")

# 8) Union intersection
@dataclass
class A:
    a: int
    common: int

@dataclass
class B:
    b: int
    common: int

reveal_type(FieldKey[Union[A, B]], expected_text="type[Literal['common']]")

@dataclass
class C:
    c: int

reveal_type(FieldKey[Union[A, C]], expected_text="Never")

# 9) Special cases / errors
reveal_type(FieldKey[Any], expected_text="type[str]")

# This should generate an error: Expected instance type
FieldKey[type[User]]

# This should generate an error: Type "object" is not a supported schema type
FieldKey[object]

# This should generate an error: Type "int" is not a supported schema type
FieldKey[int]

# 10) TypeVar
T = TypeVar("T", bound=User)
reveal_type(FieldKey[T], expected_text="type[Literal['id', 'name', 'age', '_private', 'after_kw_only']]")

U = TypeVar("U")
# This should generate an error: Type "U" is not a supported schema type
FieldKey[U]
