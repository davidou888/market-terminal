import re

# Real UUID v4 pattern: 8-4-4-4-12 hex chars
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def blockSQLkey(key: str) -> bool:
    """
    Validates that `key` is a well-formed UUID v4.
    Returns True if valid, raises ValueError otherwise.
    Enforces exact hex character content per segment — not just separator count.
    """
    if not isinstance(key, str):
        raise ValueError(f"[blockSQLkey] Expected str, got {type(key)}")

    if not UUID_PATTERN.match(key):
        raise ValueError(f"[blockSQLkey] Rejected invalid key: {key!r}")

    return True



