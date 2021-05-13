"""Music cog utility functions."""

import asyncio
import logging
from typing import Any, Iterable, List


logger: logging.Logger = logging.getLogger(__name__)


def paginate(items: Iterable, page_count: int = 1) -> List[List[Any]]:
    """Paginate items by target page count."""
    pages: List[List[str]] = []
    page_number = 0
    for i, item in enumerate(items):
        if i % page_count == 0:
            pages.append([])
            page_number += 1
        pages[page_number - 1].append(item)
    return pages


async def async_paginate(items: Iterable, page_count: int = 1) -> List[List[Any]]:
    """Paginate items by target page count, awaitable."""
    pages: List[List[str]] = []
    page_number = 0
    for i, item in enumerate(items):
        if i % page_count == 0:
            pages.append([])
            page_number += 1
        pages[page_number - 1].append(item)
        await asyncio.sleep(0.01)
    return pages
