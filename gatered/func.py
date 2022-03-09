from typing import Any, Optional
from functools import partial
from itertools import chain
import aiometer

from gatered.client import Client


async def get_post_comments(
    client: Client,
    submission_id: str,
    sort: Optional[str] = None,
    all_comments: bool = False,
    max_at_once: int = 8,
    max_per_second: int = 4,
    **kwargs: Any,
):
    """
    Get submission and its comments.
    If `more_comments` is `True`, it will fetch all the comments that are nested by reddit.

    Parameters
    ----------
    client: :class:`Client`
        Connected client instance of GateRed.
    submission_id: :class:`str`
        The Submission id (starts with `t3_`).
    sort: Optional[:class:`str`]
        Option to sort the comments of the submission, default to `None` (best)
        Available options: `top`, `new`, `controversial`, `old`, `qa`.
    all_comments: Optional[:class:`bool`]
        Set this to `True` to also get all nested comments. Default to `False`.
    max_at_once: Optional[:class:`int`]
        Limits the maximum number of concurrently requests for all comments. Default to 8.
    max_per_second: Optional[:class:`int`]
        Limits the number of requests spawned per second. Default to 4.

    Returns `post` (submission) and its `comments` as list
    """
    raw_json = await client.get_post_comments(submission_id, sort, **kwargs)

    post = raw_json["posts"].get(submission_id)
    comments = list(raw_json["comments"].values())

    more_comments = list(raw_json["moreComments"].values())

    if all_comments and more_comments:
        while more_comments:
            reqs = [
                partial(client.get_more_comments, submission_id, mc["token"], **kwargs)
                for mc in more_comments
            ]
            aggr_res = await aiometer.run_all(
                reqs,
                max_at_once=max_at_once,
                max_per_second=max_per_second,
            )

            # Add comments to comments
            comments += list(
                chain.from_iterable(
                    [list(res["comments"].values()) for res in aggr_res]
                )
            )
            # Extract more comments
            more_comments = list(
                chain.from_iterable(
                    [list(res["moreComments"].values()) for res in aggr_res]
                )
            )

    return {"post": post, "comments": comments}


async def get_posts(
    client: Client,
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
    raw_json = await client.get_posts(subreddit_name, sort, t, after, dist, **kwargs)

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
