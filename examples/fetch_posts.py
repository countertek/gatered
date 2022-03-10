# TODO: implement simple fetch example

import asyncio
from gatered import get_posts


async def fetch_posts(subreddit_name: str):
    async for data in get_posts(subreddit_name):
        print(len(data["posts"]))
        print(data["posts"][0])


async def fetch_posts_aggregate(subreddit_name: str):
    res = [post async for data in get_posts(subreddit_name) for post in data["posts"]]
    print(len(res))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_posts("Eldenring"))
