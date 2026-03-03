---
title: "Inspect a Collection | Zvec"
source: "https://zvec.org/en/docs/collections/inspect/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Collections](https://zvec.org/en/docs/collections/)

## Inspect a Collection

[Python API Reference](https://zvec.org/api-reference/python/collection/#zvec.model.collection.Collection) [Node.js API Reference](https://zvec.org/api-reference/nodejs/classes/ZVecCollection)

Once you've opened a collection, you can inspect its structure, configuration, and runtime state to better understand how it's organized and performing. This is especially helpful during development, debugging, or system monitoring.

---

## Quick Reference

| Property | Description |
| --- | --- |
| `Collection.schema` | Collection structure and field definitions (e.g., vector dimensions, data types) |
| `Collection.stats` | Runtime metrics such as document count and index completeness |
| `Collection.option` | Runtime settings (e.g., read-only mode, memory mapping) |
| `Collection.path` | Filesystem path to the collection directory |

---

## Collection Schema

To view the [schema](https://zvec.org/en/docs/collections/create/#define-a-collection-schema):

```
print(collection.schema)
```

To view only **scalar fields**:

```
print(collection.schema.fields)
```

To view only **vector fields**:

```
print(collection.schema.vectors)
```

---

## Collection Statistics

The `stats` property provides real-time operational insights:

```
print(collection.stats)
```

---

## Collection Options

Runtime behavior is governed by the options used when opening the collection:

```
print(collection.option)
```

---

## Collection Path

The `path` property returns the on-disk location of the collection:

```
print(collection.path)
```

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)