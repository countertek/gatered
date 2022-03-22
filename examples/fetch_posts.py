import asyncio
from gatered import get_posts, get_posts_with_subreddit_info
from pprint import pprint


async def fetch_posts_with_subreddit_info(subreddit_name: str):
    async for data in get_posts_with_subreddit_info(subreddit_name):
        pprint(data["subreddit"])
        pprint(data["posts"][0])
        pprint(len(data["posts"]))


async def fetch_posts(subreddit_name: str):
    async for data in get_posts(subreddit_name):
        pprint(data[0])
        pprint(len(data))


async def fetch_posts_aggregate(subreddit_name: str):
    res = [post async for data in get_posts(subreddit_name) for post in data]
    pprint(len(res))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_posts("Eldenring"))
