from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from functools import partialmethod
from itertools import chain
from typing import Any, Optional, TypeVar

import aiohttp
from typing_extensions import TypeAlias

T = TypeVar("T")
log = logging.getLogger(__name__)
StrOrURL = aiohttp.client.StrOrURL
RequestType: TypeAlias = "Coroutine[None, None, Optional[T]]"


class Client:
    """The Client that interacts with the Reddit gateway API."""

    _BASE_URL = "https://gateway.reddit.com/desktopapi/v1"
    _KEEP_SESSION_HEADER = False
    _SUBREDDIT_SORT = "hot"
    _TOP_SORT_T = "day"

    def __init__(self, **options: Any):
        self._session: Optional[aiohttp.ClientSession] = None

        self.use_reddit_session: bool = options.get(
            "use_reddit_session", self._KEEP_SESSION_HEADER)
        self._x_reddit_loid: Optional[str] = None
        self._x_reddit_session: Optional[str] = None

        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Origin': 'https://www.reddit.com',
            'Referer': 'https://www.reddit.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
        }
        self.default_params = {
            # rtj (rich text json) is excluded
            'redditWebClient': 'web2x',
            'app': 'web2x-client-production',
            'allow_over18': 1,
        }

        self.proxy: Optional[str] = options.get("proxy")
        self.proxy_auth: Optional[aiohttp.BasicAuth] = options.get(
            "proxy_auth")
        self.connector: Optional[aiohttp.BaseConnector] = options.get(
            "connector")

        # Init http client
        self.recreate()

    def reset_reddit_session(self) -> None:
        self._x_reddit_loid: Optional[str] = '0'
        self._x_reddit_session: Optional[str] = '0'

    def recreate(self) -> None:
        self.reset_reddit_session()
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(connector=self.connector)

    async def close(self) -> None:
        await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _request(self, method: str, url: StrOrURL, **kwargs: Any) -> Optional[Any]:
        kwargs["headers"] = {**self.headers, **kwargs.get("headers", {})}
        if self.use_reddit_session:
            kwargs["headers"].update({
                'x-reddit-loid': self._x_reddit_loid,
                'x-reddit-session': self._x_reddit_session
            })

        # proxy support
        if not kwargs.get('proxy') and self.proxy is not None:
            kwargs["proxy"] = self.proxy
        if not kwargs.get('proxy_auth') and self.proxy_auth is not None:
            kwargs["proxy_auth"] = self.proxy_auth

        for tries in range(5):
            async with self._session.request(method, url, **kwargs) as r:
                log.debug(
                    f"{method} {r.url} *{kwargs.get('data')}* has returned {r.status}")

                # success return the text/json
                if 200 <= r.status < 300:
                    r_loid = r.headers.get("x-reddit-loid", '')
                    r_session = r.headers.get("x-reddit-session", '')

                    if self.use_reddit_session and self._x_reddit_loid != '0':
                        self._x_reddit_loid = r_loid
                        self._x_reddit_session = r_session
                    try:
                        data = await r.json()
                        data['_x-reddit-loid'] = r_loid
                        data['_x-reddit-session'] = r_session
                    except aiohttp.ContentTypeError:
                        data = await r.text()

                    return data

                # rate limited (this is not tested)
                elif r.status == 429:
                    log.warning("We are being Rate limited")
                    try:
                        await asyncio.sleep(float(r.headers["X-Retry-After"]))
                    except KeyError:
                        await asyncio.sleep(2 ** tries)
                    continue

                # we've received a 500, 502 or 504, an unconditional retry
                elif r.status in {500, 502, 504}:
                    await asyncio.sleep(1 + tries * 3)
                    continue

                # then usual error cases - 403, 404 ...
                else:
                    r.raise_for_status()

        # we've run out of retries, raise
        r.raise_for_status()

    _get: Callable[..., RequestType] = partialmethod(_request, "GET")
    _post: Callable[..., RequestType] = partialmethod(_request, "POST")

    # -- Request endpoints impl. --

    async def raw_get_more_comments(self, submission_id: str, token: str, **kwargs: Any):
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
        params = {
            'emotes_as_images': 'true',
            **self.default_params,
        }
        return await self._post(f"{self._BASE_URL}/morecomments/{submission_id}", params=params, json=payload, **kwargs)

    async def raw_get_submission(self, submission_id: str, sort: Optional[str] = None, **kwargs: Any):
        """
        Get submission and its details (comments and its related info).

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
            'emotes_as_images': 'true',
            **self.default_params,
            'hasSortParam': 'false',
            'include_categories': 'true',
            'onOtherDiscussions': 'false',
        }
        if sort in {'top', 'new', 'controversial', 'old', 'qa'}:
            params['hasSortParam'] = 'true'
            params['sort'] = sort

        return await self._get(f"{self._BASE_URL}/postcomments/{submission_id}", params=params, **kwargs)

    async def raw_get_submissions(
        self,
        subreddit_name: str,
        sort: Optional[str] = _SUBREDDIT_SORT,
        t: Optional[str] = _TOP_SORT_T,
        after: Optional[str] = None,
        dist: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Get submissions list from a subreddit.

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
        params = {
            **self.default_params,
            "layout": "classic",
        }
        # Check for sort
        if sort in {'hot', 'new', 'top', 'rising'}:
            params['sort'] = sort
            if sort == 'top':
                if t not in {'hour', 'day', 'week', 'month', 'year', 'all'}:
                    t = self._TOP_SORT_T
                params['t'] = t
        # Check for pagnition
        if after and dist:
            params['after'] = after
            params['dist'] = dist

        # may need to filter ads in the client
        return await self._get(f"{self._BASE_URL}/subreddits/{subreddit_name}", params=params, **kwargs)

    # -- Main Methods --

    async def get_submission(
        self,
        submission_id: str,
        sort: Optional[str] = None,
        all_comments: bool = False,
        keep_reddit_session: bool = True,
        **kwargs: Any
    ):
        """
        Get submission and its comments.
        If `more_comments` is `True`, it will fetch all the comments that are nested by reddit. 

        Parameters
        ----------
        submission_id: :class:`str`
            The Submission id (starts with `t3_`).
        sort: Optional[:class:`str`]
            Option to sort the comments of the submission, default to None (best)
            Available options: `top`, `new`, `controversial`, `old`, `qa`.
        all_comments: Optional[:class:`bool`]
            Set this to `True` to also get all nested comments. Default to `False`.
        keep_reddit_session: Optional[:class:`bool`]
            Set this to `True` to use same reddit session for fetching all nested comments. Default to `True`.
            This option is ignored when `self.use_reddit_session` is set to `True`.

        Returns `post` (submission) and its `comments` as list
        """
        raw_json = await self.raw_get_submission(submission_id, sort, **kwargs)

        post = raw_json['posts'].get(submission_id)
        comments = list(raw_json['comments'].values())

        more_comments = list(raw_json['moreComments'].values())

        if all_comments and more_comments:
            if not self.use_reddit_session and keep_reddit_session:
                kwargs["headers"] = {
                    **kwargs.get("headers", {}),
                    'x-reddit-loid': raw_json.get('_x-reddit-loid'),
                    'x-reddit-session': raw_json.get('_x-reddit-session'),
                }

            # ? ENHANCE: Async recursion function might be faster?
            while more_comments:
                multiple_requests = [self.raw_get_more_comments(
                    submission_id, mc['token'], **kwargs) for mc in more_comments]
                aggr_res = await asyncio.gather(*multiple_requests)

                # Add comments to comments
                comments += list(chain.from_iterable(
                    [list(res['comments'].values()) for res in aggr_res]))

                # Extract more comments
                more_comments = list(chain.from_iterable(
                    [list(res['moreComments'].values()) for res in aggr_res]))

        return {'post': post, 'comments': comments}

    async def get_submissions(
        self,
        subreddit_name: str,
        sort: Optional[str] = _SUBREDDIT_SORT,
        t: Optional[str] = _TOP_SORT_T,
        after: Optional[str] = None,
        dist: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Get submissions list from a subreddit, with ads filtered.
        This provides flexibility for you to handle pagninations by yourself.
        (Since I'm not sure it's a good idea to provide an iterable or a full list.
        Therefore I leave the implementation to you only by providing the basic function.)

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

        Returns `subreddit` and its `posts` (submissions) as list, as well as `token` and `dist` for paginations.
        """
        raw_json = await self.raw_get_submissions(subreddit_name, sort, t, after, dist, **kwargs)

        subreddit_info = {
            **(list(raw_json['subreddits'].values())[0]),
            **(list(raw_json['subredditAboutInfo'].values())[0])
        }
        posts = [
            raw_json['posts'].get(i)
            for i in raw_json['postIds']
            if not i.startswith('t3_z=')
        ]

        return {
            'subreddit': subreddit_info,
            'posts': posts,
            'sort': raw_json.get('listingSort'),
            'token': raw_json.get('token'),
            'dist': raw_json.get('dist'),
            '_x-reddit-loid': raw_json.get('_x-reddit-loid'),
            '_x-reddit-session': raw_json.get('_x-reddit-session'),
        }
