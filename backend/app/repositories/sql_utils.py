from psycopg.sql import Identifier, SQL


def build_update_statement(
    *,
    fields: dict[str, object],
    allowed_fields: set[str],
) -> tuple[SQL, list[object]]:
    invalid_fields = sorted(set(fields) - allowed_fields)
    if invalid_fields:
        raise ValueError(f"Unsupported fields for update: {', '.join(invalid_fields)}")

    assignments = [SQL("{} = %s").format(Identifier(column)) for column in fields]
    return SQL(", ").join(assignments), list(fields.values())
