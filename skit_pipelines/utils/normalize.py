def to_snake_case(name: str) -> str:
    return name.lower().replace("-", "_")


def to_camel_case(name: str) -> str:
    words = to_snake_case(name).split("_")
    title_cased = map(lambda word: word.title(), words)
    return "".join(title_cased)


def strip(c: str) -> str:
    return c.strip()


def isdigit(c: str) -> bool:
    return c.isdigit()


def comma_sep_str(string: str, fn = None) -> str:
    default_fn = lambda c: c
    fn = fn or default_fn
    return list(map(fn, filter(isdigit, map(strip, string.split(",")))))
