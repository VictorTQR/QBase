---
title: "Optimize a Collection | Zvec"
source: "https://zvec.org/en/docs/collections/optimize/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Collections](https://zvec.org/en/docs/collections/)

## Optimize a Collection

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.optimize) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#optimizesync)

The `optimize()` method **improves search performance** by building the configured vector index from vectors accumulated in a temporary flat buffer. It runs **in the background** and **does not block reads or writes**, ensuring your application remains fully responsive.

---

## Why Optimization is Needed

In Zvec, newly inserted vectors are **not added directly** to the configured vector index.

Instead, they are first appended to a lightweight [flat (brute-force) index](https://zvec.org/en/docs/concepts/vector-index/flat-index/) buffer.

This design choice offers important benefits — but also a trade-off:

- ✅ **Strengths**
	- **Maximum write throughput**: Enables high-speed data ingestion.
	- **Streaming inserts**: Supports real-time insertion for index types like [IVF](https://zvec.org/en/docs/concepts/vector-index/ivf-index/) that don't natively allow incremental updates.
- ⚠️ **Trade-off**
	- **Slower searches over time**: As the flat buffer grows, search performance degrades.

🔁 **Solution**

Call `optimize()` periodically. This triggers a background process that merges the buffered vectors into the configured vector index — **without interrupting ongoing reads or writes**. 🚀

`optimize()` is a synchronous method (it returns only after the optimization has finished), but it **does not lock the collection**.  
Other threads can continue reading, writing, and querying without delay — your application stays fully responsive.

---

## Usage Example

Optimize a collection

```
import zvec

collection = zvec.open(path="/path/to/my/collection")

# Insert some documents

for i in range(1000):

    doc = zvec.Doc(id=f"doc_{i}", vectors={"embedding": [i + 0.1, i + 0.2, i + 0.3]})

    collection.insert(doc)

# Optimize the collection

collection.optimize()
```

---

## Check Indexing Status

Use the `stats` property to get real-time insights into your collection's indexing state:

```
print(collection.stats)
```

---

## When to Call optimize()

Optimize **regularly — but not too often**:

- **Too infrequent** → Flat buffers grow large, degrading search performance
- **Too frequent** → Wastes resources optimizing small batches prematurely

Find a balance based on your **data ingestion rate** and **query latency requirements**.

**Best practice:**  
Check your collection's indexing status if searches feel slow.  
As a general guideline, consider optimizing when you have **100,000+ unindexed documents** — but adjust based on your specific use case.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Destroy](https://zvec.org/en/docs/collections/destroy/)

[

Previous Page

](https://zvec.org/en/docs/collections/destroy/)[

Schema Evolution

Next Page

](https://zvec.org/en/docs/collections/schema-evolution/)

### On this page

[Why Optimization is Needed](https://zvec.org/en/docs/collections/optimize/#why-optimization-is-needed) [Usage Example](https://zvec.org/en/docs/collections/optimize/#usage-example) [Check Indexing Status](https://zvec.org/en/docs/collections/optimize/#check-indexing-status) [When to Call `optimize()`](https://zvec.org/en/docs/collections/optimize/#when-to-call-optimize)