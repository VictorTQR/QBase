---
title: "Filtered Vector Search | Zvec"
source: "https://zvec.org/en/docs/data-operations/query/hybrid/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/) [Query](https://zvec.org/en/docs/data-operations/query/)

## Filtered Vector Search

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.query) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#querysync)

You can combine **vector search** with **scalar filters** to restrict results to a subset of documents — just like adding a `WHERE` clause to a similarity search.

---

## Prerequisites

This guide assumes you:

- Have already opened a `collection` instance.
- Are familiar with [vector querying](https://zvec.org/en/docs/data-operations/query/single-vector/) and [conditional filtering](https://zvec.org/en/docs/data-operations/query/filter/).

---

## Performing Filtered Vector Search

To combine vector similarity search with filters, pass both a `VectorQuery` and a `filter` expression to the `query()` method.

Filtered vector similarity search

```
import zvec

result = collection.query(

    zvec.VectorQuery(  

        field_name="dense_embedding",

        vector=[0.1] * 768,  # Replace with real embedding

    ),

    filter="publish_year > 1936",  # Only consider books published after 1936

    topk=10,

)

print(result)
```

This returns the top-10 most similar documents that satisfy `publish_year > 1936`, sorted by similarity score.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Conditional Filtering](https://zvec.org/en/docs/data-operations/query/filter/)

[

Previous Page

](https://zvec.org/en/docs/data-operations/query/filter/)[

Grouped Query

Next Page

](https://zvec.org/en/docs/data-operations/query/group/)

### On this page

[Prerequisites](https://zvec.org/en/docs/data-operations/query/hybrid/#prerequisites) [Performing Filtered Vector Search](https://zvec.org/en/docs/data-operations/query/hybrid/#performing-filtered-vector-search)