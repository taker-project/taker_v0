# Taker-v0 [![Build Status](https://travis-ci.com/taker-project/taker_v0.svg?branch=master)](https://travis-ci.com/taker-project/taker_v0)

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

Initially, Taker will be command-line. After the initial stable release, work on GUI tools can be started.

## When will it become 1.0?

I don't know.

## Build dependencies

* `make` (not necessarily GNU Make, because Makefiles in this project try to be POSIX-compatible)
* `python (tested on 3.6)`, `pip`, `venv`
* `g++` (or `clang`)
* `cmake` for runners
* `libjsoncpp` for runners (on Debian/Ubuntu, you can use `libjsoncpp-dev` package)

Currently the project targets UNIX-like OSes and will be tested on GNU/Linux and FreeBSD. Other OS support will be added later.
