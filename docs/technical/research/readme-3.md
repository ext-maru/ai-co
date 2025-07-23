---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: 'Doc: https://docs.litellm.ai/docs/completion/batching LiteLLM Python
  SDK allows you to: 1. `litellm.batch_completion` Batch litellm.completion function
  for a given model. 2. `litellm.batch_completion_'
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: research
tags:
- technical
- python
title: Implementation of `litellm.batch_completion`, `litellm.batch_completion_models`,
  `litellm.batch_completion_models_all_responses`
version: 1.0.0
---

# Implementation of `litellm.batch_completion`, `litellm.batch_completion_models`, `litellm.batch_completion_models_all_responses`

Doc: https://docs.litellm.ai/docs/completion/batching


LiteLLM Python SDK allows you to:
1. `litellm.batch_completion` Batch litellm.completion function for a given model.
2. `litellm.batch_completion_models` Send a request to multiple language models concurrently and return the response
    as soon as one of the models responds.
3. `litellm.batch_completion_models_all_responses` Send a request to multiple language models concurrently and return a list of responses
    from all models that respond.