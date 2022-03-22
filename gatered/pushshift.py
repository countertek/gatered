"""
This module defines PushShiftAPi client to fetch information from PushShift Reddit Archive.
"""
from typing import Any, Optional, TypeVar

from asyncio import sleep
from httpx import AsyncClient, Timeout
import logging

T = TypeVar("T")
log = logging.getLogger(__name__)


class PushShiftAPI:
    """
    The Client that interacts with the PushShift API and returns raw JSON as `dict`.
    [httpx options](https://www.python-httpx.org/api/#asyncclient) can be passed in when creating the client such as `proxies`.

    This acts as a helper to fetch past submissions based on time range (which is not supported by reddit).
    To get the comments, it would be better to get a list of `submission_id` from PushShift and use `gatered.func.get_comments` instead.
    """

    _BASE_URL = "https://api.pushshift.io"
    _DEFAULT_HEADER = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "https://redditsearch.io/",
        "Referer": "https://redditsearch.io/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
    }
    _DEFAULT_OPTIONS = {"timeout": Timeout(10, read=30)}
    _DEFAULT_SORT = "desc"
    _DEFAULT_SIZE = 100

    def __init__(self, **options: Any):
        """
        Initialize a `PushShiftAPI` object, where `options` are
        [httpx options](https://www.python-httpx.org/api/#asyncclient).
        """
        self._client: Optional[AsyncClient] = None
        self._x_reddit_loid: str = "0"
        self._x_reddit_session: str = "0"
        self.options = {**self._DEFAULT_OPTIONS, **options}

    async def __aenter__(self):
        self._client = AsyncClient(
            base_url=self._BASE_URL,
            headers=self._DEFAULT_HEADER,
            **self.options,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()

    async def _get(self, url_path: str, **kwargs: Any) -> Optional[Any]:
        for tries in range(1, 6):
            r = await self._client.get(url_path, **kwargs)
            log.debug(
                f"GET {r.url} *{kwargs.get('data')}* has returned {r.status_code}"
            )

            # Successful returning json
            if 200 <= r.status_code < 300:
                return r.json()

            # Rate limited and wait for a minute
            elif r.status_code == 429:
                log.warning("Rate limited!! Sleep for 60 secs")
                await sleep(60)
                continue

            # we've received a 500, 502 or 504, an unconditional retry
            elif r.status_code in {500, 502, 504}:
                await sleep(tries * 5)
                continue

            # then usual error cases - 403, 404 ...
            else:
                r.raise_for_status()

        # we've run out of retries, raise
        r.raise_for_status()

    async def get_posts(
        self,
        subreddit_name: str,
        before: int = None,
        after: int = None,
        sort: str = _DEFAULT_SORT,
        size: int = _DEFAULT_SIZE,
        **kwargs: Any,
    ):
        """
        Get a list of submissions from PushShift. Returns a list of PushShift archived submissions.

        - `subreddit_name` (str):
            The Subreddit name.
        - `before` (`Optional[int]`) and `after` (`Optional[int]`):
            Provide epoch time (without ms) to get posts from a time range.
            Default to `None` to get latest posts.
        - `sort` (str):
            Option to sort the submissions, default to `desc`
            Available options: `asc`, `desc`
        - `size` (int):
            Size of list to fetch. Default to maximum of 100.
        """
        res = await self._get(
            "/reddit/search/submission",
            params={
                "after": after,
                "before": before,
                "subreddit": subreddit_name,
                "sort": sort,
                "size": size,
            },
            **kwargs,
        )
        return res["data"]
