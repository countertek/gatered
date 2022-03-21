import asyncio
from gatered import get_comments


async def fetch_comments(submission_id: str):
    async for comments in get_comments(submission_id, all_comments=True):
        print(len(comments))
        print(comments[0])


async def fetch_comments_aggregate(submission_id: str):
    res = [
        comment
        async for comments in get_comments(submission_id, all_comments=True)
        for comment in comments
    ]
    print(len(res))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_comments("t3_t97ji9"))
