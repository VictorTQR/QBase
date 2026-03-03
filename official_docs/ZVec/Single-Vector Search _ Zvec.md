---
title: "Single-Vector Search | Zvec"
source: "https://zvec.org/en/docs/data-operations/query/single-vector/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/) [Query](https://zvec.org/en/docs/data-operations/query/)

## Single-Vector Search

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.query) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#querysync)

Single-vector search finds documents most similar to a single query embedding. This is the most common search pattern in vector databases.

---

## Prerequisites

This guide assumes you have opened a collection and have a `collection` object ready.

---

## Performing Single-Vector Search

To perform a single-vector similarity search, use the `query()` method and provide a single [vector query specification](https://zvec.org/en/docs/data-operations/query/#query).

All queries return a `list[Doc]` containing the **top-k** most similar documents, sorted by relevance score.

Each `Doc` object includes:

1. `id`: The document identifier.
2. `score`: The similarity score.
3. `vectors`: A map from vector field names to their corresponding embedding values.  
	This is **only populated** if `include_vector=True` is passed in the query.
4. `fields`: A map from scalar field names to their stored values.  
	By default, **all scalar fields** are returned; this can be restricted using the `output_fields` parameter.

## Parameters

When performing a vector search, the `query()` method accepts two kinds of parameters:

1. **common parameters**, which apply universally regardless of the underlying index type
2. **index-specific parameters**, which allow fine-tuning of search behavior based on the vector index in use

### Common Parameters

| Parameter | Description |
| --- | --- |
| `topk` | The number of most similar documents to return. |
| `include_vector` | If `True`, the returned `Doc` objects include the full vector embeddings (disabled by default for performance). |
| `output_fields` | An optional list of scalar field names to include in results. If omitted, all scalar fields are returned. |
| `filter` | An optional SQL-like boolean expression to restrict results. See [filtered search](https://zvec.org/en/docs/data-operations/query/filter/) for details. |

### Index-Specific Parameters

You can fine-tune search behavior by passing index-specific query parameters through the `param` option in the `Query` object.

The exact type and structure of these `param` depend on the vector index used for the target vector embedding. If omitted, default values are used.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Query](https://zvec.org/en/docs/data-operations/query/)

[

Previous Page

](https://zvec.org/en/docs/data-operations/query/)[

Multiple Vectors

Next Page

](https://zvec.org/en/docs/data-operations/query/multi-vector/)