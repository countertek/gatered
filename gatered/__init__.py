"""
A library to fetch Reddit data using Reddit WebAPI (gateway), w/ pushshift historical submissions support.

[![Latest Version](https://img.shields.io/pypi/v/gatered.svg)](https://pypi.python.org/pypi/gatered)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/gatered)](https://pypi.python.org/pypi/gatered)
[![CI](https://github.com/countertek/gatered/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/countertek/gatered/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub license](https://img.shields.io/github/license/countertek/gatered)](https://github.com/countertek/gatered/blob/main/LICENSE)

**[Documentation](https://countertek.github.io/gatered)**
**·**
**[Replit Playground](https://replit.com/@darekaze/gatered-examples#main.py)**

## Why this library?

Although there are existing libraries (e.g. praw) to interact with Reddit developer's API,
there are still several drawbacks when we try to collect vast amount of data.
**gatered** tries to counter these problems to provide these features:

- No authentication (API key) is needed to access the data.
- Extra attributes is presented using the Reddit webAPI compared to the public devAPI.
- Fully Async based.
- Proxy support via [httpx](https://www.python-httpx.org/advanced/#http-proxying).

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
- `gatered.func.get_posts_with_subreddit_info`
- `gatered.func.get_posts`
- `gatered.func.get_comments`
- `gatered.func.get_pushshift_posts`

Alternatively you can directly use `gatered.client.Client` and `gatered.pushshift.PushShiftAPI` classes as your base to implement your own logics.

Errors can be handled by importing either `gatered.RequestError` or `gatered.HTTPStatusError`,
see [httpx exceptions](https://www.python-httpx.org/exceptions/) to learn more.

See [`examples/`](https://github.com/countertek/gatered/tree/main/examples/) for more examples.
Alternately, you can [fork the example repo on Replit](https://replit.com/@darekaze/gatered-examples#main.py) and play around online.

## License

Copyright 2022 CounterTek

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__version__ = "1.3.0"

# Import error classes from httpx: https://www.python-httpx.org/exceptions/
from httpx import RequestError, HTTPStatusError

from .client import Client
from .pushshift import PushShiftAPI
from .func import (
    get_post_comments,
    get_posts_with_subreddit_info,
    get_posts,
    get_comments,
    get_pushshift_posts,
)
