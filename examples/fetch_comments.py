import asyncio
from gatered import get_comments
from pprint import pprint


async def fetch_comments(submission_id: str):
    async for comments in get_comments(submission_id, all_comments=False):
        pprint(comments[0])
        pprint(len(comments))


async def fetch_comments_aggregate(submission_id: str):
    res = [
        comment
        async for comments in get_comments(submission_id, all_comments=True)
        for comment in comments
    ]
    pprint(len(res))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_comments("t3_t97ji9"))
