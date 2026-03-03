---
title: "Data Modeling | Zvec"
source: "https://zvec.org/en/docs/concepts/data-modeling/"
author:
published:
created: 2026-02-27
description:
tags:
  - "clippings"
---
[Concepts](https://zvec.org/en/docs/concepts/)

## Data Modeling

In Zvec, data is organized into **collections** and **documents**.

---

## Collections

A **collection** is a named container for [documents](https://zvec.org/en/docs/concepts/data-modeling/#documents) — similar to a **table** in a relational database system such as MySQL, where each **document** represents a **row** in a table. A collection is where you store, organize, and query your data.

Every collection is governed by a **schema** that defines the scalar fields and vectors it contains, along with their [types](https://zvec.org/en/docs/concepts/data-modeling/#data-types) and [indexing settings](https://zvec.org/en/docs/concepts/data-modeling/#indexes).

![Collection example](https://zvec.org/_next/static/media/collection-example.73d5431e.svg)

Collection example

**All documents within a collection conform to the same schema**.

### Why Use Collections?

Collections provide **isolation** by ensuring that each data workload operates within its own dedicated schema and indexing configuration. This separation prevents interference between unrelated use cases and allows each to evolve independently.

For example:

- A **Retrieval-Augmented Generation (RAG) collection** might store text embeddings together with metadata — such as title, section, source URL, and last-updated timestamp.
- An **image search collection** could hold high-dimensional image embeddings along with associated fields like image ID, file path, or caption.

### Persistence

- **Each collection is persisted independently on disk in its own dedicated directory**, providing isolation between different data workloads.
- Each collection is **self-contained within its directory**. This means you can relocate a collection's directory and Zvec will still be able to open it when provided with the correct path.

---

## Documents

A document is the fundamental unit of data storage — think of it as a single record or row in a relational database table. Each document lives inside a [collection](https://zvec.org/en/docs/concepts/data-modeling/#collections) and must conform to that collection's schema.

### Structure of a Document

A document is a **structured** object composed of three core components.

- 🔑 `id`: A unique string identifier for the document, cannot be changed after insertion
- 📐 `vectors`: A named set of vectors
- 🗂️ `fields`: A named set of scalar (non-vector) fields, which can include strings, numbers, booleans, or arrays of these types

### Example Document

**All fields must conform to their declared types in the schema**. Vectors must exactly match the specified type (dense or sparse) and dimensionality (e.g., a 768-dimensional dense vector cannot accept a 512-dimensional vector).

---

## Data Types

Zvec uses a strongly typed schema system based on the `DataType` enumeration. The supported types fall into two categories:

1. **Scalar types** — strings, integers, floats, booleans, and arrays of these types
2. **Vector types** — dense or sparse numeric representations for vector embeddings

### Scalar Types

- Elementary Types
	| `STRING` | `BOOL` | `INT32` | `INT64` | `UINT32` | `UINT64` | `FLOAT` | `DOUBLE` |
	| --- | --- | --- | --- | --- | --- | --- | --- |
- Array Types
	| `ARRAY_STRING` | `ARRAY_BOOL` | `ARRAY_INT32` | `ARRAY_INT64` | `ARRAY_UINT32` | `ARRAY_UINT64` | `ARRAY_FLOAT` | `ARRAY_DOUBLE` |
	| --- | --- | --- | --- | --- | --- | --- | --- |

### Vector Types

- [Dense Vector](https://zvec.org/en/docs/concepts/vector-embedding/#dense-vectors) Types:  
	represented as fixed-length numeric arrays, e.g., `[0.1, -0.5, ..., 0.9]`
	| `VECTOR_FP16` | `VECTOR_FP32` | `VECTOR_INT8` |
	| --- | --- | --- |
- [Sparse Vector](https://zvec.org/en/docs/concepts/vector-embedding/#sparse-vectors) Types:  
	represented as maps from integer indices to float values, e.g., `{ 42: 0.85, 1024: 0.13 }`
	| `SPARSE_VECTOR_FP32` | `SPARSE_VECTOR_FP16` |
	| --- | --- |

---

## Indexes

Indexes accelerate data retrieval beyond basic storage of scalar fields and vectors. In Zvec:

- **Every vector field must be indexed** using an appropriate [vector index](https://zvec.org/en/docs/concepts/vector-index/) to enable similarity search.
- **Scalar fields are optionally indexed** — but you should build [inverted indexes](https://zvec.org/en/docs/concepts/inverted-index/) on any scalar field you plan to use in filtering queries (e.g., `WHERE category = 'music'`).

You can define indexes at [collection creation](https://zvec.org/en/docs/collections/create/) by specifying `index_param` in the schema for each field or vector.  
Alternatively, you can add indexes after collection creation by calling [`create_index()`](https://zvec.org/en/docs/collections/schema-evolution/#create-an-index) dynamically — no data re-ingestion required.

Create a collection

```
import zvec

# Define the collection schema with one scalar field and one vector field, both

# configured with indexes via "index_param".

schema = zvec.CollectionSchema(   

    name="my_collection",

    fields=[

        zvec.FieldSchema(

            name="price",

            data_type=zvec.DataType.INT32,

            index_param=zvec.InvertIndexParam(enable_range_optimization=True),

        ),

    ],

    vectors=[

        zvec.VectorSchema(

            name="vector",

            data_type=zvec.DataType.VECTOR_FP32,

            dimension=256,

            index_param=zvec.HnswIndexParam(metric_type=zvec.MetricType.COSINE),

        ),

    ],

)

collection = zvec.create_and_open(path="/path/to/my/collection", schema=schema)
```

[🐛 Report an Issue](https://github.com/alibaba/zvec/issues)[Concepts](https://zvec.org/en/docs/concepts/)

[

Previous Page

](https://zvec.org/en/docs/concepts/)[

Vector Embedding

Next Page

](https://zvec.org/en/docs/concepts/vector-embedding/)