"""Module to handle API data for Music cog."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple
from urllib.parse import urlencode

from aiohttp import ClientConnectionError, ClientResponseError, ClientSession

from bot.constants import Tokens


logger: logging.Logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiMethod:
    """API method data."""

    super_name: str
    sub_name: str
    required_parameters: Tuple[str, ...] = ()
    optional_prameters: Tuple[str, ...] = ()

    def __str__(self) -> str:
        """Combined method name to use with API request."""
        return f"{self.super_name}.{self.sub_name}"


@dataclass
class LastFmApiSettings:
    """Last.fm API settings."""

    chart_methods: Dict[str, ApiMethod]
    track_methods: Dict[str, ApiMethod]
    key: str = Tokens.lastfm_api_key
    secret: str = Tokens.lastfm_client_secret
    token: str = ""
    base_url: str = "http://ws.audioscrobbler.com/2.0?"
    token_url: str = ""
    MAX_LIMIT: int = 50
    MIN_LIMIT: int = 1


track_methods: Dict[str, ApiMethod] = {
    "getsimilar": ApiMethod(
        super_name="track",
        sub_name="getsimilar",
        required_parameters=("name", "artist"),
        optional_prameters=("mbid", "autocorrect", "limit"),
    ),
}
chart_methods: Dict[str, ApiMethod] = {
    "gettoptracks": ApiMethod(
        super_name="chart",
        sub_name="gettoptracks",
        required_parameters=(),
        optional_prameters=("page", "limit"),
    ),
}

settings: LastFmApiSettings = LastFmApiSettings(chart_methods=chart_methods, track_methods=track_methods)


async def get_api_json_data(api_settings: LastFmApiSettings, session: ClientSession, /, **parameters) -> Dict[str, Any]:
    """Get JSON data as dict by API method and other query parameters."""
    # Simple safe guard to avoid fetching too many results.
    limit_key: str = "limit"
    limit: int = parameters[limit_key] if 1 < parameters.get(limit_key, 0) <= api_settings.MAX_LIMIT else 1
    default_parameters: Dict[str, Any] = {
        "limit": limit,
        "api_key": api_settings.key,
        "format": "json",
    }
    if not 1 < parameters[limit_key] <= api_settings.MAX_LIMIT:
        print("bad limit", parameters.get(limit_key))
        raise ValueError(f"Limit ({parameters[limit_key]}) is invalid, please try again.")

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
                raise await e
    except ClientConnectionError as e:
        logger.error(repr(e))
        raise await e
