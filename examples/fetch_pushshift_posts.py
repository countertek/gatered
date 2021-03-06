import asyncio
from gatered import get_pushshift_posts
from datetime import datetime
from pprint import pprint


start_desc = datetime(2022, 3, 1)
end_till = datetime(2022, 2, 26)


async def fetch_posts(subreddit_name: str):
    async for data in get_pushshift_posts(
        subreddit_name,
        start_desc=start_desc,
        end_till=end_till,
    ):
        pprint(data[0])
        pprint(len(data))


async def fetch_posts_aggregate(subreddit_name: str):
    res = [
        post
        async for data in get_pushshift_posts(
            subreddit_name,
            start_desc=start_desc,
            end_till=end_till,
        )
        for post in data
    ]
    pprint(len(res))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_posts("ethereum"))
