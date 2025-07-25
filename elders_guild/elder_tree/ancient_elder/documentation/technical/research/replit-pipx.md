---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
title: Untitled Document
version: 1.0.0
---

To use aider with pipx on replit, you can run these commands in the replit shell:

```bash
pip install pipx
pipx run aider-chat ...normal aider args...
```

If you install aider with pipx on replit and try and run it as just `aider` it will crash with a missing `libstdc++.so.6` library.

