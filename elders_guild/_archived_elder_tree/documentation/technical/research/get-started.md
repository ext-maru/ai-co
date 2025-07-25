---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: cd /to/your/project aider --model deepseek --api-key deepseek=<key> aider
  --model sonnet --api-key anthropic=<key> aider --model o3-mini --api-key openai=<key>
  ```
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
- python
title: Change directory into your codebase
version: 1.0.0
---


If you already have python 3.8-3.13 installed, you can get started quickly like this.

First, install aider:

{% include install.md %}

Start working with aider on your codebase:

```bash
# Change directory into your codebase
cd /to/your/project

# DeepSeek
aider --model deepseek --api-key deepseek=<key>

# Claude 3.7 Sonnet
aider --model sonnet --api-key anthropic=<key>

# o3-mini
aider --model o3-mini --api-key openai=<key>
```
