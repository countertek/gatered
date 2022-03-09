"""
gatered
~~~~~~~~~

A utils for interacting with Reddit Gateway API (Web API).
"""

__version__ = "0.1.0"

# Import error classes from httpx: https://www.python-httpx.org/exceptions/
from httpx import RequestError, HTTPStatusError

from .client import Client, PushShiftAPI
from .func import get_posts, get_post_comments
