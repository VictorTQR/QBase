---
title: "Multi-Vector Search | Zvec"
source: "https://zvec.org/en/docs/data-operations/query/multi-vector/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/) [Query](https://zvec.org/en/docs/data-operations/query/)

## Multi-Vector Search

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.query) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#querysync)

Zvec supports **multi-vector queries**, allowing you to combine different embeddings in a single search.

When querying multiple vector embeddings, Zvec retrieves top candidates from each vector space independently.  
Since similarity scores from different vector spaces might not be directly comparable, a **re-ranker** is required to fuse and and re-rank the results into a unified, relevance-ordered list.

---

## Prerequisites

This guide assumes:

- You have opened a `collection` with multiple vector fields
- You're familiar with the basic vector querying concepts. If not, please review the [single-vector search](https://zvec.org/en/docs/data-operations/query/single-vector/) guide

---

## Performing Multi-Vector Search

To run a multi-vector search, pass a list of [`VectorQuery`](https://zvec.org/en/docs/data-operations/query/single-vector/#vectorquery) objects to the `query()` method and specify a fusion strategy via the `reranker` parameter.

In multi-vector search, `topk` takes on a different meaning compared to single-vector queries:

- `topk` (in `query()`): Controls how many candidate documents are retrieved **from each vector field** before re-ranking. A larger `topk` gives the re-ranker more candidates to work with, potentially improving final quality but increasing computational cost.
- `topn` (in `ReRanker`): Controls how many final documents are returned **after** score fusion and re-ranking. This is your final result set size.

### Re-ranking Strategies

Zvec provides different re-ranking strategies to combine scores from multiple vector fields.

| Re-ranker | `WeightedReRanker` | `RrfReRanker` (Reciprocal Rank Fusion) |
| --- | --- | --- |
| Approach | Combines normalized similarity scores using **custom weights** | Fuses results based only on **ranking positions** — no scores needed   The RRF score at rank  *r* is: $\text{RRF}(r) = \frac{1}{k + r + 1}$ |
| Best for | • Scores are reasonably comparable across vector fields   • You know the relative importance of each embedding type | • Scores come from different metrics or scales   • You prefer a simple, robust, tuning-free method |
| Parameters | • `weights`: Dictionary mapping vector names to their relative importance   • `metric`: The similarity metric used for score normalization | `rank_constant` (*k*): Controls how quickly rank influence decreases. Higher values reduce the dominance of top-ranked results. |

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Single Vector](https://zvec.org/en/docs/data-operations/query/single-vector/)

[

Previous Page

](https://zvec.org/en/docs/data-operations/query/single-vector/)[

Conditional Filtering

Next Page

](https://zvec.org/en/docs/data-operations/query/filter/)