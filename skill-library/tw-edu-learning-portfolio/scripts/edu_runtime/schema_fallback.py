"""Small, offline validator for the schema keywords used by this Skill.

This intentionally rejects unknown schema keywords so future upstream schema changes
cannot silently skip validation. It validates JSON data, not arbitrary Python objects.
"""
from __future__ import annotations

ALLOWED = {"$schema", "type", "additionalProperties", "required", "properties",
           "items", "minItems", "minLength", "minimum", "exclusiveMinimum",
           "const", "enum", "description", "title"}

class SchemaError(ValueError):
    pass

def _type_matches(value, name):
    if name == "object": return isinstance(value, dict)
    if name == "array": return isinstance(value, list)
    if name == "string": return isinstance(value, str)
    if name == "integer": return isinstance(value, int) and not isinstance(value, bool)
    if name == "number": return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "boolean": return isinstance(value, bool)
    if name == "null": return value is None
    raise SchemaError(f"unsupported schema type: {name}")

def validate(value, schema, location="$"):
    unknown = set(schema) - ALLOWED
    if unknown:
        raise SchemaError(f"unsupported schema keywords at {location}: {sorted(unknown)}")
    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(value, name) for name in names):
            raise SchemaError(f"{location}: expected {names}, got {type(value).__name__}")
    if "const" in schema and value != schema["const"]:
        raise SchemaError(f"{location}: value must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError(f"{location}: value must be one of {schema['enum']!r}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        raise SchemaError(f"{location}: string shorter than minLength")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise SchemaError(f"{location}: array shorter than minItems")
        if "items" in schema:
            for i, item in enumerate(value): validate(item, schema["items"], f"{location}[{i}]")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaError(f"{location}: below minimum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise SchemaError(f"{location}: not above exclusiveMinimum")
    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = required - set(value)
        if missing:
            raise SchemaError(f"{location}: missing {sorted(missing)}")
        properties = schema.get("properties", {})
        extra = set(value) - set(properties)
        additional = schema.get("additionalProperties", True)
        if additional is False and extra:
            raise SchemaError(f"{location}: extra properties {sorted(extra)}")
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key], f"{location}.{key}")
            elif isinstance(additional, dict):
                validate(item, additional, f"{location}.{key}")
