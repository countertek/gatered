# TODO: implement simple fetch example

import asyncio
from gatered import get_post_comments


async def fetch_post(submission_id: str):
    return await get_post_comments(submission_id, all_comments=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(fetch_post("t3_t97ji9"))

    print(res["post"])
    print(len(res["comments"]))
