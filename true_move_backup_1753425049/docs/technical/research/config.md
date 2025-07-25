---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: Aider has many options which can be set with command line switches. Most
  options can also be set in an `.aider.conf.yml` file which can be placed in your
  home directory or at the root of your git repo
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
title: Configuration
version: 1.0.0
---

---
nav_order: 55
has_children: true
description: Information on all of aider's settings and how to use them.
---

# Configuration

Aider has many options which can be set with
command line switches.
Most options can also be set in an `.aider.conf.yml` file
which can be placed in your home directory or at the root of
your git repo. 
Or by setting environment variables like `AIDER_xxx`
either in your shell or a `.env` file.

Here are 4 equivalent ways of setting an option. 

With a command line switch:

```
$ aider --dark-mode
```

Using a `.aider.conf.yml` file:

```yaml
dark-mode: true
```

By setting an environment variable:

```
export AIDER_DARK_MODE=true
```

Using an `.env` file:

```
AIDER_DARK_MODE=true
```

{% include keys.md %}

