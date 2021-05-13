"""Module to handle API data for Music cog."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from bot.constants import Tokens


logger: logging.Logger = logging.getLogger(__name__)


class InvalidArgument(ValueError):
    """Exception to raise when an argument is invalid."""

    pass


@dataclass
class RequestInfo:
    """Mutable data object to hold request info for methods."""

    _time: Optional[float] = None

    @property
    def time(self) -> Optional[float]:
        """Timestamp of current request."""
        return self._time

    @property
    def time_since(self) -> float:
        """
        Time in seconds since last tracked request.

        Time may not be exact, depending on when request is tracked.  Should not be
          an issue, since values are used with caching and precision is not sensitive.
        """
        if self.time is None:
            raise TypeError("No initial value for `time`. Call `update` before accessing other attributes.")
        return time.time() - self.time

    def update(self) -> None:
        """
        Update request info.

        Call method via an API method every time a request is made.
        """
        self._time: float = time.time()


@dataclass(frozen=True)
class ApiMethod:
    """
    API method data.

    An API method is immutable (frozen) by design, to avoid editing constant values.  However,
      the time of when a request was made is used with caching.  A mutable protected
      attribute can update request info while the other attributes remain immutable.
    """

    name: str
    prefix: str
    item: str
    required_params: Tuple[str, ...] = ()
    optional_params: Tuple[str, ...] = ()
    _cache_limit: int = 3600 * 24
    _request: RequestInfo = field(default_factory=RequestInfo)

    def __repr__(self) -> str:
        """Object instantiation representation."""
        # Use separate variables for attributes to remove "self" when shortcutting with f-string.
        name: str = self.name
        prefix: str = self.prefix
        item: str = self.item
        required_params: Tuple[str, ...] = self.required_params
        optional_params: Tuple[str, ...] = self.optional_params
        return f"{type(self).__name__}({name=}, {prefix=}, {item=}, {required_params=}, {optional_params=})"

    def __str__(self) -> str:
        """Combined method name to use with API request."""
        return f"{self.prefix}.{self.name}"

    @property
    def item_plural(self) -> str:
        """Plural string of `item` for use when retrieving item data from payload."""
        return self.item + "s"

    def track_request(self) -> None:
        """
        Update request info.

        Call when a request is made. Enables tracking info to help with caching etc.
        """
        self._request.update()

    @property
    def time_since_request(self) -> float:
        """
        Time in seconds since when last request using the method was tracked.

        Used with caching to determine if a result should be cached.
        """
        return self._request.time_since


@dataclass(frozen=True)
class LastFmApiSettings:
    """Last.fm API settings."""

    chart_methods: Dict[str, ApiMethod]
    track_methods: Dict[str, ApiMethod]
    key: str = Tokens.lastfm_api_key
    base_url: str = "http://ws.audioscrobbler.com/2.0?"
    min_limit: int = 1
    max_limit: int = 50
    request_delay: float = 0.002


track_methods: Dict[str, ApiMethod] = {
    "getsimilar": ApiMethod(
        name="getsimilar",
        prefix="track",
        item="track",
        required_params=("name", "artist"),
        optional_params=("mbid", "autocorrect", "limit"),
    ),
}
chart_methods: Dict[str, ApiMethod] = {
    "gettoptracks": ApiMethod(
        name="gettoptracks",
        prefix="chart",
        item="track",
        required_params=(),
        optional_params=("page", "limit"),
    ),
}

settings: LastFmApiSettings = LastFmApiSettings(chart_methods=chart_methods, track_methods=track_methods)


async def get(api_settings: LastFmApiSettings, session: ClientSession, /, **parameters) -> Dict[str, Any]:
    """Get JSON data as dict by API method and other query parameters."""
    # Simple safe guard to avoid fetching too many results.
    limit_key: str = "limit"
    limit: int = parameters[limit_key] if 1 < parameters.get(limit_key, 0) <= api_settings.max_limit else 1
    default_parameters: Dict[str, Any] = {
        "limit": limit,
        "api_key": api_settings.key,
        "format": "json",
    }
    if not 1 < parameters[limit_key] <= api_settings.max_limit:
        e: InvalidArgument = InvalidArgument(
            f"Count ({parameters[limit_key]}) must be between 1 and {api_settings.max_limit}."
        )
        logger.error(str(e))
        raise e

    # Merge parameters, positioning default parameters at the end.
    #   Since Python 3.6, dictionaries are ordered and keep their insertion order.
    parameters = {**parameters, **default_parameters}
    query_string: str = urlencode(parameters)
    url: str = api_settings.base_url + query_string
    try:
        async with session.get(url) as response:
            try:
                return await response.json()
            except ClientResponseError as e:
                logger.error(repr(e))
                raise e
    except ClientConnectionError as e:
        logger.error(repr(e))
        raise e
    finally:
        # Sleep after each request to enforce request delay.
        await asyncio.sleep(settings.request_delay)
