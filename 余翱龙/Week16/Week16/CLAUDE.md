# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a minimal Werewolf (狼人杀) game rules reference combined with a simple OpenAI API example using Alibaba's DashScope service (qwen-plus model).

## Running the Code

```bash
# Set API key environment variable, then run:
D:/python_code/extension/.venv/Scripts/python.exe chat_case.py
```

Requires `DASHSCOPE_API_KEY` environment variable (or replace with direct API key).

## Code Structure

- **chat_case.py** - Single-file OpenAI/DashScope API example. Uses OpenAI SDK with Alibaba's DashScope base URL to call `qwen-plus` model.
- **Game Rules.md** - Werewolf game rules reference documentation (non-code).

No build system, tests, or linting infrastructure exists.