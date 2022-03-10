from typing import Any, Dict, Optional
from asyncio import sleep
import logging

from gatered.client import Client
from gatered.pushshift import PushShiftAPI
from gatered.utils import datetime, get_timestamp

log = logging.getLogger(__name__)


async def get_post_comments(
    submission_id: str,
    all_comments: bool = False,
    httpx_options: Dict[str, Any] = {},
):
    """
    Helper function to get submission and its comments.
    If `all_comments` is `True`, it will fetch all the comments that are nested by reddit.

    Parameters
    ----------
    submission_id: :class:`str`
        The Submission id (starts with `t3_`).
    all_comments: Optional[:class:`bool`]
        Set this to `True` to also get all nested comments. Default to `False`.

    Returns `post` (submission) and its `comments` as list
    """
    async with Client(**httpx_options) as client:
        return await client.get_post_comments(submission_id, all_comments=all_comments)


async def get_posts(
    subreddit_name: str,
    sort: Optional[str] = "hot",
    t: Optional[str] = "day",
    page_limit: Optional[int] = 4,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {},
):
    """
    Async Generator to get submissions page by page.

    Parameters
    ----------
    subreddit_name: :class:`str`
        Name of the subreddit.
    sort: Optional[:class:`str`]
        Option to sort the submissions, default to `hot`
        Available options: `hot`, `new`, `top`, `rising`
    t: Optional[:class:`str`]
        Type for sorting submissions by `top`, default to `day`
        Available options: `hour`, `day`, `week`, `month`, `year`, `all`
    page_limit: Optional[:class:`int`]
        Set a request limit for pages to fetch. Disable this limit by passing `None`.
        Default to 4 (which will fetch 100 posts)
    req_delay: Optional[:class:`int`]
        Set delay between each page request. Set 0 to disable it. Default to 0.5.

    Returns an async generator. Use async for loop to handle page results.
    """
    log.debug(f"Fetching submissions and comments from subreddit *{subreddit_name}*")

    async with Client(**httpx_options) as client:
        token, dist = None, None

        while True:
            data = await client.get_posts(
                subreddit_name,
                sort=sort,
                t=t,
                after=token,
                dist=dist,
            )
            yield data

            # Check continue condition
            token, dist = data.get("token"), data.get("dist")
            if not token:
                break

            # Handle page limit
            if isinstance(page_limit, (int, float)):
                page_limit -= 1
                if page_limit < 1:
                    break

            # Apply delay
            await sleep(req_delay)


async def get_pushshift_posts(
    subreddit_name: str,
    start_desc: datetime = None,
    end_till: datetime = None,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {},
):
    """
    Async Generator to get submissions by time range.

    Parameters
    ----------
    subreddit_name: :class:`str`
        Name of the subreddit.
    start_desc: Optional[:class:`datetime`]
        Provide `datetime` to get posts of a time range.
        Default to `None` to get from latest posts.
    end_till: Optional[:class:`datetime`]
        Provide `datetime` to get posts of a time range.
        Default to `None` to get all existing posts.
    req_delay: Optional[:class:`int`]
        Set delay between each page request. Set 0 to disable it. Default to 0.5.

    Returns an async generator. Use async for loop to handle page results.
    """
    log.debug(f"Fetching pushshift submissions from subreddit *{subreddit_name}*")

    async with PushShiftAPI(**httpx_options) as client:
        before = get_timestamp(start_desc) if start_desc else None
        after = get_timestamp(end_till) if end_till else None

        while True:
            data = await client.get_posts(subreddit_name, before=before, after=after)
            yield data

            # Check continue condition
            if len(data) < client._DEFAULT_SIZE:
                break

            # Continue and apply delay
            before = data[-1]["created_utc"]
            await sleep(req_delay)
