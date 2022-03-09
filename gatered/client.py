from typing import Any, Optional, TypeVar
from typing_extensions import TypeAlias
from collections.abc import Callable, Coroutine
from functools import partialmethod

import asyncio
import httpx
import logging

T = TypeVar("T")
log = logging.getLogger(__name__)
RequestType: TypeAlias = "Coroutine[None, None, Optional[T]]"


class Client:
    """
    The Client that interacts with the Reddit gateway API and returns raw JSON.
    Httpx options can be passed in when creating the client such as proxies:
    https://www.python-httpx.org/api/#asyncclient
    """

    _SUBREDDIT_SORT = "hot"
    _TOP_SORT_T = "day"
    _BASE_URL = "https://gateway.reddit.com/desktopapi/v1"
    _DEFAULT_HEADER = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Origin": "https://www.reddit.com",
        "Referer": "https://www.reddit.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
    }
    _DEFAULT_PARAMS = {
        # rtj (rich text json) is excluded
        "redditWebClient": "web2x",
        "app": "web2x-client-production",
        "allow_over18": 1,
    }

    def __init__(self, **options: Any):
        self._client: Optional[httpx.AsyncClient] = None
        self._x_reddit_loid: str = "0"
        self._x_reddit_session: str = "0"
        self.options = options

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            headers=self._DEFAULT_HEADER,
            params=self._DEFAULT_PARAMS,
            **self.options,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        url_path: str,
        **kwargs: Any,
    ) -> Optional[Any]:
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"].update(
            {
                "x-reddit-loid": self._x_reddit_loid,
                "x-reddit-session": self._x_reddit_session,
            }
        )

        for tries in range(1, 6):
            r = await self._client.request(method, url_path, **kwargs)
            log.debug(
                f"{method} {r.url} *{kwargs.get('data')}* has returned {r.status_code}"
            )

            # Successful returning text/json
            if 200 <= r.status_code < 300:
                if self._x_reddit_loid == "0":
                    self._x_reddit_loid = r.headers.get("x-reddit-loid", "")
                    self._x_reddit_session = r.headers.get("x-reddit-session", "")

                return r.json()

            # Rate limited (this is not tested)
            elif r.status == 429:
                log.warning("Rate limited!!")
                try:
                    await asyncio.sleep(float(r.headers["X-Retry-After"]))
                except KeyError:
                    await asyncio.sleep(30 * tries)
                continue

            # we've received a 500, 502 or 504, an unconditional retry
            elif r.status in {500, 502, 504}:
                await asyncio.sleep(tries * 5)
                continue

            # then usual error cases - 403, 404 ...
            else:
                r.raise_for_status()

        # we've run out of retries, raise
        r.raise_for_status()

    _get: Callable[..., RequestType] = partialmethod(_request, "GET")
    _post: Callable[..., RequestType] = partialmethod(_request, "POST")

    # -- Request endpoints impl. --

    async def get_more_comments(
        self,
        submission_id: str,
        token: str,
        **kwargs: Any,
    ):
        """
        Get More comments from a submission.

        Parameters
        ----------
        submission_id: :class:`str`
            The Submission id (starts with `t3_`)
        token: :class:`str`
            Token for more comments content.

        Returns raw comments list.
        """
        payload = {"token": token}
        params = {"emotes_as_images": "true"}
        return await self._post(
            f"/morecomments/{submission_id}",
            params=params,
            json=payload,
            **kwargs,
        )

    async def get_post_comments(
        self,
        submission_id: str,
        sort: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Get post and its comments (comments and its related info).

        Parameters
        ----------
        submission_id: :class:`str`
            The Submission id (starts with `t3_`)
        sort: Optional[:class:`str`]
            Option to sort the comments of the submission, default to None (best)
            Available options: `top`, `new`, `controversial`, `old`, `qa`

        Returns raw submission and its comments, moreComments etc.
        """
        params = {
            "emotes_as_images": "true",
            "hasSortParam": "false",
            "include_categories": "true",
            "onOtherDiscussions": "false",
        }
        if sort in {"top", "new", "controversial", "old", "qa"}:
            params["hasSortParam"] = "true"
            params["sort"] = sort

        return await self._get(
            f"/postcomments/{submission_id}",
            params=params,
            **kwargs,
        )

    async def get_posts(
        self,
        subreddit_name: str,
        sort: Optional[str] = _SUBREDDIT_SORT,
        t: Optional[str] = _TOP_SORT_T,
        after: Optional[str] = None,
        dist: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Get submissions list from a subreddit.
        Note: This also includes ads posts.

        Parameters
        ----------
        subreddit_name: :class:`str`
            The Subreddit name.
        sort: Optional[:class:`str`]
            Option to sort the submissions, default to `hot`
            Available options: `hot`, `new`, `top`, `rising`
        t: Optional[:class:`str`]
            Type for sorting submissions by `top`, default to `day`
            Available options: `hour`, `day`, `week`, `month`, `year`, `all`
        after: Optional[:class:`str`]
        dist: Optional[:class:`str`]
            Needed for pagnitions.

        Returns raw submissions list.
        """
        params = {"layout": "classic"}
        # Check for sort
        if sort in {"hot", "new", "top", "rising"}:
            params["sort"] = sort
            if sort == "top":
                if t not in {"hour", "day", "week", "month", "year", "all"}:
                    t = self._TOP_SORT_T
                params["t"] = t
        # Check for pagnition
        if after and dist:
            params["after"] = after
            params["dist"] = dist

        return await self._get(f"/subreddits/{subreddit_name}", params=params, **kwargs)


class PushShiftAPI:
    """
    The Client that interacts with the PushShift API and returns raw JSON.
    Httpx options can be passed in when creating the client.

    This acts as a helper to fetch past submissions based on time range (which is not provided by reddit).
    To get the comments, it's recommended to use offical Gateway API as source.
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
    _DEFAULT_SORT = "desc"
    _DEFAULT_SIZE = 100

    def __init__(self, **options: Any):
        self._client: Optional[httpx.AsyncClient] = None
        self._x_reddit_loid: str = "0"
        self._x_reddit_session: str = "0"
        self.options = options

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            headers=self._DEFAULT_HEADER,
            params=self._DEFAULT_PARAMS,
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
            elif r.status == 429:
                log.warning("Rate limited!! Sleep for 60 secs")
                await asyncio.sleep(60)
                continue

            # we've received a 500, 502 or 504, an unconditional retry
            elif r.status in {500, 502, 504}:
                await asyncio.sleep(tries * 5)
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
    ):
        """
        Get submissions list from a subreddit.

        Parameters
        ----------
        subreddit_name: :class:`str`
            The Subreddit name.
        before: Optional[:class:`int`]
        after: Optional[:class:`int`]
            Provide epoch time (without ms) to get posts from a time range.
            Default to `None` to get latest posts.
        sort: Optional[:class:`str`]
            Option to sort the submissions, default to `desc`
            Available options: `asc`, `desc`
        size: Optional[:class:`int`]
            Size of list to fetch. Default to maximum of 100.

        Returns submissions list.
        """
        res = await self._get(
            "/reddit/search/submission",
            {
                "after": after,
                "before": before,
                "subreddit": subreddit_name,
                "sort": sort,
                "size": size,
            },
        )
        return res["data"]
