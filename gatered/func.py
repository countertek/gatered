from typing import Any, Dict, Optional

from gatered.client import Client


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


# TODO: add subreddit posts pagnition helper (need to investigate how async for loop)

# TODO: add pushshift loop support (need to investigate how async for loop can help)
