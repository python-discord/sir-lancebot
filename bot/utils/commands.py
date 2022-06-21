from typing import Optional

from rapidfuzz import process


def get_command_suggestions(all_commands: list[str], query: str, *, cutoff=60, limit=3) -> Optional[list]:
    results = process.extract(query, all_commands, score_cutoff=cutoff, limit=limit)
    return [result[0] for result in results]
