---
title: "Flat Index | Zvec"
source: "https://zvec.org/en/docs/concepts/vector-index/flat-index/"
author:
published:
created: 2026-02-27
description: "The Gold Standard for Exact Similarity Search"
tags:
  - "clippings"
---
[Concepts](https://zvec.org/en/docs/concepts/) [Vector Index](https://zvec.org/en/docs/concepts/vector-index/)

## Flat Index

The Gold Standard for Exact Similarity Search

## How It Works

Performs an exact (brute-force) similarity search by comparing the query vector against every vector in the dataset.

## When to Use a Flat Index

- ✅ Small datasets
- ✅ Prototyping and experimentation
- ✅ Evaluation baselines
- ✅ Scenarios where 100% recall is non-negotiable

**Best Practice**: Start with Flat Index during development and testing — it’s your reliability anchor. Once you validate your approach, consider approximate indexes (like [HNSW](https://zvec.org/en/docs/concepts/vector-index/hnsw-index/)) for production-scale performance. Use the Flat index when working with tiny datasets where correctness outweighs speed.

## Advantages

1. ✨ **Perfect Recall Guarantee** — Finds true nearest neighbors
2. ✨ **Zero Configuration** — Simple setup with no tuning required
3. ✨ **Instant Indexing** — Build time is virtually immediate

## Limitations

⚠️ Search latency grows linearly with dataset size — making it impractical for large-scale workloads.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)

### On this page

[How It Works](https://zvec.org/en/docs/concepts/vector-index/flat-index/#how-it-works) [When to Use a Flat Index](https://zvec.org/en/docs/concepts/vector-index/flat-index/#when-to-use-a-flat-index) [Advantages](https://zvec.org/en/docs/concepts/vector-index/flat-index/#advantages) [Limitations](https://zvec.org/en/docs/concepts/vector-index/flat-index/#limitations)