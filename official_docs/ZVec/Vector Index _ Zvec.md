---
title: "Vector Index | Zvec"
source: "https://zvec.org/en/docs/concepts/vector-index/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Concepts](https://zvec.org/en/docs/concepts/)

## Vector Index

A vector index is a specialized data structure that accelerates similarity search over large collections of vector embeddings.

Without an index, finding the most similar items to a query requires comparing it against **every single vector** in the database — a process known as **brute-force** or **flat search**.

Brute-force search is:

- ✅ **Accurate**: Returns the exact most similar results — no approximation.
- ⚠️ **Painfully slow at scale**: With millions or billions of vectors, queries can take seconds or minutes, making them impractical for real-time applications.

---

## Approximate vs. Exact Search

Most vector indexes use ***Approximate Nearest Neighbor (ANN)*** algorithms.

Instead of finding the exact closest matches, ANN finds *very close approximations* — often indistinguishable in quality for practical purposes — while delivering massive gains in speed and efficiency.

For real-world uses, such as semantic search or recommendations, this small accuracy trade-off delivers huge gains in speed and scalability. In short: ***good enough to be correct, but lightning fast*** ✨.

### Recall: Measuring Approximation Quality

**Recall** is the standard metric for evaluating how well an ANN algorithm preserves result quality.

It quantifies the fraction of **true nearest neighbors** — identified by an exact (brute-force) search — that appear in the top‑k results returned by the approximate method:

$$
\textcolor{#2563eb}{
  \text{Recall@}k = \frac{\text{Number of true nearest neighbors in top-}k}{k}
}
$$

Example:

- If you request the top 10 results and 9 of them match the true top 10 from a brute-force search, your `recall@10` is 90%.
- High recall (e.g., ≥ 96%) typically means the approximation is practically indistinguishable from exact search for most applications.

Different index types (e.g., HNSW) and their parameters (e.g., `ef_search`) let you fine-tune the balance between ***recall, query speed, and resource usage*** — so you can optimize for your specific accuracy and performance requirements.

---

## Vector Index Types

Zvec supports the following vector index types, each suited to different use cases, dataset sizes, and performance requirements:

1. [Flat (Brute-Force) index](https://zvec.org/en/docs/concepts/vector-index/flat-index/)
2. [HNSW (Hierarchical Navigable Small World)](https://zvec.org/en/docs/concepts/vector-index/hnsw-index/)
3. [IVF (Inverted File Index)](https://zvec.org/en/docs/concepts/vector-index/ivf-index/)

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Vector Embedding](https://zvec.org/en/docs/concepts/vector-embedding/)

[

Previous Page

](https://zvec.org/en/docs/concepts/vector-embedding/)[

Flat Index

The Gold Standard for Exact Similarity Search

](https://zvec.org/en/docs/concepts/vector-index/flat-index/)

### On this page

[Approximate vs. Exact Search](https://zvec.org/en/docs/concepts/vector-index/#approximate-vs-exact-search) [Recall: Measuring Approximation Quality](https://zvec.org/en/docs/concepts/vector-index/#recall-measuring-approximation-quality) [Vector Index Types](https://zvec.org/en/docs/concepts/vector-index/#vector-index-types)