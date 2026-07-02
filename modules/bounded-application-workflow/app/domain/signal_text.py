def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def casefold_for_match(text: str) -> str:
    return collapse_whitespace(text).casefold()
