# GateRed

Reddit Gateway API Library, w/ pushshift history support.

[![CI](https://github.com/countertek/gatered/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/countertek/gatered/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Introduction

The idea is to access reddit data without logins and limits through its web API and proxy support.

## Documentation

### Installing

You can install this library easily from pypi:

```bash
# with pip
pip install gatered

# with poetry
poetry add gatered
```

### Using

TBD


## Plan

- [x] Reddit Gateway API (fetch posts and comments)
- [x] Add support to fetch past submissions using pushshift
- [x] Add GitHub Action CI check and publish flow
- [x] Publish on PyPI w/ portry
- [x] Handle pagination through async generators
- [ ] Refine documentation in README and add examples
- [ ] Make an example sandbox in replit
- [ ] Prepare test cases

