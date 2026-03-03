---
title: "Scalar Indexes"
source: "https://docs.lancedb.com/indexing/scalar-index"
author:
  - "[[LanceDB]]"
published:
created: 2026-03-03
description: "Learn how to use scalar indexes in LanceDB for efficient metadata filtering and query optimization."
tags:
  - "clippings"
---
Scalar indexes organize data by scalar attributes (e.g., numbers, categories) and enable fast filtering of vector data. They accelerate retrieval of scalar data associated with vectors, thus enhancing query performance.LanceDB supports three types of scalar indexes:
- `BTREE`: Stores column data in sorted order for binary search. Best for columns with many unique values.
- `BITMAP`: Uses bitmaps to track value presence. Ideal for columns with few unique values (e.g., categories, tags).
- `LABEL_LIST`: Special index for `List<T>` columns supporting `array_contains_all` and `array_contains_any` queries.

## Choosing the Right Index Type

## Scalar Index Operations

### 1\. Build the Index

You can create multiple scalar indexes within a table. By default, the index will be `BTREE`, but you can always configure another type like `BITMAP`

If you are using Cloud or Enterprise, the `create_scalar_index` API returns immediately, but the building of the scalar index is asynchronous. To wait until all data is fully indexed, you can specify the `wait_timeout` parameter on `create_scalar_index()` or call `wait_for_index()` on the table.

### 2\. Check Index Status

### 3\. Update the Index

Updating the table data (adding, deleting, or modifying records) requires that you also update the scalar index. This can be done by calling `optimize`, which will trigger an update to the existing scalar index.

New data added after creating the scalar index will still appear in search results if optimize is not used, but with increased latency due to a flat search on the unindexed portion. LanceDB Cloud automates the optimize process, minimizing the impact on search speed.

The following scan will be faster if the column `book_id` has a scalar index:Scalar indexes can also speed up scans containing a vector search or full text search, and a prefilter:

## Index UUID Columns

LanceDB supports scalar indexes on UUID columns (stored as `FixedSizeBinary(16)`), enabling efficient lookups and filtering on UUID-based primary keys.

**To use `FixedSizeBinary`, ensure you have:**
- Python SDK version `0.22.0` or later
- TypeScript SDK version `0.19.0` or later

### 1\. Define UUID Type

### 2\. Generate UUID Data

### 3\. Create Table with UUID Column

### 4\. Create and Wait for the Index

### 5\. Perform Operations with the UUID Index

[FTS index](https://docs.lancedb.com/indexing/fts-index) [GPU indexing](https://docs.lancedb.com/indexing/gpu-indexing)