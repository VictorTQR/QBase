---
title: "Open an Existing Collection | Zvec"
source: "https://zvec.org/en/docs/collections/open/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Collections](https://zvec.org/en/docs/collections/)

## Open an Existing Collection

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.open) [Node.js API Reference](https://zvec.org/api-reference/nodejs/functions/ZVecOpen)

To open an existing collection, use the `open()` function to load it from disk.

## Usage

Open a collection

```
import zvec

existing_collection = zvec.open(  

    path="/path/to/my/collection",

    option=zvec.CollectionOption(read_only=False, enable_mmap=True),

)
```

## Parameters

- `path`:  
	The filesystem path to the collection directory.
- `option`:  
	Runtime settings that control how the collection is accessed.
	- `read_only`:  
		Opens the collection in read-only mode. Attempts to write will raise an error.
	- `enable_mmap`:  
		Uses memory-mapped I/O for faster access (defaults to `True`). This trades slightly higher memory cache usage for improved performance.

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)