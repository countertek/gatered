# TODO: implement simple fetch example

import asyncio

from gatered.client import BaseClient


async def fetch_submissions():
    client = BaseClient()

    async with client:
        # res = await client.get_post_comments("t97ji9")
        res = await client.get_posts('Eldenring')
        print(res)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_submissions())
