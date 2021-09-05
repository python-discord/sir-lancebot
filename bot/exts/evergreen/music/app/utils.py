"""Music cog utility functions."""

import asyncio
import logging
from typing import Any, Iterable


logger = logging.getLogger(__name__)


def paginate(items: Iterable[str], page_count: int = 1) -> list[list[Any]]:
    """Paginate items by target page count."""
    pages = []
    page_number = 0
    for i, item in enumerate(items):
        if i % page_count == 0:
            pages.append([])
            page_number += 1
        pages[page_number - 1].append(item)
    return pages


async def async_paginate(items: Iterable[str], page_count: int = 1) -> list[list[Any]]:
    """Paginate items by target page count, awaitable."""
    pages = []
    page_number = 0
    for i, item in enumerate(items):
        if i % page_count == 0:
            pages.append([])
            page_number += 1
        pages[page_number - 1].append(item)
        await asyncio.sleep(0.01)
    return pages
