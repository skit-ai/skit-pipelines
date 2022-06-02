def to_snake_case(name: str) -> str:
    return name.lower().replace("-", "_")


def to_camel_case(name: str) -> str:
    words = to_snake_case(name).split("_")
    title_cased = map(lambda word: word.title(), words)
    return "".join(title_cased)
