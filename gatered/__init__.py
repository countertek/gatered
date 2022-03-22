"""
A utils for interacting with Reddit Gateway API (Web API), w/ pushshift historical posts support.

[![Latest Version](https://img.shields.io/pypi/v/gatered.svg)](https://pypi.python.org/pypi/gatered)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/gatered)](https://pypi.python.org/pypi/gatered)
[![CI](https://github.com/countertek/gatered/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/countertek/gatered/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub license](https://img.shields.io/github/license/countertek/gatered)](https://github.com/countertek/gatered/blob/main/LICENSE)

## Why this library?

Although Reddit has developer APIs and there are existing libraries (e.g. praw) to interact with reddit, there are still several drawbacks in terms of collecting data:

- An API key is needed to collect data.
- Rate limit is based on API keys.
- Some fields are missing using developer APIs.

Therefore, **gatered** exists just to counter this problem. It directly access Reddit's web API to get the whole information. No authentication is needed, and it supports proxy provided by [httpx](https://www.python-httpx.org/advanced/#http-proxying).

## Install

You can install this library easily from pypi:

```bash
# with pip
pip install gatered

# with poetry
poetry add gatered
```

## Using

The library provides easy functions to get start fast:
- `gatered.func.get_post_comments`
- `gatered.func.get_posts`
- `gatered.func.get_comments`
- `gatered.func.get_pushshift_posts`

Alternatively you can directly use `gatered.client.Client` and `gatered.pushshift.PushShiftAPI` classes as your base to implement your own logics.

Errors can be handled by importing either `gatered.RequestError` or `gatered.HTTPStatusError`, see [httpx exceptions](https://www.python-httpx.org/exceptions/) to learn more.

See [`examples/`](https://github.com/countertek/gatered/tree/main/examples/) for more examples.
"""

__version__ = "1.1.1"

# Import error classes from httpx: https://www.python-httpx.org/exceptions/
from httpx import RequestError, HTTPStatusError

from .client import Client
from .pushshift import PushShiftAPI
from .func import get_post_comments, get_posts, get_comments, get_pushshift_posts
