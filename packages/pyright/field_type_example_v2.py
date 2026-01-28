from typing import TypedDict, TypeVar, FieldKey, FieldType, NamedTuple, Literal, Mapping, Any


class Schema(TypedDict):
    key1: str
    key2: int
    

class SchemaModel[S: Mapping[str, Any]]:
    def __init__(self, schema: S):
        # This is properly typed
        self._schema = schema
    
    def __getitem__[K: FieldKey[S]](self, key: K) -> FieldType[S, K]:
        return self._schema[key]


def get_api_response() -> Schema:
    return Schema(key1="hello", key2=1)


model = SchemaModel[Schema](get_api_response())


reveal_type(model['key1'])
reveal_type(model['key2'])
