from typing import Iterable


def normalize_string(value: str) -> str:
    return " ".join(value.split())


def dedupe_strings(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        normalized = normalize_string(item)
        if not normalized:
            continue

        key = normalized.casefold()
        if key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return result
