---
title: "Destroy a Collection | Zvec"
source: "https://zvec.org/en/docs/collections/destroy/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Collections](https://zvec.org/en/docs/collections/)

## Destroy a Collection

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection.destroy) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection#destroysync)

Destroying a collection **permanently deletes it from disk**. This operation **cannot be undone**.

Destroy a collection

```
import zvec

collection = zvec.open(path="/path/to/my/collection")

# Permanently delete the collection

collection.destroy()
```

After calling `destroy()`, the collection directory and its contents are removed from the filesystem.

Do not use the `collection` object afterward — it is no longer valid.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)