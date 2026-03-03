---
title: "Retrieve Documents | Zvec"
source: "https://zvec.org/en/docs/data-operations/fetch/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Data Operations](https://zvec.org/en/docs/data-operations/)

## Retrieve Documents

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.fetch) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#fetchsync)

Use `fetch()` to retrieve [documents](https://zvec.org/en/docs/concepts/data-modeling/#documents) by their `id` s.  
This is a **direct lookup** — no search, scoring, or filtering is involved.

Fetch documents

```
# Fetch a single document

result = collection.fetch(ids="book_1")

print(result)   # { "book_1": Doc(...) }

# Fetch multiple documents

result = collection.fetch(ids=["book_1", "book_2", "book_3"])

print(result)   # { "book_1": Doc(...), "book_2": Doc(...), "book_3": Doc(...) }
```

- **Input**: A single document `id` or a list of document `id` s.
- **Output**: A mapping from each **found** `id` to its corresponding document object.
- Missing `id` s are **silently omitted** from the result (no error raised).
- The returned dictionary does not guarantee input order — access documents by `id` instead.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Grouped Query](https://zvec.org/en/docs/data-operations/query/group/)

[

Previous Page

](https://zvec.org/en/docs/data-operations/query/group/)[

Embedding

Next Page

](https://zvec.org/en/docs/embedding/)