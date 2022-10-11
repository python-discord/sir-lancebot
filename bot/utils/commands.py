from rapidfuzz import process


def get_command_suggestions(all_commands: list[str], query: str, *, cutoff: int = 60, limit: int = 3) -> list[str]:
    """Get similar command names."""
    results = process.extract(query, all_commands, score_cutoff=cutoff, limit=limit)
    return [result[0] for result in results]
