---
title: "Reranking Search Results"
source: "https://docs.lancedb.com/reranking/index"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Use a reranker to improve search relevance."
tags:
  - "clippings"
---
[Skip to main content](https://docs.lancedb.com/reranking/#content-area)

Reranking is the process of re-ordering search results to improve relevance, often using a different model than the one used for the initial search. LanceDB has built-in support for reranking with models from Cohere, Sentence-Transformers, and more.

### Quickstart

To use a reranker, you perform a search and then pass the results to the `rerank()` method.

### Supported Rerankers

LanceDB supports several rerankers out of the box. Here are a few examples:

| Reranker | Default Model |
| --- | --- |
| `CohereReranker` | `rerank-english-v2.0` |
| `CrossEncoderReranker` | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `ColbertReranker` | `colbert-ir/colbertv2.0` |

You can find more details about these and other rerankers in the [integrations](https://docs.lancedb.com/integrations/reranking) section.

### Multi-vector reranking

Most rerankers support reranking based on multiple vectors. To rerank based on multiple vectors, you can pass a list of vectors to the `rerank` method. Here’s an example of how to rerank based on multiple vector columns using the `CrossEncoderReranker`:

## Creating Custom Rerankers

LanceDB also you to create custom rerankers by extending the base `Reranker` class. The custom reranker should implement the `rerank` method that takes a list of search results and returns a reranked list of search results. This is covered in more detail in the [creating custom rerankers](https://docs.lancedb.com/reranking/custom-reranker) section.

Was this page helpful?

[FTS with SQL](https://docs.lancedb.com/search/sql/fts-sql) [Custom rerankers](https://docs.lancedb.com/reranking/custom-reranker)