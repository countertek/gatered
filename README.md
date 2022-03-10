# GateRed

Reddit Gateway API Library, w/ pushshift history support.

[![CI](https://github.com/countertek/gatered/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/countertek/gatered/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Introduction

The idea is to access reddit data without logins and limits through its web API and proxy support.

### Installing

You can install this library easily from pypi:

```bash
# with pip
pip install gatered

# with poetry
poetry add gatered
```

### Using

The library provides easy functions to get start fast:
- `get_post_comments`
- `get_posts`
- `get_pushshift_posts`

Alternatively you can directly use `Client` and `PushShiftAPI` classes to implement your own logics.

Check the `examples` folder to learn more.

## Documentation

<a href="./gatered/func.py#L12"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_post_comments`

```python
get_post_comments(
    submission_id: str,
    all_comments: bool = False,
    httpx_options: Dict[str, Any] = {}
)
```

Helper function to get submission and its comments. If `all_comments` is `True`, it will fetch all the comments that are nested by reddit. 

Returns `post` (submission) and its `comments` as list.

#### Parameters 

submission_id: :class:`str`  
The Submission id (starts with `t3_`). 

all_comments: Optional[:class:`bool`]  
Set this to `True` to also get all nested comments. Default to `False`. 


<a href="./gatered/func.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_posts`

```python
get_posts(
    subreddit_name: str,
    sort: Optional[str] = 'hot',
    t: Optional[str] = 'day',
    page_limit: Optional[int] = 4,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {}
)
```

Async Generator to get submissions page by page.

Returns an async generator. Use async for loop to handle page results.

#### Parameters

subreddit_name: :class:`str`  
Name of the subreddit. 

sort: Optional[:class:`str`]  
Option to sort the submissions, default to `hot`  
Available options: `hot`, `new`, `top`, `rising` 

t: Optional[:class:`str`]  
Type for sorting submissions by `top`, default to `day`  
Available options: `hour`, `day`, `week`, `month`, `year`, `all` 

page_limit: Optional[:class:`int`]  
Set a request limit for pages to fetch. Disable this limit by passing `None`.  Default to 4 (which will fetch 100 posts) 

req_delay: Optional[:class:`int`]  
Set delay between each page request. Set 0 to disable it. Default to 0.5. 


<a href="./gatered/func.py#L93"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_pushshift_posts`

```python
get_pushshift_posts(
    subreddit_name: str,
    start_desc: datetime = None,
    end_till: datetime = None,
    req_delay: int = 0.5,
    httpx_options: Dict[str, Any] = {}
)
```

Async Generator to get submissions by time range. 

Returns an async generator. Use async for loop to handle page results. 

#### Parameters

subreddit_name: :class:`str`  
Name of the subreddit. 

start_desc: Optional[:class:`datetime`]  
Provide `datetime` to get posts of a time range. Default to `None` to get from latest posts. 

end_till: Optional[:class:`datetime`]  
Provide `datetime` to get posts of a time range.  Default to `None` to get all existing posts. 

req_delay: Optional[:class:`int`]  
Set delay between each page request. Set 0 to disable it. Default to 0.5. 

---

<a href="./gatered/client.py#L16"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Client`
The Client that interacts with the Reddit gateway API and returns raw JSON.  
Httpx options can be passed in when creating the client such as proxies: https://www.python-httpx.org/api/#asyncclient 

<a href="./gatered/client.py#L42"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(**options: Any)
```

<a href="./gatered/client.py#L220"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_post_comments`

```python
get_post_comments(
    submission_id: str,
    sort: Optional[str] = None,
    all_comments: bool = False,
    max_at_once: int = 8,
    max_per_second: int = 4,
    **kwargs: Any
)
```

Get submission and its comments. If `all_comments` is `True`, it will fetch all the comments that are nested by reddit.

Returns `post` (submission) and its `comments` as list.

#### Parameters 

submission_id: :class:`str`  
The Submission id (starts with `t3_`).

sort: Optional[:class:`str`]  
Option to sort the comments of the submission, default to `None` (best)  Available options: `top`, `new`, `controversial`, `old`, `qa`. 

all_comments: Optional[:class:`bool`]  
Set this to `True` to also get all nested comments. Default to `False`.  

max_at_once: Optional[:class:`int`]  
Limits the maximum number of concurrently requests for all comments. Default to 8. 

max_per_second: Optional[:class:`int`]  
Limits the number of requests spawned per second. Default to 4. 


<a href="./gatered/client.py#L285"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_posts`

```python
get_posts(
    subreddit_name: str,
    sort: Optional[str] = 'hot',
    t: Optional[str] = 'day',
    after: Optional[str] = None,
    dist: Optional[int] = None,
    **kwargs: Any
)
```

Get submissions list from a subreddit, with ads filtered. This provides flexibility for you to handle pagninations by yourself.

Returns `subreddit` and its `posts` (submissions) as list, as well as `token` and `dist` for paginations. 

#### Parameters 

subreddit_name: :class:`str`  
The Subreddit name. 

sort: Optional[:class:`str`]  
Option to sort the submissions, default to `hot`   
Available options: `hot`, `new`, `top`, `rising` 

t: Optional[:class:`str`]  Type for sorting submissions by `top`, default to `day`  Available options: `hour`, `day`, `week`, `month`, `year`, `all` 

after: Optional[:class:`str`], dist: Optional[:class:`str`]  
Needed for pagnitions. 

---

<a href="./gatered/pushshift.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `PushShiftAPI`
The Client that interacts with the PushShift API and returns raw JSON. Httpx options can be passed in when creating the client. 

This acts as a helper to fetch past submissions based on time range (which is not provided by reddit). To get the comments, it's recommended to use offical Gateway API as source. 

<a href="./gatered/pushshift.py#L37"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(**options: Any)
```

<a href="./gatered/pushshift.py#L83"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_posts`

```python
get_posts(
    subreddit_name: str,
    before: int = None,
    after: int = None,
    sort: str = 'desc',
    size: int = 100,
    **kwargs: Any
)
```

Get submissions list from a subreddit. 

Returns a list of submissions. 

#### Parameters 

subreddit_name: :class:`str`  
The Subreddit name. 

before: Optional[:class:`int`], after: Optional[:class:`int`]  
Provide epoch time (without ms) to get posts from a time range. Default to `None` to get latest posts. 

sort: Optional[:class:`str`]  
Option to sort the submissions, default to `desc`  
Available options: `asc`, `desc` 

size: Optional[:class:`int`]  
Size of list to fetch. Default to maximum of 100. 

---

## Plan

- [x] Reddit Gateway API (fetch posts and comments)
- [x] Add support to fetch past submissions using pushshift
- [x] Add GitHub Action CI check and publish flow
- [x] Publish on PyPI w/ portry
- [x] Handle pagination through async generators
- [x] Refine documentation in README and add examples
- [ ] Make an example sandbox in replit
- [ ] Prepare test cases
