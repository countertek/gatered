import asyncio
from gatered import get_post_comments
from pprint import pprint


async def fetch_all_post_comments(submission_id: str):
    res = await get_post_comments(submission_id, all_comments=True)

    pprint(res["post"])
    pprint(res["comments"][0])
    pprint(len(res["comments"]))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_all_post_comments("t3_t97ji9"))
