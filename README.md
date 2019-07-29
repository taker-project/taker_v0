# Taker-v0

[![Build Status](https://travis-ci.com/taker-project/taker_v0.svg?branch=master)](https://travis-ci.com/taker-project/taker_v0)
[![codecov](https://codecov.io/gh/taker-project/taker_v0/branch/master/graph/badge.svg)](https://codecov.io/gh/taker-project/taker_v0)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

First version of Taker problem preparation system.

## What is it?

It's a competitive programming contest preparation system, just like [Polygon](https://polygon.codeforces.com). But it will have some advantages, like possibility to use it locally, being more modular (core tools can be run everywhere, and some web/GUI interface can be built upon them). And, in the end it's released as free software.

## Why it is called Taker?

The answer is: `taker = task + maker`. Also, the name is simillar to `make`, which will be used to conrol the dependencies.

Also, there are some concepts on how to rename it.

## Specification

Some initial work was [in this repo](https://github.com/taker-project/taker-specs). The format will evolve from these docs.

## Work plan

The plan for the project development is improving by code rewriting in several iterations. Initial plan for iterations is (this may change):
- v0&mdash; basic prototype: add main functionality, start creating the problem format. This will be written on Python
- v1&mdash; more production-ready version: stabilize the problem format, add more functionality, write some tests
- v2&mdash; final version: rewrite to C++ (?), fully stabilize the format

Initially, Taker will be command-line. After the initial stable release, work on GUI or Web tools can be started.

## When will it become 1.0?

I don't know.

## Build dependencies

* `make` (not necessarily GNU Make, because Makefiles in this project tries to be POSIX-compatible)
* `python (works on 3.5, 3.6 and 3.7)`, `pip`, `venv`
* `g++` (or `clang`)
* `cmake` for runners
* `libjsoncpp` for runners (on Debian/Ubuntu, you can use `libjsoncpp-dev` package)

## OS support

Currently the project targets UNIX-like OSes and is tested on _GNU/Linux_, _macOS_ and _FreeBSD_. Other OS support will be added later.

The least portable part of Taker is the process runner. For UNIXes, it is `taker_unixrun`. It mostly uses POSIX-compatible routines, but there may be problems while porting it to some other UNIX-like OS. Now it works on the following ones:

* GNU/Linux
* FreeBSD
* macOS \[thanks to [Travis CI](https://travis-ci.org) for macOS builds :) \]

Note that on OSes other than GNU/Linux, `taker_unixrun` uses `ru_maxrss` for `getrusage()`, which not always gives the correct value for consumed memory. So, GNU/Linux is supported best now.

Taker's build system is also tightly integrated with UNIXes. So, to port Taker on Windows, some additional effort is required.
