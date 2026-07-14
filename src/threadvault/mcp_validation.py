from __future__ import annotations

from typing import Any


class McpValidationError(ValueError):
    """A client-safe validation error for MCP request data."""


def validate_tool_arguments(tool: dict[str, Any], arguments: Any) -> dict[str, Any]:
    """Validate tool arguments against the exact schema advertised by tools/list."""
    if not isinstance(arguments, dict):
        raise McpValidationError("Tool arguments must be an object.")
    _validate(arguments, tool["inputSchema"], "arguments")
    return arguments


def validate_initialize_params(params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise McpValidationError("initialize params must be an object.")

    required = {"protocolVersion", "capabilities", "clientInfo"}
    missing = sorted(required - params.keys())
    if missing:
        raise McpValidationError(f"initialize is missing required field: {missing[0]}.")

    protocol_version = params["protocolVersion"]
    if not isinstance(protocol_version, str) or not protocol_version.strip():
        raise McpValidationError("initialize protocolVersion must be a non-empty string.")
    if not isinstance(params["capabilities"], dict):
        raise McpValidationError("initialize capabilities must be an object.")

    client_info = params["clientInfo"]
    if not isinstance(client_info, dict):
        raise McpValidationError("initialize clientInfo must be an object.")
    for field in ("name", "version"):
        value = client_info.get(field)
        if not isinstance(value, str) or not value.strip():
            raise McpValidationError(f"initialize clientInfo.{field} must be a non-empty string.")
    return params


def _validate(value: Any, schema: dict[str, Any], location: str) -> None:
    one_of = schema.get("oneOf")
    if one_of is not None:
        matches = 0
        for candidate in one_of:
            try:
                _validate(value, candidate, location)
            except McpValidationError:
                continue
            matches += 1
        if matches != 1:
            raise McpValidationError(f"{location} does not match exactly one allowed shape.")
        return

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        raise McpValidationError(f"{location} must be {_type_label(expected_type)}.")

    if "enum" in schema and value not in schema["enum"]:
        raise McpValidationError(f"{location} must be one of the advertised values.")

    if expected_type == "object":
        _validate_object(value, schema, location)
    elif expected_type == "array":
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                _validate(item, item_schema, f"{location}[{index}]")
    elif expected_type == "integer":
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise McpValidationError(f"{location} is below the advertised minimum.")
        if maximum is not None and value > maximum:
            raise McpValidationError(f"{location} exceeds the advertised maximum.")


def _validate_object(value: dict[str, Any], schema: dict[str, Any], location: str) -> None:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    for field in required:
        if field not in value:
            raise McpValidationError(f"{location}.{field} is required.")

    if schema.get("additionalProperties") is False:
        unexpected = sorted(set(value) - set(properties))
        if unexpected:
            raise McpValidationError(f"{location} contains an unexpected field: {unexpected[0]}.")

    for field, item in value.items():
        field_schema = properties.get(field)
        if field_schema is not None:
            _validate(item, field_schema, f"{location}.{field}")


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return type(value) is bool
    if expected_type == "integer":
        return type(value) is int
    if expected_type == "null":
        return value is None
    return False


def _type_label(expected_type: str) -> str:
    return {
        "object": "an object",
        "array": "an array",
        "string": "a string",
        "boolean": "a boolean",
        "integer": "an integer",
        "null": "null",
    }.get(expected_type, expected_type)
