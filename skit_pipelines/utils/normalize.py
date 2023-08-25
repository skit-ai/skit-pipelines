def to_snake_case(name: str) -> str:
    return name.lower().replace("-", "_")


def to_camel_case(name: str) -> str:
    words = to_snake_case(name).split("_")
    title_cased = map(lambda word: word.title(), words)
    return "".join(title_cased)


def strip(c: str) -> str:
    return c.strip()


def non_blank(c: str) -> bool:
    return c != ""


def comma_sep_str(string: str, fn=None) -> list:
    default_fn = lambda c: c
    fn = fn or default_fn
    return list(map(fn, filter(non_blank, map(strip, string.split(",")))))
