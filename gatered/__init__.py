"""
gatered
~~~~~~~~~

A utils for interacting with Reddit Gateway API (Web API).
"""

__version__ = "0.3.0"

# Import error classes from httpx: https://www.python-httpx.org/exceptions/
from httpx import RequestError, HTTPStatusError

from .client import Client
from .pushshift import PushShiftAPI
from .func import get_post_comments, get_posts, get_pushshift_posts
