from __future__ import annotations

import re


def normalize_match_text(text_value: str | None) -> str:
    if not text_value:
        return ""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text_value.lower()).split())


def output_contains_any(text_value: str | None, tokens: list[str]) -> bool:
    text_lower = (text_value or "").lower()
    return any(token in text_lower for token in tokens)


def contains_any_alias(text_value: str | None, aliases: list[str]) -> bool:
    if not text_value:
        return False
    text_lower = text_value.lower()
    normalized_text = normalize_match_text(text_value)
    padded_text = f" {normalized_text} " if normalized_text else ""
    compact_text = normalized_text.replace(" ", "")

    for alias in aliases:
        alias_lower = (alias or "").strip().lower()
        if not alias_lower:
            continue
        normalized_alias = normalize_match_text(alias_lower)
        compact_alias = normalized_alias.replace(" ", "")

        if any(char in alias_lower for char in ".-_") and alias_lower in text_lower:
            return True
        if normalized_alias and f" {normalized_alias} " in padded_text:
            return True
        if " " in normalized_alias and compact_alias and compact_alias in compact_text:
            return True
    return False
