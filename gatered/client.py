"""
This module defines gatered client to fetch information through Reddit webAPI (gateway.reddit.com).
"""
from typing import Any, Optional, TypeVar, Callable, Coroutine
from typing_extensions import TypeAlias
from functools import partial, partialmethod

from asyncio import sleep
from aiometer import run_all
from httpx import AsyncClient
import logging

T = TypeVar("T")
log = logging.getLogger(__name__)
_RequestType: TypeAlias = "Coroutine[None, None, Optional[T]]"


class Client:
    """
    The Client that interacts with Reddit webAPI and returns raw JSON as `dict`.
    [httpx options](https://www.python-httpx.org/api/#asyncclient) can be passed in when creating the client such as `proxies`.
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
        """
        Initialize a `Client` object, where `options` are
        [httpx options](https://www.python-httpx.org/api/#asyncclient).
        """
        self._client: Optional[AsyncClient] = None
        self._x_reddit_loid: str = "0"
        self._x_reddit_session: str = "0"
        self.options = options

    async def __aenter__(self):
        self._client = AsyncClient(
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
            elif r.status_code == 429:
                log.warning("Rate limited!!")
                try:
                    await sleep(float(r.headers["X-Retry-After"]))
                except KeyError:
                    await sleep(30 * tries)
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

    _get: Callable[..., _RequestType] = partialmethod(_request, "GET")
    _post: Callable[..., _RequestType] = partialmethod(_request, "POST")

    # -- Request endpoints impl. --

    async def raw_get_more_comments(
        self,
        submission_id: str,
        token: str,
        **kwargs: Any,
    ):
        """
        Get `comments` from a submission provided with a generated cache `moreComment` token.
        Returns raw JSON.

        - `submission_id` (str):
            The Submission id (starts with `t3_`)
        - `token` (str):
            Token for more comments content.
        """
        payload = {"token": token}
        params = {"emotes_as_images": "true"}
        return await self._post(
            f"/morecomments/{submission_id}",
            params=params,
            json=payload,
            **kwargs,
        )

    async def raw_get_post_comments(
        self,
        submission_id: str,
        sort: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Get `post` and its `comments` + `moreComments` (including its related info).
        Return raw JSON.

        - `submission_id` (str):
            The Submission id (starts with `t3_`)
        - `sort` (str):
            Option to sort the comments of the submission, default to `None` (best).
            Available options: `top`, `new`, `controversial`, `old`, `qa`, `None`
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

    async def raw_get_posts(
        self,
        subreddit_name: str,
        sort: Optional[str] = _SUBREDDIT_SORT,
        t: Optional[str] = _TOP_SORT_T,
        after: Optional[str] = None,
        dist: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Get submissions list from a subreddit. This also includes advertisement submissions.
        Returns raw JSON.

        - `subreddit_name` (str):
            The Subreddit name.
        - `sort` (str):
            Option to sort the submissions, default to `hot`.
            Available options: `hot`, `new`, `top`, `rising`
        - `t` (str):
            Type for sorting submissions by `top`, default to `day`.
            Available options: `hour`, `day`, `week`, `month`, `year`, `all`
        - `after` (str) and `dist` (str):
            Included in the returned raw JSON. Used for pagination.
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

    async def get_post_comments(
        self,
        submission_id: str,
        sort: Optional[str] = None,
        all_comments: bool = False,
        max_at_once: int = 8,
        max_per_second: int = 4,
        **kwargs: Any,
    ):
        """
        Get submission and its comments.
        If `all_comments` is `True`, it will fetch all the comments that are nested by reddit.

        Returns a dict with `post` as dict and its `comments` as list

        - `submission_id` (str):
            The Submission id (starts with `t3_`).
        - `sort` (str):
            Option to sort the comments of the submission, default to `None` (best).
            Available options: `top`, `new`, `controversial`, `old`, `qa`.
        - `all_comments` (bool):
            Set this to `True` to also get all nested comments. Default to `False`.
        - `max_at_once` (int):
            Limits the maximum number of concurrently requests for fetching all comments. Default to 8.
        - `max_per_second` (int):
            Limits the number of requests spawned per second. Default to 4.
        """
        raw_json = await self.raw_get_post_comments(submission_id, sort, **kwargs)

        post = raw_json["posts"].get(submission_id)
        comments = list(raw_json["comments"].values())

        more_comments = raw_json["moreComments"].values()

        if all_comments and more_comments:
            while more_comments:
                reqs = [
                    partial(
                        self.raw_get_more_comments,
                        submission_id,
                        more_c["token"],
                        **kwargs,
                    )
                    for more_c in more_comments
                ]
                aggr_res = await run_all(
                    reqs,
                    max_at_once=max_at_once,
                    max_per_second=max_per_second,
                )

                # Add comments to comments
                comments += [c for res in aggr_res for c in res["comments"].values()]

                # Extract more comments
                more_comments = [
                    more_c
                    for res in aggr_res
                    for more_c in res["moreComments"].values()
                ]

        return {"post": post, "comments": comments}

    async def get_posts(
        self,
        subreddit_name: str,
        sort: Optional[str] = "hot",
        t: Optional[str] = "day",
        after: Optional[str] = None,
        dist: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Get submissions list from a subreddit, with ads filtered.
        This provides flexibility for you to handle pagninations by yourself.

        Returns a dict with `subreddit` and its `posts` as list, as well as `token` and `dist` for paginations.

        - `subreddit_name` (str):
            The Subreddit name.
        - `sort` (str):
            Option to sort the submissions, default to `hot`
            Available options: `hot`, `new`, `top`, `rising`
        - `t` (str):
            Type for sorting submissions by `top`, default to `day`
            Available options: `hour`, `day`, `week`, `month`, `year`, `all`
        - `after` (str) and `dist` (str):
            Used for pagination.
        """
        raw_json = await self.raw_get_posts(
            subreddit_name, sort, t, after, dist, **kwargs
        )

        subreddit_info = {
            **(list(raw_json["subreddits"].values())[0]),
            **(list(raw_json["subredditAboutInfo"].values())[0]),
        }
        posts = [
            raw_json["posts"].get(i)
            for i in raw_json["postIds"]
            if not i.startswith("t3_z=")
        ]

        return {
            "subreddit": subreddit_info,
            "posts": posts,
            "sort": raw_json.get("listingSort"),
            "token": raw_json.get("token"),
            "dist": raw_json.get("dist"),
        }
