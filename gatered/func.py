"""
This module contains easy functions to acquire information from Reddit. 
All functions are async and can be called directly without context manager.
"""
from typing import Any, Dict, Optional
from functools import partial
from asyncio import sleep
from aiometer import run_all
import logging

from gatered.client import Client
from gatered.pushshift import PushShiftAPI
from gatered.utils import datetime, get_timestamp

log = logging.getLogger(__name__)


async def get_post_comments(
    submission_id: str,
    all_comments: bool = False,
    sort: Optional[str] = None,
    httpx_options: Dict[str, Any] = {},
):
    """
    Helper function to get submission and its comments.

    Provide `submission_id` (starts with `t3_`) and
    if `all_comments` is `True`, it will fetch all the comments that are nested by reddit.

    Provide `sort` as an option to sort the comments of the submission, default to `None` (best).
    Available `sort` options: `top`, `new`, `controversial`, `old`, `qa`.

    Returns a dict with `post` as dict and its `comments` as list.
    """
    async with Client(**httpx_options) as client:
        return await client.get_post_comments(
            submission_id,
            sort=sort,
            all_comments=all_comments,
        )


async def get_posts_with_subreddit_info(
    subreddit_name: str,
    sort: Optional[str] = "hot",
    t: Optional[str] = "day",
    page_limit: Optional[int] = 4,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {},
):
    """
    Async Generator to get submissions batch by batch, includes subreddit info on every yield.

    Returns an async generator that yields a dict with two fields, `posts` (list) and `subreddit` (dict).
    Use `async for` loop to handle the results.

    - `subreddit_name` (str):
        The Subreddit name.
    - `sort` (str):
        Option to sort the submissions, default to `hot`.
        Available options: `hot`, `new`, `top`, `rising`
    - `t` (str):
        Type for sorting submissions by `top`, default to `day`.
        Available options: `hour`, `day`, `week`, `month`, `year`, `all`
    - `page_limit` (int):
        Set a request limit for pages to fetch. Disable this limit by passing `None`.
        Default to 4 (which will fetch 100 posts)
    - `req_delay` (int):
        Set delay between each page request. Set 0 to disable it. Default to 0.5.
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


async def get_posts(
    subreddit_name: str,
    sort: Optional[str] = "hot",
    t: Optional[str] = "day",
    page_limit: Optional[int] = 4,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {},
):
    """
    Async Generator to get submissions batch by batch.

    Returns an async generator that yields a list of posts.
    Use `async for` loop to handle the results.

    - `subreddit_name` (str):
        The Subreddit name.
    - `sort` (str):
        Option to sort the submissions, default to `hot`.
        Available options: `hot`, `new`, `top`, `rising`
    - `t` (str):
        Type for sorting submissions by `top`, default to `day`.
        Available options: `hour`, `day`, `week`, `month`, `year`, `all`
    - `page_limit` (int):
        Set a request limit for pages to fetch. Disable this limit by passing `None`.
        Default to 4 (which will fetch 100 posts)
    - `req_delay` (int):
        Set delay between each page request. Set 0 to disable it. Default to 0.5.
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
            yield data["posts"]

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


async def get_comments(
    submission_id: str,
    sort: Optional[str] = None,
    max_at_once: int = 8,
    max_per_second: int = 4,
    httpx_options: Dict[str, Any] = {},
):
    """
    Async Generator to get all comments batch by batch.

    Returns an async generator that yields a list of comments. Use `async for` loop to handle the results.

    - `submission_id` (str):
        The Submission id (starts with `t3_`).
    - `sort` (str):
        Option to sort the comments of the submission, default to `None` (best).
        Available options: `top`, `new`, `controversial`, `old`, `qa`.
    - `max_at_once` (int):
        Limits the maximum number of concurrently requests when fetching nested comments. Default to 8.
    - `max_per_second` (int):
        Limits the number of requests spawned per second when fetching nested comments. Default to 4.
    """
    log.debug(f"Fetching comments from submission *{submission_id}*")

    async with Client(**httpx_options) as client:
        raw_json = await client.raw_get_post_comments(submission_id, sort)
        yield list(raw_json["comments"].values())

        more_comments = raw_json["moreComments"].values()
        while more_comments:
            reqs = [
                partial(client.raw_get_more_comments, submission_id, mc["token"])
                for mc in more_comments
            ]
            aggr_res = await run_all(
                reqs,
                max_at_once=max_at_once,
                max_per_second=max_per_second,
            )

            # Yield comments
            yield [c for res in aggr_res for c in res["comments"].values()]

            # Extract more comments
            more_comments = [
                mc for res in aggr_res for mc in res["moreComments"].values()
            ]


async def get_pushshift_posts(
    subreddit_name: str,
    start_desc: datetime = None,
    end_till: datetime = None,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {},
):
    """
    Async Generator to get archived submissions by time range from pushshift.

    Returns an async generator that yields a list of posts. Use `async for` loop to handle the results.

    - `subreddit_name` (str):
        Name of the subreddit.
    - `start_desc` (`Optional[datetime]`):
        Provide `datetime` to get posts of a time range.
        Default to `None` to get from latest posts.
    - `end_till` (`Optional[datetime]`):
        Provide `datetime` to get posts of a time range.
        Default to `None` to get all existing posts.
    - `req_delay` (int):
        Set delay between each page request. Set 0 to disable it. Default to 0.5.
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
