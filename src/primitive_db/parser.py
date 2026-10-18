def parse_where(tokens):
    if len(tokens) != 3 or tokens[1] != "=":
        return None
    col, _, raw = tokens
    return {col: _parse_literal(raw)}


def parse_set(tokens):
    return parse_where(tokens)


def _parse_literal(raw):
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    try:
        return int(raw)
    except ValueError:
        return raw