---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: Cohere offers *free* API access to their models. Their Command-R+ model
  works well with aider as a *very basic* coding assistant. You'll need a [Cohere
  API key](https://dashboard.cohere.com/welcome/lo
difficulty: beginner
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
title: Cohere
version: 1.0.0
---

---
parent: Connecting to LLMs
nav_order: 500
---

# Cohere

Cohere offers *free* API access to their models.
Their Command-R+ model works well with aider
as a *very basic* coding assistant.
You'll need a [Cohere API key](https://dashboard.cohere.com/welcome/login).

First, install aider:

{% include install.md %}

Then configure your API keys:

```
export COHERE_API_KEY=<key> # Mac/Linux
setx   COHERE_API_KEY <key> # Windows, restart shell after setx
```

Start working with aider and Cohere on your codebase:

```bash
# Change directory into your codebase
cd /to/your/project

aider --model command-r-plus-08-2024

# List models available from Cohere
aider --list-models cohere_chat/
```
