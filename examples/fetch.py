# TODO: implement simple fetch example

import asyncio
from gatered import Client, get_post_comments


async def fetch_submissions():
    client = Client()

    async with client:
        # res = await client.get_post_comments("t3_t97ji9")
        # res = await client.get_posts('Eldenring')
        res = await get_post_comments(client, "t3_t97ji9", all_comments=True)
        print(res['post'])
        print(len(res['comments']))



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_submissions())
